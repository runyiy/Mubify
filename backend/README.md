# Mubify Backend - AI Music Recommendation Assistant

This is the backend service for **Mubify**, an AI music recommendation assistant.

The backend is built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Alembic**, and **ChromaDB**.
It currently supports user authentication, Spotify track search, favorites, CSV dataset import,
audio-feature recommendations, semantic music search, and hybrid recommendations.

---

## Tech Stack

| Area | Technology |
|---|---|
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| ORM / SQL Toolkit | SQLAlchemy |
| Database Migration | Alembic |
| Vector Search | ChromaDB |
| Authentication | JWT |
| Password Hashing | Passlib + bcrypt |
| Testing | Pytest |
| Dataset | Spotify tracks CSV (exact source pending confirmation) |

---

## Current Features

| Module | Feature | Endpoint |
|---|---|---|
| Health | Check API status | `GET /health` |
| Health | Check database status | `GET /api/v1/health/db` |
| Auth | Register user | `POST /api/v1/auth/register` |
| Auth | Login user | `POST /api/v1/auth/login` |
| Users | Get current user | `GET /api/v1/users/me` |
| Tracks | Get track list | `GET /api/v1/tracks` |
| Tracks | Search tracks | `GET /api/v1/tracks?search=love` |
| Tracks | Filter by genre | `GET /api/v1/tracks?genre=pop` |
| Tracks | Get track by database ID | `GET /api/v1/tracks/{track_db_id}` |
| Tracks | Get track by Spotify track ID | `GET /api/v1/tracks/spotify/{spotify_track_id}` |
| Favorites | Get user favorites | `GET /api/v1/favorites` |
| Favorites | Add favorite track | `POST /api/v1/favorites/{track_id}` |
| Favorites | Remove favorite track | `DELETE /api/v1/favorites/{track_id}` |
| Recommendations | Get similar tracks by audio features | `GET /api/v1/recommendations/similar/{track_id}` |
| Recommendations | Natural-language semantic search with ChromaDB | `POST /api/v1/recommendations/semantic` |
| Recommendations | Hybrid semantic + audio-feature recommendations | `POST /api/v1/recommendations/hybrid` |

---

## Recommendation APIs

### Similar Tracks

`GET /api/v1/recommendations/similar/{track_id}`

Query parameters:

| Name | Type | Default | Notes |
|---|---|---|---|
| `limit` | integer | `20` | Must be between 1 and 100 |
| `same_genre_only` | boolean | `false` | When true, only returns tracks from the same genre |

This endpoint uses PostgreSQL track audio features and does not require ChromaDB.

### Semantic Recommendations

`POST /api/v1/recommendations/semantic`

Request body:

```json
{
  "query": "upbeat pop songs for a workout",
  "limit": 20,
  "genre": "pop"
}
```

Fields:

| Name | Type | Default | Notes |
|---|---|---|---|
| `query` | string | required | Must be 1 to 500 characters |
| `limit` | integer | `20` | Must be between 1 and 50 |
| `genre` | string or null | `null` | Optional Chroma metadata filter |

This endpoint queries the ChromaDB collection used by the recommendation service.
It returns tracks from PostgreSQL using the database IDs stored in Chroma.

### Hybrid Recommendations

`POST /api/v1/recommendations/hybrid`

Request body:

```json
{
  "query": "calm acoustic music for studying",
  "limit": 20,
  "candidate_pool_size": 100,
  "genre": "acoustic"
}
```

Fields:

| Name | Type | Default | Notes |
|---|---|---|---|
| `query` | string | required | Must be 1 to 500 characters |
| `limit` | integer | `20` | Must be between 1 and 50 |
| `candidate_pool_size` | integer | `100` | Must be between 20 and 500 |
| `genre` | string or null | `null` | Optional Chroma metadata filter |

This endpoint first retrieves candidates from ChromaDB, then reranks them with audio features
such as `danceability`, `energy`, `valence`, `acousticness`, `instrumentalness`,
`speechiness`, `liveness`, `tempo`, and `popularity`.

---

## Core Database Objects

| Object | Table | Description |
|---|---|---|
| User | `users` | Stores user account data |
| Track | `tracks` | Stores Spotify track metadata and audio features |
| Favorite | `favorites` | Stores user-favorite track relationships |

PostgreSQL is the source of truth for tracks. ChromaDB stores derived natural-language
documents and metadata for semantic search.

---

## Setup

From the backend directory:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The `.env` file must live at:

```text
backend/.env
```

The backend loads that file directly, so commands may be run from the repository
root or from the backend directory.

Edit `.env` so the required values match your local environment:

| Name | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection URL used by the API, scripts, and Alembic |
| `SECRET_KEY` | Yes | JWT signing secret; replace the example value for local development |
| `JWT_ALGORITHM` | No | Defaults to `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Defaults to `30` |

If startup fails with `Missing backend configuration`, create `backend/.env`
from `backend/.env.example` or set the missing environment variables before
running the command.

### Create a Local PostgreSQL Database

The project currently expects PostgreSQL. Docker setup is not included, so the
following example uses a locally installed PostgreSQL server.

On Linux, open PostgreSQL as its administrative user:

```bash
sudo -u postgres psql
```

Create a dedicated local user and database:

```sql
CREATE USER mubify_user WITH PASSWORD 'change_me';
CREATE DATABASE mubify OWNER mubify_user;
\q
```

Update `backend/.env` to use the same credentials:

```dotenv
DATABASE_URL=postgresql://mubify_user:change_me@localhost:5432/mubify
SECRET_KEY=replace-this-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

The PostgreSQL URL has this format:

```text
postgresql://<username>:<password>@<host>:<port>/<database>
```

