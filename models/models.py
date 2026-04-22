import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import UUID7
from sqlalchemy import Column, text
from sqlmodel import TIMESTAMP, Field, SQLModel


class Profiles(SQLModel):
    """General Profile Fields"""

    id: Optional[UUID7] = Field(default_factory=uuid.uuid7, primary_key=True)
    name: str = Field(unique=True)
    gender: str = Field(index=True)
    gender_probability: Decimal = Field(decimal_places=2, index=True)
    age: int = Field(index=True)
    age_group: str = Field(index=True)
    country_id: str = Field(max_length=2, index=True)
    country_name: str
    country_probability: Decimal = Field(decimal_places=2, index=True)


class ProfilesDatabase(Profiles, table=True):
    """Profile class for the database with non-formatted date"""

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
        ),
    )


class ProfilesResponse(Profiles):
    """Profiles class for the JSON response"""

    created_at: str
