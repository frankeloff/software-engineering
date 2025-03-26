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

import ioc

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$/C4L49LqflBZOt0sZb9nxur0kEoJFVQN/NnfSuEQIAWB6Goza9Ff2",
        "is_admin": True,
    }
}

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


class UserInDB(User):
    hashed_password: str


class CreateUser(User):
    password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str) -> UserInDB | None:
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def get_users_from_db(db) -> list[User]:
    return [User(**user_dict) for user_dict in db.values()]


def add_user_to_db(db: dict[str, dict[str, str | bool]], user: UserInDB) -> None:
    db[user.username] = user.model_dump()


def remove_user_from_db(db: dict[str, dict[str, str | bool]], username: str) -> None:
    db.pop(username)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
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


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
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
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


app = FastAPI()
setup_dishka(ioc.container, app)


@app.post("/token")
@inject
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> Token:
    """
    Ручка для получения токена
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
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
        User(**user.model_dump()).model_dump_json(),
        ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    if fake_sessions_db.get(user.username) is None:
        fake_sessions_db[user.username] = [access_token]
    else:
        fake_sessions_db[user.username].append(access_token)

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
async def create_user(
    current_user: Annotated[User, Depends(get_current_active_user)], user: CreateUser
) -> User:
    """
    Ручка для создания пользователя

    Пользователей может создавать только админ
    """
    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if get_user(fake_users_db, user.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже существует",
        )

    add_user_to_db(
        fake_users_db,
        UserInDB(
            username=user.username,
            is_admin=user.is_admin,
            hashed_password=get_password_hash(user.password),
        ),
    )

    return User(**user.model_dump())


@app.get("/users")
async def get_users(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[User]:
    """
    Ручка для получения всех пользователей

    Всех польхователей может получать только админ
    """
    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return get_users_from_db(fake_users_db)


@app.delete("/users/{username:str}")
@inject
async def remove_user(
    username: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
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

    user = get_user(fake_users_db, username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    remove_user_from_db(fake_users_db, user.username)

    if fake_sessions_db.get(user.username):
        for session in fake_sessions_db[user.username]:
            await redis_con.delete(session)

    return User(**user.model_dump())