If the password contains URL-reserved characters such as `@`, `:`, or `/`, URL-encode
those characters in `DATABASE_URL`. PostgreSQL installation and service startup commands
vary by operating system; confirm that the server is running before continuing.

You can test the example connection with:

```bash
psql "postgresql://mubify_user:change_me@localhost:5432/mubify"
```

Apply database migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

By default, the local API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

---

## Import Spotify Tracks

The import script reads a Spotify CSV file and inserts tracks into PostgreSQL.

The dataset is not committed to this repository. Create the data directory and manually
place a compatible CSV file at the default location:

```bash
mkdir -p data
# Manually place the prepared CSV at: data/dataset.csv
```

Default CSV path:

```text
backend/data/dataset.csv
```

Run with the default path:

```bash
python scripts/import_spotify_tracks.py
```

Run with an explicit CSV path:

```bash
python scripts/import_spotify_tracks.py path/to/dataset.csv
```

The script:

- skips rows missing required track fields
- parses numeric audio features
- inserts in batches of 1000
- skips duplicate Spotify `track_id` values using PostgreSQL `ON CONFLICT DO NOTHING`

At minimum, each imported row must contain non-empty values for:

```text
track_id, artists, album_name, track_name, track_genre
```

TODO: The repository does not currently identify the team's exact dataset download
source, original filename, version, or license. Obtain a compatible `dataset.csv` from
the project maintainer and place it manually at `backend/data/dataset.csv`. Do not assume
that every similarly named Spotify dataset has the columns expected by the import script.

---

## Index Tracks Into ChromaDB

Semantic and hybrid recommendation endpoints require ChromaDB to be indexed after
tracks have been imported into PostgreSQL.

Run the Chroma indexing script:

```bash
python scripts/index_tracks_chroma.py
```

Optional flags:

```bash
python scripts/index_tracks_chroma.py --limit 1000 --batch-size 500
```

The script:

- reads tracks from PostgreSQL in ascending database ID order
- converts each track into a natural-language document
- stores metadata such as database ID, Spotify ID, track name, artists, genre, popularity, and audio features
- upserts documents into the Chroma collection used by the recommendation service

The Chroma client currently uses the local path:

```text
./chroma_db
```

Run this script again after importing new tracks if those tracks should appear in
semantic or hybrid recommendations.

---

## Suggested Local Workflow

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
mkdir -p data
# Manually place the prepared CSV at data/dataset.csv before continuing.
python scripts/import_spotify_tracks.py
pip install -r requirements-ai.txt
python scripts/index_tracks_chroma.py
uvicorn app.main:app --reload
```

Then verify:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/health/db
curl "http://127.0.0.1:8000/api/v1/tracks?limit=5"
```

Example semantic recommendation request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/recommendations/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"upbeat pop songs","limit":5}'
```

Example hybrid recommendation request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/recommendations/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query":"calm acoustic songs","limit":5,"candidate_pool_size":50}'
```

---

## Before You Start

Check the following before running migrations or starting the API:

- the virtual environment is active and `requirements.txt` is installed
- PostgreSQL is installed, running, and accepts the credentials in `backend/.env`
- `backend/.env` exists and contains `DATABASE_URL` and `SECRET_KEY`
- `alembic upgrade head` completes successfully
- `backend/data/dataset.csv` exists before running the default import command
- `requirements-ai.txt` is installed before Chroma indexing or semantic recommendations
- tracks have been imported into PostgreSQL before building the Chroma index

## Common Setup Errors

### Database connection fails

Confirm that PostgreSQL is running and that the username, password, port, and database
name in `DATABASE_URL` match the values created in PostgreSQL. Test the same URL directly:

```bash
psql "$DATABASE_URL"
```

If the shell does not load variables from `backend/.env`, pass the URL explicitly to
`psql` instead. The application itself reads `backend/.env` directly.

### `CSV file not found`

The default import command expects this exact path:

```text
backend/data/dataset.csv
```

Create `backend/data/` and place the CSV there, or provide an explicit file path:

```bash
python scripts/import_spotify_tracks.py /absolute/path/to/dataset.csv
```

### Semantic or hybrid recommendations report that the index is unavailable

Install the AI dependencies, import tracks into PostgreSQL, and then build the Chroma
index before calling these endpoints:

```bash
pip install -r requirements-ai.txt
python scripts/index_tracks_chroma.py
```

---

## Testing

Run tests from the backend directory:

```bash
pip install -r requirements-dev.txt
pytest
```

Tests set their own safe `DATABASE_URL` and `SECRET_KEY` in `tests/conftest.py`,
so they do not require a local `backend/.env`.

The existing tests cover authentication, tracks, favorites, audio-feature recommendations,
and CSV row parsing.

TODO: Add tests for the Chroma-backed `semantic` and `hybrid` recommendation endpoints.

---

## Project Structure

```text
backend/
├── alembic/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── favorites.py
│   │           ├── health.py
│   │           ├── recommendations.py
│   │           ├── tracks.py
│   │           └── users.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── favorite.py
│   │   ├── track.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── favorite_repository.py
│   │   ├── recommendation_repository.py
│   │   ├── track_repository.py
│   │   └── user_repository.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── favorite.py
│   │   ├── recommendation.py
│   │   ├── track.py
│   │   └── user.py
│   ├── services/
│   │   ├── chroma_service.py
│   │   ├── hybrid_recommendation_service.py
│   │   └── semantic_recommendation_service.py
│   └── main.py
├── data/
├── scripts/
│   ├── import_spotify_tracks.py
│   └── index_tracks_chroma.py
├── tests/
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Future Work

Planned or incomplete features:

- user-based recommendation endpoint
- playlist support
- listening history
- RAG-based music assistant
- Docker support
- deployment setup
- Chroma-backed endpoint tests
