import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints.health import check_database


class FailingSession:
    def execute(self, statement):
        raise SQLAlchemyError("database unavailable")


def test_health_check_success(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_check_success(client):
    response = client.get("/api/v1/health/db")

    assert response.status_code == 200
    assert response.json() == {"database": "ok"}


def test_database_health_check_failure_returns_503():
    with pytest.raises(HTTPException) as exc_info:
        check_database(db=FailingSession())

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Database health check failed"
