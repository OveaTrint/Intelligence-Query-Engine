import re
from typing import Dict, List

import pycountry

# import pycountry


MALE_KEYWORDS = (
    "males",
    "boys",
    "male",
    "boy",
    "man",
    "men",
)
FEMALE_KEYWORDS = (
    "female",
    "females",
    "girls",
    "girl",
    "woman",
    "women",
)

CHILD_KEYWORDS = (
    "children",
    "child",
    "baby",
    "babies",
)
TEENAGER_KEYWORDS = (
    "teenagers",
    "teenager",
    "teen",
    "teens",
)
ADULT_KEYWORDS = (
    "adults",
    "adult",
)
SENIOR_KEYWORDS = (
    "senior",
    "seniors",
    "elder",
    "elders",
    "elderly",
    "pensioner",
    "pensioners",
)


def get_gender(query: List[str]):
    filter = {}

    is_male = any(word in MALE_KEYWORDS for word in query)
    is_female = any(word in FEMALE_KEYWORDS for word in query)

    if is_male and is_female:
        pass
    elif is_male:
        filter["gender"] = "male"
    elif is_female:
        filter["gender"] = "female"

    return filter


def get_age_group(query: List[str]) -> Dict:
    filter = {}

    is_child = any(word in CHILD_KEYWORDS for word in query)
    is_teenager = any(word in TEENAGER_KEYWORDS for word in query)
    is_adult = any(word in ADULT_KEYWORDS for word in query)
    is_senior = any(word in SENIOR_KEYWORDS for word in query)

    if is_child:
        filter["age_group"] = "child"
    elif is_teenager:
        filter["age_group"] = "teenager"
    elif is_adult:
        filter["age_group"] = "adult"
    elif is_senior:
        filter["age_group"] = "senior"

    return filter


def get_age(query: str) -> Dict:
    filter = {}

    # checks whether young is in the query
    is_young = "young" in query

    # Checks if "young" is specified, overrides any other age parsing is so.
    if is_young:
        filter["min_age"] = 16
        filter["max_age"] = 24

    # uses regex to check for min age e.g if "older than 24" = {"min_age": 24} , "over 45" = {"min_age": 45}
    min_age_match = re.search(r"\b(?:older than|over|above|more than)\s+(\d+)\b", query)
    if min_age_match and not is_young:
        filter["min_age"] = int(min_age_match.group(1))

    # likewise uses regex for the same thing but for max_age e.g "younger than 34" = {"max_age": 24}, "under 43" = {"max_age":43}
    max_age_match = re.search(
        r"\b(?:younger than|under|below|less than)\s+(\d+)\b", query
    )
    if max_age_match and not is_young:
        filter["max_age"] = int(max_age_match.group(1))

    # checks between ages e.g between 30 and 70 =  {"min_age": 30, "max_age":70}
    between_age_match = re.search(
        r"\b(?:between|aged?)\s+(\d+)\s+(?:and|to|-)\s+(\d+)\b", query
    )
    if between_age_match and not is_young:
        filter["min_age"] = int(between_age_match.group(1))
        filter["max_age"] = int(between_age_match.group(2))

    return filter


def get_country_id(query: str) -> Dict:
    filter = {}

    # checks values after in and from to get country name
    country_match = re.search(r"\b(?:in|from?)\s+(\w+)\b", query)
    if country_match:
        country = country_match.group(1)
        try:
            country_id = pycountry.countries.get(name=country).alpha_2
            filter["country_id"] = country_id
        except AttributeError:
            return filter

    return filter


def parse_query(query: str) -> Dict:
    """Parses query string to query parameters using rules"""
    filters = {}

    # remove special characters
    query = re.sub(r"[^a-zA-z0-9 ]+", "", query)

    # make query lowercase and tokenize it to make it easy to parse
    query = query.lower()
    tokenized_query = query.split()

    # helper functions for each parsing
    gender = get_gender(tokenized_query)
    age_group = get_age_group(tokenized_query)
    age = get_age(query)
    country_id = get_country_id(query)

    if gender:
        filters.update(gender)
    if age_group:
        filters.update(age_group)
    if age:
        filters.update(age)
    if country_id:
        filters.update(country_id)

    return filters
