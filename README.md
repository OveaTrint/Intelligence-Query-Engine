# Intelligence Query Engine

A FastAPI-powered profile query engine that supports both structured filtering and natural-language-style search over profile data.

## Features

- REST API built with **FastAPI**
- Data persistence with **SQLModel + SQLAlchemy** and PostgreSQL driver support (`psycopg`)
- Structured filtering endpoint with:
  - gender
  - age group
  - country code
  - min/max age
  - probability filters
  - sorting and pagination
- Natural-language search endpoint (`/api/search`)
- Centralized custom error handling and validation responses
- Seed script for loading sample profile data

---

## Tech Stack

- Python (>= 3.14)
- FastAPI
- SQLModel / SQLAlchemy
- psycopg (binary)
- Pydantic
- pycountry
- Uvicorn
- python-dotenv

---

## Project Structure

```text
Intelligence-Query-Engine/
├── core/
│   ├── __init__.py
│   └── config.py
├── database/
│   ├── __init__.py
│   └── database.py
├── exceptions/
│   ├── __init__.py
│   └── exceptions.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   └── schemas.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── main.py
├── query_parser.py
├── seed_profiles.py
├── seed_profiles.json
├── pyproject.toml
└── README.md
```

---

## Getting Started

### 1) Clone the repository

```bash
git clone https://github.com/OveaTrint/Intelligence-Query-Engine.git
cd Intelligence-Query-Engine
```

### 2) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

> On Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

If you use `uv`:
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

### 4) Configure environment

Set up any required environment variables (for example DB connection details) in your environment or `.env` file, depending on how `core/config.py` is wired.

### 5) Run the API

```bash
uvicorn main:app --reload
```

The service will be available at:

- API root: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Database Seeding

To populate the database with sample profiles from `seed_profiles.json`:

```bash
python -c "from seed_profiles import seed; seed()"
```

---

## API Endpoints

### Health Check

