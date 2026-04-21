from contextlib import asynccontextmanager
from enum import Enum
from typing import Annotated, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Depends
from sqlmodel import desc, select

from database.database import SessionDep, create_db_and_tables, session
from models.models import Profiles
from seed_profiles import seed


def is_seeded() -> bool:
    DB_TEST_ROWS = 5
    result = session.exec(select(Profiles)).fetchmany(DB_TEST_ROWS)

    if result:
        return True
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    if is_seeded():
        pass
    else:
        seed()
    yield


class ProfilesSort(str, Enum):
    age = "age"
    created_at = "created_at"
    gender_probability = "gender_probability"


ACCEPTED_SORT_BY = {
    ProfilesSort.age: Profiles.age,
    ProfilesSort.created_at: Profiles.created_at,
    ProfilesSort.gender_probability: Profiles.gender_probability,
}


class OrderBy(str, Enum):
    ascending = "asc"
    descending = "desc"


app = FastAPI(title="Intelligence Query Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


@app.get("/api/profiles")
async def get_profile(
    session: SessionDep,
    gender: Optional[str] = None,
    age_group: Optional[str] = None,
    country_id: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    max_country_probability: Optional[float] = None,
    sort_by: ProfilesSort = Query(None),
    order: OrderBy = Query(None),
):
    query = select(Profiles)

    if gender:
        query = query.where(Profiles.gender == gender.lower())
    if age_group:
        query = query.where(Profiles.age_group == age_group.lower())
    if country_id:
        query = query.where(Profiles.country_id == country_id.upper())
    if min_age:
        query = query.where(Profiles.age > min_age)
    if max_age:
        query = query.where(Profiles.age < max_age)
    if min_gender_probability:
        query = query.where(Profiles.gender_probability > min_gender_probability)
    if max_country_probability:
        query = query.where(Profiles.country_probability < max_country_probability)

    if order and not sort_by:
        raise Exception

    if sort_by and order == OrderBy.descending:
        query = query.order_by(desc(ACCEPTED_SORT_BY[sort_by]))
    elif sort_by or (sort_by and order == OrderBy.ascending):
        query = query.order_by(ACCEPTED_SORT_BY[sort_by])

    profiles = session.exec(query).all()

    return profiles
