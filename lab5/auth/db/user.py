from sqlalchemy import Column, Integer, String, Text, Boolean
from . import Base


class UserModel(Base):
    __tablename__ = "budget_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    is_admin = Column(Boolean)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'password': self.password
        }
