from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import desc, select

from database.database import create_db_and_tables, session
from exceptions.exceptions import BadRequestError, ProfileNotFoundError
from models.models import ProfilesDatabase
from models.schemas import (
    ACCEPTED_SORT_BY,
    FilterParams,
    OrderBy,
    PaginatedProfiles,
)
from seed_profiles import seed
from utils.helpers import format_profiles, is_seeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    if is_seeded():
        pass
    else:
        seed()
    yield


app = FastAPI(title="Intelligence Query Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError) -> JSONResponse:
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
    filter_params: Annotated[FilterParams, Query()],
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
    if filter_params.order and not filter_params.sort_by:
        raise BadRequestError()

    if filter_params.sort_by and filter_params.order == OrderBy.descending:
        query = query.order_by(desc(ACCEPTED_SORT_BY[filter_params.sort_by]))
    elif filter_params.sort_by or (
        filter_params.sort_by and filter_params.order == OrderBy.ascending
    ):
        query = query.order_by(ACCEPTED_SORT_BY[filter_params.sort_by])

    offset = filter_params.page * filter_params.limit

    query = query.offset(offset).limit(filter_params.limit)
    profiles = session.exec(query).all()

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
