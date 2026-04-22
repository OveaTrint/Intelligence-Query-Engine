from sqlmodel import select

from database.database import session
from models.models import ProfilesDatabase, ProfilesResponse


def format_profiles(profiles):
    """Converts fields in the database to the valid JSON response format"""
    formatted_profiles = [
        ProfilesResponse(
            name=profile.name,
            gender=profile.gender,
            gender_probability=profile.gender_probability,
            age=profile.age,
            age_group=profile.age_group,
            country_id=profile.country_id,
            country_name=profile.country_name,
            country_probability=profile.country_probability,
            created_at=profile.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        for profile in profiles
    ]

    return formatted_profiles


def is_seeded() -> bool:
    """Checks if database has been seeded with dummy data"""
    db_test_rows = 5
    result = session.exec(select(ProfilesDatabase)).fetchmany(db_test_rows)

    if result:
        return True
    return False
