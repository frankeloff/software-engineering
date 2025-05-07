from .mongo import income_collection, expense_collection, create_indexes
from .models import IncomeInDB, ExpenseInDB, Currency


def seed_data():
    create_indexes()

    if income_collection.count_documents({}) == 0:
        income_collection.insert_many(
            [
                IncomeInDB(
                    _id="1", user_id=1, amount=1000, currency=Currency.USD
                ).model_dump(by_alias=True),
                IncomeInDB(
                    _id="2", user_id=2, amount=1500, currency=Currency.RUB
                ).model_dump(by_alias=True),
                IncomeInDB(
                    _id="3", user_id=3, amount=2000, currency=Currency.USD
                ).model_dump(by_alias=True),
                IncomeInDB(
                    _id="4", user_id=4, amount=2500, currency=Currency.RUB
                ).model_dump(by_alias=True),
            ]
        )

    if expense_collection.count_documents({}) == 0:
        expense_collection.insert_many(
            [
                ExpenseInDB(
                    _id="1", user_id=1, amount=500, currency=Currency.USD
                ).model_dump(by_alias=True),
                ExpenseInDB(
                    _id="2", user_id=2, amount=700, currency=Currency.RUB
                ).model_dump(by_alias=True),
                ExpenseInDB(
                    _id="3", user_id=3, amount=900, currency=Currency.USD
                ).model_dump(by_alias=True),
                ExpenseInDB(
                    _id="4", user_id=4, amount=1200, currency=Currency.RUB
                ).model_dump(by_alias=True),
            ]
        )
