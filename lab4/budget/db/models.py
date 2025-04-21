from enum import StrEnum

from bson import ObjectId
from pydantic import BaseModel, PositiveInt, Field


class Currency(StrEnum):
    USD = "USD"
    RUB = "RUB"


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


class MongoModel(BaseModel):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class IncomeInDB(MongoModel, IncomeData):
    user_id: int


class ExpenseInDB(MongoModel, ExpenseData):
    user_id: int
