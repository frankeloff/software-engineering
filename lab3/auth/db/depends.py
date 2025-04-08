from typing import Any, Generator
from sqlalchemy.orm.session import Session
from . import get_session

def get_con() -> Generator[Session, Any, None]:
    con = get_session()
    try:
        yield con
    finally:
        con.close()
