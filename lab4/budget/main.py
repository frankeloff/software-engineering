from typing import Annotated
from uuid import uuid4

import redis.asyncio as redis
from dishka import FromComponent
from fastapi import FastAPI, Header, HTTPException, status
from dishka.integrations.fastapi import inject, setup_dishka

from db.mongo import income_collection, expense_collection, create_indexes
from db.models import (
    CommonHeaders,
    IncomeData,
    SessionUser,
    IncomeInDB,
    ExpenseData,
    ExpenseInDB,
)
from db.seed import seed_data
import ioc


type Username = str


app = FastAPI()
setup_dishka(ioc.container, app)


@app.on_event("startup")
def startup_event():
    create_indexes()
    seed_data()


@app.post("/income")
@inject
async def add_income(
    headers: Annotated[CommonHeaders, Header()],
    income: IncomeData,
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> IncomeData:
    """
    Ручка для добавления дохода
    """
    try:
        _, token = headers.authorization.split(maxsplit=1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    session = await redis_con.get(token)

    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_info = SessionUser.model_validate_json(session)

    income = IncomeInDB(
        _id=str(uuid4()), user_id=user_info.user_id, **income.model_dump()
    )
    result = income_collection.insert_one(income.model_dump(by_alias=True))
    income.id = str(result.inserted_id)
    return income


@app.get("/income")
@inject
async def get_income(
    headers: Annotated[CommonHeaders, Header()],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> list[IncomeData]:
    """
    Ручка для получения доходов
    """
    try:
        _, token = headers.authorization.split(maxsplit=1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    session = await redis_con.get(token)

    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_info = SessionUser.model_validate_json(session)

    results = income_collection.find({"user_id": user_info.user_id})

    return [IncomeData(**doc) for doc in results]


@app.post("/expenses")
@inject
async def add_expense(
    headers: Annotated[CommonHeaders, Header()],
    expense: ExpenseData,
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> ExpenseData:
    """
    Ручка для добавления расхода
    """
    try:
        _, token = headers.authorization.split(maxsplit=1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    session = await redis_con.get(token)

    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_info = SessionUser.model_validate_json(session)

    expense_doc = ExpenseInDB(
        _id=str(uuid4()), user_id=user_info.user_id, **expense.model_dump()
    )
    result = expense_collection.insert_one(expense_doc.model_dump(by_alias=True))
    expense_doc.id = str(result.inserted_id)
    return expense_doc


@app.get("/expenses")
@inject
async def get_expenses(
    headers: Annotated[CommonHeaders, Header()],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> list[ExpenseData]:
    """
    Ручка для получения расходов
    """
    try:
        _, token = headers.authorization.split(maxsplit=1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    session = await redis_con.get(token)

    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_info = SessionUser.model_validate_json(session)

    results = expense_collection.find({"user_id": user_info.user_id})
    return [ExpenseData(**doc) for doc in results]
