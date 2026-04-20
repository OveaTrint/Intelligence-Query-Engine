import json

from database.database import session
from models.models import Profiles


def seed():
    with open("seed_profiles.json") as f:
        json_profiles = json.load(f)

    profiles = json_profiles["profiles"]
    profile_models = [Profiles(**profile) for profile in profiles]

    session.bulk_save_objects(profile_models)
    session.commit()


if __name__ == "__main__":
    seed()
