from enum import Enum
from typing import Optional, Sequence

from sqlmodel import Field, SQLModel

from .models import ProfilesDatabase, ProfilesResponse


class PaginatedProfiles(SQLModel):
    """Schema for the paginated JSON response"""

    status: str = Field(default="success")
    page: int
    limit: int
    total: int = Field(default=2026)
    data: Sequence[ProfilesResponse]


class OrderBy(str, Enum):
    ascending = "asc"
    descending = "desc"


class Gender(str, Enum):
    male = "male"
    female = "female"


class AgeGroup(str, Enum):
    child = "child"
    teenager = "teenager"
    adult = "adult"
    senior = "senior"


class SortByProfiles(str, Enum):
    age = "age"
    created_at = "created_at"
    gender_probability = "gender_probability"


class Params(SQLModel):
    """General parameters for api"""

    model_config = {"extra": "forbid"}

    gender: Gender = Field(None)
    age_group: AgeGroup = Field(None)
    country_id: Optional[str] = Field(None, max_length=2)
    min_age: Optional[int] = Field(None)
    max_age: Optional[int] = Field(None)
    min_gender_probability: Optional[float] = Field(None)
    max_country_probability: Optional[float] = Field(None)
    page: int = Field(0, ge=0)
    limit: int = Field(default=10, le=50, gt=0)


class ProfilesParams(Params):
    """Parameters for api/profiles"""

    sort_by: SortByProfiles = Field(None)
    order: OrderBy = Field(None)


ACCEPTED_SORT_BY = {
    SortByProfiles.age: ProfilesDatabase.age,
    SortByProfiles.created_at: ProfilesDatabase.created_at,
    SortByProfiles.gender_probability: ProfilesDatabase.gender_probability,
}
