# Mubify Backend - AI Music Recommendation Assistant

This is the backend service for **Mubify**, an AI music recommendation assistant.

The backend is built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Alembic**.  
It currently supports user authentication, Spotify track search, favorites, dataset import, and a basic music recommendation API.

---

## Tech Stack

| Area | Technology |
|---|---|
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| ORM / SQL Toolkit | SQLAlchemy |
| Database Migration | Alembic |
| Authentication | JWT |
| Password Hashing | Passlib + bcrypt |
| Testing | Pytest |
| Dataset | Kaggle Spotify Tracks Dataset |

---

## Current Features

| Module | Feature | Endpoint |
|---|---|---|
| Health | Check backend / database status | `GET /api/v1/health` or `GET /api/v1/health/db` |
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
| Recommendations | Get similar tracks | `GET /api/v1/recommendations/similar/{track_id}` |

---

## Core Database Objects

| Object | Table | Description |
|---|---|---|
| User | `users` | Stores user account data |
| Track | `tracks` | Stores Spotify track metadata and audio features |
| Favorite | `favorites` | Stores user-favorite track relationships |

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
│   └── main.py
├── data/
├── scripts/
│   └── import_spotify_tracks.py
├── tests/
├── requirements.txt
├── pytest.ini
└── README.md
```

##Future Work

Planned features:

User-based recommendation endpoint
Playlist support
Listening history
ChromaDB integration
RAG-based music search
Natural language music recommendation assistant
Docker support
Deployment setup
