import os
from contextlib import contextmanager
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = os.getenv("DATABASE_URL", "postgresql://basa_user:basa_pass@localhost:5432/basa_db")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


@contextmanager
def get_session():
    with Session(get_engine()) as session:
        yield session
