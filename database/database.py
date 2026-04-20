from sqlmodel import Session, SQLModel, create_engine

from core.config import DATABASE_URL

assert DATABASE_URL, "No database URL provided"

engine = create_engine(DATABASE_URL, echo=True)

session = Session(engine)
SQLModel.metadata.create_all(engine)
