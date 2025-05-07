from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine = create_engine(settings.postgres_dsn)
get_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
