from pymongo import MongoClient, ASCENDING
from config import settings

client = MongoClient(settings.mongo_url)
db = client[settings.mongo_db]

income_collection = db.incomes
expense_collection = db.expenses


def create_indexes():
    income_collection.create_index([("user_id", ASCENDING)])
    expense_collection.create_index([("user_id", ASCENDING)])
