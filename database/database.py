from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from core.config import DATABASE_URL

assert DATABASE_URL, "No database URL provided"

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def _get_session():
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


# Session for non requests
session = Session(engine)

SessionDep = Annotated[Session, Depends(_get_session)]
