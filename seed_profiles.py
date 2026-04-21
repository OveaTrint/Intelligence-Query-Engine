import json

from database.database import Session, create_db_and_tables, engine
from models.models import Profiles

create_db_and_tables()
session = Session(engine)


def seed():
    """Loads the database with dummy data provided by HNG"""
    with open("seed_profiles.json") as f:
        json_profiles = json.load(f)

    profiles = json_profiles["profiles"]
    profile_models = [Profiles(**profile) for profile in profiles]

    session.bulk_save_objects(profile_models)
    session.commit()


if __name__ == "__main__":
    seed()
