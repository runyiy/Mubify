# Mubify Backend

Mubify is a backend portfolio project for backend engineering job applications. It exposes a
FastAPI API for authentication, music catalog search, favorites, and recommendation workflows
backed by PostgreSQL and ChromaDB.

This repository is a backend-only version extracted from a team project. I was responsible for
the backend implementation; I do not claim responsibility for the original frontend.

## Technology stack

| Area | Technology |
|---|---|
| API | FastAPI, Uvicorn, Pydantic |
| Persistence | PostgreSQL, SQLAlchemy 2.0 |
| Schema migrations | Alembic |
| Authentication | JWT, Passlib, bcrypt |
| Semantic retrieval | ChromaDB |
| Testing | pytest, HTTPX, SQLite test fixtures, coverage.py |
| Quality | Ruff linting and formatting |
| Local infrastructure | Docker, Docker Compose |

## Backend architecture

The application is organized into explicit API, repository, and service layers:

- API routers validate HTTP input, apply authentication dependencies, and translate domain or
  dependency failures into HTTP responses.
- Repositories contain SQLAlchemy queries and persistence operations. PostgreSQL remains the
  source of truth for users, tracks, and favorites.
- Services coordinate recommendation workflows and ChromaDB access without moving relational
  ownership away from PostgreSQL.
- Pydantic schemas define request and response contracts, while SQLAlchemy models define the
  relational data model.

Database access uses SQLAlchemy 2.0 sessions and typed declarative models. Alembic maintains the
schema history for the `users`, `tracks`, and `favorites` tables, including the uniqueness and
relationship constraints used by the API.

Authentication uses bearer JWTs. Registration hashes passwords before persistence, login issues
time-limited access tokens, and protected endpoints resolve the current user through a shared
FastAPI dependency.

## Recommendation design

The project does not use a trained machine-learning recommendation model. Its recommendation
pipeline consists of:

1. ChromaDB semantic candidate retrieval from text representations derived from track metadata
   and audio features.
2. PostgreSQL lookup of the returned track IDs; PostgreSQL is the track source of truth.
3. Heuristic audio-feature and popularity reranking for hybrid recommendation requests.

The reranker uses fields such as danceability, energy, valence, acousticness,
instrumentalness, speechiness, liveness, tempo, and popularity. No benchmark or accuracy gain is
claimed without a reproducible evaluation.

## Core features

- User registration, login, and current-user lookup
- JWT-protected endpoints
- Paginated track listing, text search, and genre filtering
- Track lookup by database ID or Spotify track ID
- Add, list, and remove user favorites
- PostgreSQL audio-feature similarity recommendations
- ChromaDB semantic track retrieval
- Hybrid semantic candidate retrieval and heuristic reranking
- CSV import into PostgreSQL and ChromaDB indexing scripts
- Database and application health endpoints

## API overview

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Application health |
| `GET` | `/api/v1/health/db` | Database connectivity |
| `POST` | `/api/v1/auth/register` | Register a user |
| `POST` | `/api/v1/auth/login` | Obtain a JWT |
| `GET` | `/api/v1/users/me` | Read the authenticated user |
| `GET` | `/api/v1/tracks` | List, search, and filter tracks |
| `GET` | `/api/v1/tracks/{track_db_id}` | Read a track by database ID |
| `GET` | `/api/v1/tracks/spotify/{spotify_track_id}` | Read a track by Spotify ID |
| `GET` | `/api/v1/favorites` | List favorites |
| `POST` | `/api/v1/favorites/{track_id}` | Add a favorite |
| `DELETE` | `/api/v1/favorites/{track_id}` | Remove a favorite |
| `GET` | `/api/v1/recommendations/similar/{track_id}` | Audio-feature similarity |
| `POST` | `/api/v1/recommendations/semantic` | Semantic retrieval |
| `POST` | `/api/v1/recommendations/hybrid` | Semantic retrieval plus reranking |

Interactive OpenAPI documentation is available at `/docs` while the API is running.

## Run with Docker Compose

Docker Compose starts PostgreSQL, applies Alembic migrations, and then starts the API:

```bash
docker compose up --build --wait
```

Verify the services:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/api/v1/health/db
```

Stop the stack and retain the PostgreSQL volume:

```bash
docker compose down
```

Compose defaults are intended for local development. Override credentials and `SECRET_KEY`
through the shell or a local `.env` file before using a shared environment.

## Local development

Python, Alembic, pytest, Ruff, and Docker commands are run from the repository root.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Create a PostgreSQL database, update `.env`, apply migrations, and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Useful migration commands:

```bash
alembic current
alembic heads
alembic history
```

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Yes | None | SQLAlchemy and Alembic PostgreSQL URL |
| `SECRET_KEY` | Yes | None | JWT signing secret |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access-token lifetime |

The application resolves `.env` relative to the repository root, so it does not depend on the
shell's current directory. Never commit `.env` or real credentials.

## Dataset import and ChromaDB indexing

The dataset is not committed. The importer expects a compatible Spotify tracks CSV at
`data/dataset.csv` by default, or accepts an explicit path:

```bash
python scripts/import_spotify_tracks.py
python scripts/import_spotify_tracks.py /absolute/path/to/dataset.csv
```

The expected columns are:

```text
track_id,artists,album_name,track_name,popularity,duration_ms,explicit,
danceability,energy,key,loudness,mode,speechiness,acousticness,
instrumentalness,liveness,valence,tempo,time_signature,track_genre
```

After importing tracks, build the local semantic index:

```bash
python scripts/index_tracks_chroma.py
python scripts/index_tracks_chroma.py --limit 1000 --batch-size 500
```

Generated datasets and the local `chroma_db/` persistence directory are ignored by Git and the
Docker build context. The repository does not redistribute the third-party dataset.

## Tests and code quality

Run the full checks from the repository root:

```bash
ruff check .
ruff format --check .
python -m pytest
python -m pytest --cov=app --cov-report=term-missing
```

Tests use SQLite fixtures where practical and set isolated configuration values in
`tests/conftest.py`; they do not require the local `.env` file.

## Project structure

```text
.
├── app/
│   ├── api/                 # FastAPI dependencies, routers, and endpoints
│   ├── core/                # Configuration and JWT/password security
│   ├── db/                  # SQLAlchemy base and sessions
│   ├── models/              # Relational models
│   ├── repositories/        # Persistence queries
│   ├── schemas/             # API request and response contracts
│   ├── services/            # ChromaDB and recommendation workflows
│   └── main.py              # ASGI application
├── alembic/                 # Migration environment and revisions
├── scripts/                 # Dataset import and Chroma indexing
├── tests/                   # Unit and API tests
├── .github/workflows/       # Backend CI
├── Dockerfile
├── compose.yaml
├── alembic.ini
├── pyproject.toml
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

## Current limitations and future improvements

- ChromaDB is a local persistent index and must be rebuilt after relevant track imports.
- The Compose stack persists PostgreSQL data but does not currently persist ChromaDB through a
  named volume.
- Dataset quality and licensing must be validated independently before redistribution or broader
  use.
- The project has no published recommendation-quality benchmark.
- Potential future work includes listening-history signals, playlist workflows, repeatable
  recommendation evaluation, stronger operational observability, and deployment configuration.

This repository demonstrates backend design and implementation; it is not presented as
production-ready.