- **GET /**  
Returns a simple alive message.

---

### Get Profiles (Structured Query)

- **GET /api/profiles**

Supports query parameters from `ProfilesParams` (defined in `models/schemas.py`), including pagination, filtering, and sorting.

Typical parameters include:

- `page`
- `limit`
- `gender`
- `age_group`
- `country_id`
- `min_age`
- `max_age`
- `min_gender_probability`
- `max_country_probability`
- `sort_by`
- `order`

---

### Search Profiles (Natural Language Query)

- **GET /api/search**

Parameters:

- `q` (string, required): natural language query
- `page` (int, default: 1)
- `limit` (int, default: 10, max: 50)

This endpoint parses the `q` input and converts it to filters before querying profiles.

---

## NLQ Parsing

The `/api/search` endpoint uses a rule-based parser in `query_parser.py` to convert free-text queries into structured filters.

Internally, `parse_query(query: str)`:

1. removes special characters,
2. lowercases the query,
3. tokenizes words for keyword matching,
4. runs dedicated extractors for:
   - gender
   - age group
   - age constraints
   - country
5. merges extracted values into one `filters` dict.

---

### 1) Gender parsing (`get_gender`)

`get_gender` checks tokenized words against keyword sets:

- Male keywords: `males, boys, male, boy, man, men`
- Female keywords: `female, females, girls, girl, woman, women`

Output behavior:

- male match only → `{"gender": "male"}`
- female match only → `{"gender": "female"}`
- both male and female present → no gender filter is added
- neither present → no gender filter

---

### 2) Age-group parsing (`get_age_group`)

`get_age_group` maps tokens to one age-group field using priority order:

1. `child` keywords: `children, child, baby, babies`
2. `teenager` keywords: `teenagers, teenager, teen, teens`
3. `adult` keywords: `adults, adult`
4. `senior` keywords: `senior, seniors, elder, elders, elderly, pensioner, pensioners`

Because this is an `if/elif` chain, only **one** group is selected (first match by priority).

Example:
- query contains both `adult` and `senior` → result is `adult` (adult check runs before senior).

---

### 3) Age / ages parsing (`get_age`)

`get_age` supports the following rules:

#### a) `young` shortcut (highest precedence)
If `"young"` appears anywhere in the normalized query:

- `min_age = 16`
- `max_age = 24`

When `young` is present, other regex-based age rules are ignored.

#### b) Minimum age patterns
Regex:
- `older than X`
- `over X`
- `above X`
- `more than X`

Result:
- `{"min_age": X}`

#### c) Maximum age patterns
Regex:
- `younger than X`
- `under X`
- `below X`
- `less than X`

Result:
- `{"max_age": X}`

#### d) Range patterns
Regex:
- `between X and Y`
- `between X to Y`
- `between X - Y`
- `age X and Y`
- `aged X and Y` (and `to` / `-` variants)

Result:
- `{"min_age": X, "max_age": Y}`

---

### 4) Country parsing (`get_country_id`)

`get_country_id` looks for a single word after `in` or `from`, then tries to resolve it using `pycountry`:

- pattern: `in <word>` or `from <word>`
- resolution: `pycountry.countries.get(name=<word>).alpha_2`
- output: `{"country_id": "<ISO_ALPHA2>"}`

If lookup fails, no country filter is added.

---

### 5) Final merge behavior (`parse_query`)

`parse_query` merges non-empty outputs from:

- `get_gender`
- `get_age_group`
- `get_age`
- `get_country_id`

Only detected fields are returned; missing/unknown parts are simply omitted.

---

## Limitations (current implementation)

1. **Single-word country extraction only**  
   `in united states` captures only `united`, so multi-word country names are not handled correctly.

2. **Exact country name matching in pycountry**  
   Inputs like `usa`, `uk`, `u.s.`, or common aliases are not guaranteed to resolve.

3. **Only first `in/from` country match is considered**  
   Queries with multiple locations are not fully interpreted.

4. **Gender conflict drops gender filter**  
   If both male and female keywords appear, parser returns no gender value.

5. **Age-group priority is fixed**  
   If multiple age-group keywords appear, only the first matched branch in priority order is used.

6. **`young` overrides all other age logic**  
   Any query containing `young` forces `16–24`, even if explicit numeric ages are also present.

7. **No validation for contradictory age constraints**  
   The parser does not reject cases like `older than 50 under 20`; it may return conflicting bounds.

8. **No plural/phrase intelligence beyond defined patterns**  
   Parsing is regex + keyword based, not semantic NLP. Unsupported phrasing may be ignored.

9. **Special-character stripping can alter intent**  
   Input is sanitized with `re.sub(r"[^a-zA-z0-9 ]+", "", query)`, which may change punctuation-based meaning.

10. **No spelling correction or fuzzy matching**  
   Misspellings in gender/age keywords or country names are not corrected.

---

## Example NLQ conversions

- `female adults in canada older than 30`  
  → `{"gender":"female","age_group":"adult","min_age":30,"country_id":"CA"}`

- `young men from nigeria`  
  → `{"gender":"male","min_age":16,"max_age":24,"country_id":"NG"}`

- `between 20 and 35 women in france`  
  → `{"gender":"female","min_age":20,"max_age":35,"country_id":"FR"}`

---

## Error Handling

The API returns structured error responses for common failure cases:

- `400` Bad Request:
  - missing/empty parameter
  - invalid query parameters
  - un-interpretable NLQ query
- `404` Not Found:
  - profile not found
- `422` Unprocessable Content:
  - invalid parameter type
- `500` Internal Server Error:
  - unexpected server failure

---

## Notes

- CORS is currently configured permissively (`allow_origins=["*"]`) for easier development/testing.
- Pagination offset is computed in code using page and limit.
- Sorting is only applied when `sort_by` is present; `order` must be paired with `sort_by`.

---
