from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# All tables live under the dbo schema (Principle VII)
metadata = MetaData(schema="dbo")


class Base(DeclarativeBase):
    metadata = metadata
