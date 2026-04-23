import re
from typing import Dict, List

import pycountry

MALE_KEYWORDS = (
    "males",
    "boys",
    "male",
    "boy",
    "man",
    "men",
    "gentleman",
    "gentlemen",
)
FEMALE_KEYWORDS = (
    "female",
    "females",
    "girls",
    "girl",
    "woman",
    "women",
    "lady",
    "ladies",
)

CHILD_KEYWORDS = (
    "children",
    "child",
    "baby",
    "babies",
    "kid",
    "kids",
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


def get_gender(tokens: List[str]) -> Dict:
    filter = {}

    is_male = any(word in MALE_KEYWORDS for word in tokens)
    is_female = any(word in FEMALE_KEYWORDS for word in tokens)

    if is_male and is_female:
        pass
    elif is_male:
        filter["gender"] = "male"
    elif is_female:
        filter["gender"] = "female"

    return filter


def get_age_group(tokens: List[str]) -> Dict:
    filter = {}

    if any(word in CHILD_KEYWORDS for word in tokens):
        filter["age_group"] = "child"
    elif any(word in TEENAGER_KEYWORDS for word in tokens):
        filter["age_group"] = "teenager"
    elif any(word in ADULT_KEYWORDS for word in tokens):
        filter["age_group"] = "adult"
    elif any(word in SENIOR_KEYWORDS for word in tokens):
        filter["age_group"] = "senior"

    return filter


def get_age(query: str) -> Dict:
    filter = {}

    between_age_match = re.search(
        r"\b(?:between|aged?|ages)\s+(\d+)\s+(?:and|to|-)\s+(\d+)\b", query
    )
    if between_age_match:
        filter["min_age"] = int(between_age_match.group(1))
        filter["max_age"] = int(between_age_match.group(2))
        return filter

    exact_age_match = re.search(r"\b(\d+)\s*[- ]?\s*years?\s+old\b", query)
    if exact_age_match:
        age = int(exact_age_match.group(1))
        filter["min_age"] = age
        filter["max_age"] = age
        return filter

    min_age_match = re.search(
        r"\b(?:older than|over|above|more than|greater than|at least)\s+(\d+)\b",
        query,
    )
    if min_age_match:
        filter["min_age"] = int(min_age_match.group(1))
    else:
        plus_match = re.search(r"\b(\d+)\s*\+", query)
        if plus_match:
            filter["min_age"] = int(plus_match.group(1))

    # "younger than N" / "under N" / "below N" / "less than N" / "at most N"
    max_age_match = re.search(
        r"\b(?:younger than|under|below|less than|at most)\s+(\d+)\b", query
    )
    if max_age_match:
        filter["max_age"] = int(max_age_match.group(1))

    if (
        re.search(r"\byoung\b", query)
        and "min_age" not in filter
        and "max_age" not in filter
    ):
        filter["min_age"] = 16
        filter["max_age"] = 24

    return filter


def _resolve_country(candidate: str) -> str | None:
    candidate = candidate.strip()
    if not candidate:
        return None
    try:
        return pycountry.countries.lookup(candidate).alpha_2
    except LookupError:
        return None


def get_country_id(query: str) -> Dict:
    filter = {}

    # Capture the word immediately after "in" / "from".
    country_match = re.search(r"\b(?:in|from)\s+(\w+)\b", query)
    if not country_match:
        return filter

    resolved = _resolve_country(country_match.group(1))
    if resolved:
        filter["country_id"] = resolved

    return filter


def parse_query(query: str) -> Dict:
    """Parses a natural-language query into API filter parameters."""
    if not query or not query.strip():
        return {}

    filters = {}

    cleaned = re.sub(r"[^a-zA-Z0-9+\- ]+", " ", query).lower()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    tokenized_query = cleaned.split()

    filters.update(get_gender(tokenized_query))
    filters.update(get_age_group(tokenized_query))
    filters.update(get_age(cleaned))
    filters.update(get_country_id(cleaned))

    return filters
