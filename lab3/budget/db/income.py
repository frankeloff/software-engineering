from sqlalchemy import Column, Integer, ForeignKey, Enum
from . import Base, Currency


class IncomeModel(Base):
    __tablename__ = "budget_income"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("budget_users.id", ondelete="CASCADE"))
    amount = Column(Integer, nullable=False)
    currency = Column(Enum(Currency))
