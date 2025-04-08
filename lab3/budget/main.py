from enum import StrEnum
from typing import Annotated

import redis.asyncio as redis
from pydantic import BaseModel, PositiveInt
from dishka import FromComponent
from fastapi import FastAPI, Header, HTTPException, status, Depends
from dishka.integrations.fastapi import inject, setup_dishka
from sqlalchemy.orm import Session

from db import Currency
from db.income import IncomeModel
from db.expense import ExpenseModel
from db.depends import get_con

import ioc


class TokenType(StrEnum):
    BEARER = "Bearer"


class CommonHeaders(BaseModel):
    authorization: str


class SessionUser(BaseModel):
    username: str
    is_admin: bool = False
    user_id: int


class BudgetData(BaseModel):
    amount: PositiveInt
    currency: Currency


class IncomeData(BudgetData):
    pass


class ExpenseData(BudgetData):
    pass


type Username = str


app = FastAPI()
setup_dishka(ioc.container, app)


@app.post("/income")
@inject
async def add_income(
    headers: Annotated[CommonHeaders, Header()],
    income: IncomeData,
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
con: Annotated[Session, Depends(get_con)],
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

    income = IncomeModel(
        user_id=user_info.user_id, amount=income.amount, currency=income.currency
    )

    con.add(income)
    con.commit()
    con.refresh(income)

    return income

@app.get("/income")
@inject
async def get_income(
    headers: Annotated[CommonHeaders, Header()],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
con: Annotated[Session, Depends(get_con)],
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

    user_income = con.query(IncomeModel).filter(IncomeModel.user_id == user_info.user_id).all()

    return user_income


@app.post("/expenses")
@inject
async def add_expense(
    headers: Annotated[CommonHeaders, Header()],
    expense: ExpenseData,
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
con: Annotated[Session, Depends(get_con)],
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

    expense = ExpenseModel(
        user_id=user_info.user_id, amount=expense.amount, currency=expense.currency
    )

    con.add(expense)
    con.commit()
    con.refresh(expense)

    return expense


@app.get("/expenses")
@inject
async def get_expenses(
    headers: Annotated[CommonHeaders, Header()],
    redis_con: Annotated[redis.Redis, FromComponent("RedisProvider")],
con: Annotated[Session, Depends(get_con)],
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

    user_expense = con.query(ExpenseModel).filter(ExpenseModel.user_id == user_info.user_id).all()

    return user_expense
