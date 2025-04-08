from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

from enum import StrEnum


class Currency(StrEnum):
    USD = "USD"
    RUB = "RUB"


engine = create_engine(settings.postgres_dsn)
get_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from .user import UserModel
from .expense import ExpenseModel
from .income import IncomeModel

__all__ = ("UserModel", "ExpenseModel", "IncomeModel")
