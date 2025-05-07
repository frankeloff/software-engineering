import json
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from dishka import FromComponent
from dishka.integrations.fastapi import inject, setup_dishka
from sqlalchemy.orm import Session
from db.user import UserModel

import ioc
from db.depends import get_con

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
USER_CACHE_EXPIRE_SECONDS = 3600  # 1 час

type SessionID = str
type Username = str

fake_sessions_db: dict[Username, list[SessionID]] = {}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class User(BaseModel):
    username: str
    is_admin: bool = False


class UserDBModel(User):
    id: int
    password: str


class SessionUser(User):
    user_id: int


class CreateUser(User):
    password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user_from_cache(
    redis_con: redis.Redis, username: str
) -> UserDBModel | None:
    cached_user = await redis_con.get(f"user:{username}")
    if cached_user:
        return UserDBModel.model_validate_json(cached_user)

    return None


async def set_user_to_cache(redis_con: redis.Redis, user: UserModel):
    await redis_con.set(
        f"user:{user.username}",
        json.dumps(user.to_dict()),
        ex=USER_CACHE_EXPIRE_SECONDS,
    )


async def remove_user_from_cache(redis_con: redis.Redis, username: str):
    await redis_con.delete(f"user:{username}")


async def authenticate_user(
    username: str, password: str, con: Session, redis_con: redis.Redis
):
    cached_user = await get_user_from_cache(redis_con, username)
    if cached_user:
        if verify_password(password, cached_user.password):
            return cached_user
        return None
    user = con.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


app = FastAPI()
setup_dishka(ioc.container, app)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    con: Annotated[Session, Depends(get_con)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    async with ioc.container() as c:
        redis_con: redis.Redis = await c.get(redis.Redis, "RedisProvider")
        cached_user = await get_user_from_cache(redis_con, token_data.username)
        if cached_user:
            return User(
                username=str(cached_user.username), is_admin=bool(cached_user.is_admin)
            )
    user = (
        con.query(UserModel).filter(UserModel.username == token_data.username).first()
    )
    if user is None:
        raise credentials_exception

    await set_user_to_cache(redis_con, user)
    return User(username=str(user.username), is_admin=bool(user.is_admin))


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@app.post("/token")
@inject
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
    con: Annotated[Session, Depends(get_con)],
) -> Token:
    """
    Ручка для получения токена
    """
    user = await authenticate_user(
        form_data.username, form_data.password, con, redis_con
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    await redis_con.set(
        access_token,
        SessionUser(
            username=str(user.username),
            is_admin=bool(user.is_admin),
            user_id=int(user.id),
        ).model_dump_json(),
        ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Ручка для получения текущего пользователя
    """
    return current_user


@app.post("/users")
@inject
async def create_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user: CreateUser,
    con: Annotated[Session, Depends(get_con)],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> User:
    """
    Ручка для создания пользователя

    Пользователей может создавать только админ
    """
    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db_user = con.query(UserModel).filter(UserModel.username == user.username).first()

    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже существует",
        )

    new_user = UserModel(
        username=user.username,
        password=get_password_hash(user.password),
        is_admin=user.is_admin,
    )

    con.add(new_user)
    con.commit()
    con.refresh(new_user)

    await set_user_to_cache(redis_con, new_user)

    return new_user


@app.get("/users")
@inject
async def get_users(
    current_user: Annotated[User, Depends(get_current_active_user)],
    con: Annotated[Session, Depends(get_con)],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> list[User]:
    """
    Ручка для получения всех пользователей

    Всех польхователей может получать только админ
    """
    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    cache = await redis_con.get("users:all")
    if cache:
        cached_users = json.loads(cache)
        return [User.model_validate(user) for user in cached_users]

    db_users = con.query(UserModel).all()

    for user in db_users:
        await set_user_to_cache(redis_con, user)

    users = [
        User(username=str(user.username), is_admin=bool(user.is_admin))
        for user in db_users
    ]

    await redis_con.set(
        "users:all",
        json.dumps([user.model_dump() for user in users]),
        ex=USER_CACHE_EXPIRE_SECONDS,
    )

    return users


@app.delete("/users/{username:str}")
@inject
async def remove_user(
    username: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    con: Annotated[Session, Depends(get_con)],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> User:
    """
    Ручка для удаления пользователя

    Пользователей может удалять только админ
    """
    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if current_user.username == username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя"
        )

    db_user = con.query(UserModel).filter(UserModel.username == username).first()

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    con.delete(db_user)
    con.commit()

    await remove_user_from_cache(redis_con, username)

    return User(username=str(db_user.username), is_admin=bool(db_user.is_admin))
