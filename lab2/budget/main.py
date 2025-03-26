from enum import StrEnum
from typing import Annotated

import aiohttp
import redis.asyncio as redis
from pydantic import BaseModel, PositiveInt
from dishka import FromComponent
from fastapi import FastAPI, Header, HTTPException, status
from dishka.integrations.fastapi import inject, setup_dishka

import ioc


class TokenType(StrEnum):
    BEARER = "Bearer"


class Currency(StrEnum):
    USD = "USD"
    RUB = "RUB"


class CommonHeaders(BaseModel):
    authorization: str


class User(BaseModel):
    username: str
    is_admin: bool = False


class BudgetData(BaseModel):
    amount: PositiveInt
    currency: Currency


class IncomeData(BudgetData):
    pass


class ExpenseData(BudgetData):
    pass


type Username = str

fake_income_data: dict[Username, list[IncomeData]] = {}
fake_expense_data: dict[Username, list[ExpenseData]] = {}


def add_income_in_db(username: str, income: IncomeData) -> None:
    if fake_income_data.get(username):
        fake_income_data[username].append(income)
    else:
        fake_income_data[username] = [income]


def get_income_from_db(username: str) -> list[IncomeData]:
    if fake_income_data.get(username):
        return fake_income_data[username]
    else:
        return []


def add_expense_in_db(username: str, expense: ExpenseData):
    if fake_expense_data.get(username):
        fake_expense_data[username].append(expense)
    else:
        fake_expense_data[username] = [expense]


def get_expenses_from_db(username: str) -> list[ExpenseData]:
    if fake_expense_data.get(username):
        return fake_expense_data[username]
    else:
        return []


app = FastAPI()
setup_dishka(ioc.container, app)


@app.post("/income")
@inject
async def add_income(
    headers: Annotated[CommonHeaders, Header()],
    income: IncomeData,
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> None:
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

    user_info = User.model_validate_json(session)

    add_income_in_db(user_info.username, income)


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

    user_info = User.model_validate_json(session)

    return get_income_from_db(user_info.username)


@app.post("/expenses")
@inject
async def add_expense(
    headers: Annotated[CommonHeaders, Header()],
    expense: ExpenseData,
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
) -> None:
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

    user_info = User.model_validate_json(session)

    add_expense_in_db(user_info.username, expense)


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

    user_info = User.model_validate_json(session)

    return get_expenses_from_db(user_info.username)
