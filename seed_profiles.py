import json

from database.database import session
from models.models import ProfilesDatabase


def seed() -> None:
    """Populates the database with dummy data provided by HNG"""
    with open("seed_profiles.json") as f:
        json_profiles = json.load(f)

    profiles = json_profiles["profiles"]
    profile_models = [ProfilesDatabase(**profile) for profile in profiles]

    session.bulk_save_objects(profile_models)
    session.commit()
