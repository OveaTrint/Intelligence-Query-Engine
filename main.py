from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import desc, select

from database.database import SessionDep, create_db_and_tables
from exceptions.exceptions import BadRequestError, ProfileNotFoundError
from models.models import ProfilesDatabase
from models.schemas import (
    ACCEPTED_SORT_BY,
    OrderBy,
    PaginatedProfiles,
    ProfilesParams,
)
from query_parser import parse_query
from utils.helpers import format_profiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Intelligence Query Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError) -> JSONResponse:
    if exc.message:
        return JSONResponse(
            content={"status": "error", "message": exc.message},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return JSONResponse(
        content={"status": "error", "message": "Missing or empty parameter"},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.exception_handler(ProfileNotFoundError)
async def profile_not_found_handler(
    request: Request, exc: BadRequestError
) -> JSONResponse:
    return JSONResponse(
        content={"status": "error", "message": "Profile not found"},
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    for error in errors:
        if error.get("type") == "extra_forbidden":
            return JSONResponse(
                content={"status": "error", "message": "Invalid query parameters"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    return JSONResponse(
        content={"status": "error", "message": "Invalid parameter type"},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        content={"status": "error", "message": "Server failure"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def paginated_response(
    session: SessionDep, filter_params: Annotated[ProfilesParams, Query()]
) -> PaginatedProfiles:
    query = select(ProfilesDatabase)

    if filter_params.gender:
        query = query.where(ProfilesDatabase.gender == filter_params.gender.lower())
    if filter_params.age_group:
        query = query.where(
            ProfilesDatabase.age_group == filter_params.age_group.lower()
        )
    if filter_params.country_id:
        query = query.where(
            ProfilesDatabase.country_id == filter_params.country_id.upper()
        )
    if filter_params.min_age:
        query = query.where(ProfilesDatabase.age > filter_params.min_age)
    if filter_params.max_age:
        query = query.where(ProfilesDatabase.age < filter_params.max_age)
    if filter_params.min_gender_probability:
        query = query.where(
            ProfilesDatabase.gender_probability > filter_params.min_gender_probability
        )
    if filter_params.max_country_probability:
        query = query.where(
            ProfilesDatabase.country_probability < filter_params.max_country_probability
        )

    # order must be paired with sort_by
    # if filter_params.order and not filter_params.sort_by:
    # raise BadRequestError()

    if filter_params.sort_by:
        if filter_params.order == OrderBy.descending:
            query = query.order_by(desc(ACCEPTED_SORT_BY[filter_params.sort_by]))
        else:
            query = query.order_by(ACCEPTED_SORT_BY[filter_params.sort_by])
    elif filter_params.order == OrderBy.descending:
        query = query.order_by(desc(ProfilesDatabase.id))
    elif filter_params.order == OrderBy.ascending:
        query = query.order_by(ProfilesDatabase.id)

    # compute offset for profiles to be displayed
    offset = filter_params.page * filter_params.limit
    query = query.offset(offset).limit(filter_params.limit)

    print(str(query))

    # executes query
    profiles = session.exec(query).all()

    # formats the list of profiles to appropriate format
    formatted_profiles = format_profiles(profiles)

    return PaginatedProfiles(
        page=filter_params.page, limit=filter_params.limit, data=formatted_profiles
    )


@app.get("/api/profiles")
async def get_profiles(
    profiles: Annotated[PaginatedProfiles, Depends(paginated_response)],
) -> PaginatedProfiles:
    if not profiles.data:
        raise ProfileNotFoundError()

    return profiles


@app.get("/api/profiles/search")
async def search_profiles(
    session: SessionDep, q: str, page: int = Query(1), limit: int = Query(10, le=50)
):
    parsed_query = parse_query(q)

    if not parsed_query:
        raise BadRequestError(message="Unable to interpret query")

    gender = parsed_query.get("gender")
    min_age = parsed_query.get("min_age")
    max_age = parsed_query.get("max_age")
    age_group = parsed_query.get("age_group")
    country_id = parsed_query.get("country_id")

    query = select(ProfilesDatabase)

    if gender:
        query = query.where(ProfilesDatabase.gender == gender.lower())
    if age_group:
        query = query.where(ProfilesDatabase.age_group == age_group.lower())
    if country_id:
        query = query.where(ProfilesDatabase.country_id == country_id.upper())
    if min_age:
        query = query.where(ProfilesDatabase.age > min_age)
    if max_age:
        query = query.where(ProfilesDatabase.age < max_age)

    offset = page * limit
    query = query.offset(offset).limit(limit)

    profiles = session.exec(query)
    if not profiles:
        raise ProfileNotFoundError()

    formatted_profiles = format_profiles(profiles)

    return PaginatedProfiles(page=page, limit=limit, data=formatted_profiles)


@app.get("/")
async def running():
    return JSONResponse(content={"status": "I'm alive :)"})
