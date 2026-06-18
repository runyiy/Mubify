import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import anyio.to_thread
import anyio
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.db.session import get_db
from app.main import app
from app.models.track import Track


async def _run_sync_inline(func, *args, **kwargs):
    return func(*args)


anyio.to_thread.run_sync = _run_sync_inline


class ASGITestClient:
    def __init__(self, app):
        self.app = app

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def request(self, method: str, url: str, **kwargs):
        async def send_request():
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, url, **kwargs)

        return anyio.run(send_request)

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request("DELETE", url, **kwargs)


SQLALCHEMY_DATABASE_URL = "sqlite://"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture()
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(setup_test_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with ASGITestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def track_factory(db_session):
    counter = {"value": 0}

    def _create_track(**overrides):
        counter["value"] += 1
        n = counter["value"]

        data = {
            "track_id": f"spotify_test_track_{n}",
            "artists": f"Test Artist {n}",
            "album_name": f"Test Album {n}",
            "track_name": f"Test Song {n}",
            "popularity": 50,
            "duration_ms": 200000,
            "explicit": False,
            "danceability": 0.5,
            "energy": 0.5,
            "key": 1,
            "loudness": -5.0,
            "mode": 1,
            "speechiness": 0.05,
            "acousticness": 0.2,
            "instrumentalness": 0.0,
            "liveness": 0.1,
            "valence": 0.5,
            "tempo": 120.0,
            "time_signature": 4,
            "track_genre": "pop",
        }

        data.update(overrides)

        track = Track(**data)
        db_session.add(track)
        db_session.commit()
        db_session.refresh(track)

        return track

    return _create_track


@pytest.fixture()
def registered_user(client):
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201

    return payload


@pytest.fixture()
def auth_token(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
