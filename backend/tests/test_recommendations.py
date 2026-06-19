import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import recommendations as recommendations_endpoint
from app.schemas.recommendation import HybridRecommendationRequest
from app.schemas.recommendation import SemanticRecommendationRequest
from app.services import hybrid_recommendation_service
from app.services import semantic_recommendation_service
from app.services.recommendation_errors import (
    RecommendationDependencyUnavailableError,
    RecommendationIndexCorruptError,
    RecommendationIndexNotReadyError,
)


class FakeCollection:
    def __init__(self, count=1, query_result=None, query_error=None):
        self._count = count
        self._query_result = query_result or {
            "ids": [[]],
            "distances": [[]],
        }
        self._query_error = query_error

    def count(self):
        return self._count

    def query(self, **kwargs):
        if self._query_error:
            raise self._query_error

        return self._query_result


@pytest.mark.parametrize(
    ("error", "expected_status_code"),
    [
        (
            RecommendationIndexNotReadyError("Recommendation index is not ready."),
            503,
        ),
        (
            RecommendationDependencyUnavailableError(
                "ChromaDB recommendation index is unavailable."
            ),
            503,
        ),
        (
            RecommendationIndexCorruptError(
                "Recommendation index is inconsistent with the track database."
            ),
            500,
        ),
    ],
)
def test_handle_recommendation_error_maps_status_code_and_detail(
    error,
    expected_status_code,
):
    with pytest.raises(HTTPException) as exc_info:
        recommendations_endpoint.handle_recommendation_error(error)

    assert exc_info.value.status_code == expected_status_code
    assert exc_info.value.detail == str(error)


def test_get_similar_tracks_not_found(client):
    response = client.get("/api/v1/recommendations/similar/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found"


def test_get_similar_tracks_success(client, track_factory):
    target = track_factory(
        track_name="Target Song",
        track_genre="pop",
        danceability=0.8,
        energy=0.8,
        valence=0.8,
        tempo=120.0,
        popularity=80,
    )

    similar = track_factory(
        track_name="Similar Song",
        track_genre="pop",
        danceability=0.79,
        energy=0.81,
        valence=0.78,
        tempo=121.0,
        popularity=79,
    )

    different = track_factory(
        track_name="Different Song",
        track_genre="metal",
        danceability=0.1,
        energy=0.2,
        valence=0.1,
        tempo=180.0,
        popularity=20,
    )

    response = client.get(f"/api/v1/recommendations/similar/{target.id}?limit=2")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    returned_track_ids = [item["track"]["id"] for item in data]

    assert target.id not in returned_track_ids
    assert similar.id in returned_track_ids
    assert different.id in returned_track_ids

    assert "similarity_score" in data[0]
    assert isinstance(data[0]["similarity_score"], float)


def test_get_similar_tracks_respects_limit(client, track_factory):
    target = track_factory(track_name="Target Song")

    track_factory(track_name="Similar 1")
    track_factory(track_name="Similar 2")
    track_factory(track_name="Similar 3")

    response = client.get(f"/api/v1/recommendations/similar/{target.id}?limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_similar_tracks_same_genre_only(client, track_factory):
    target = track_factory(
        track_name="Target Pop Song",
        track_genre="pop",
    )

    pop_track = track_factory(
        track_name="Another Pop Song",
        track_genre="pop",
    )

    rock_track = track_factory(
        track_name="Rock Song",
        track_genre="rock",
    )

    response = client.get(
        f"/api/v1/recommendations/similar/{target.id}"
        "?limit=10&same_genre_only=true"
    )

    assert response.status_code == 200

    data = response.json()

    returned_track_ids = [item["track"]["id"] for item in data]

    assert pop_track.id in returned_track_ids
    assert rock_track.id not in returned_track_ids

    for item in data:
        assert item["track"]["track_genre"] == "pop"


def test_get_similar_tracks_invalid_limit_returns_422(client, track_factory):
    target = track_factory()

    response = client.get(f"/api/v1/recommendations/similar/{target.id}?limit=0")

    assert response.status_code == 422


def test_get_similar_tracks_limit_too_large_returns_422(client, track_factory):
    target = track_factory()

    response = client.get(f"/api/v1/recommendations/similar/{target.id}?limit=101")

    assert response.status_code == 422


def test_semantic_recommendations_chroma_unavailable_returns_503(monkeypatch):
    def raise_chroma_unavailable(**kwargs):
        raise RecommendationDependencyUnavailableError(
            "ChromaDB recommendation index is unavailable."
        )

    monkeypatch.setattr(
        recommendations_endpoint,
        "semantic_track_search",
        raise_chroma_unavailable,
    )

    request = SemanticRecommendationRequest(
        query="upbeat pop songs",
        limit=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        recommendations_endpoint.read_semantic_recommendations(
            request=request,
            db=None,
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "ChromaDB recommendation index is unavailable."


def test_hybrid_recommendations_index_not_ready_returns_503(monkeypatch):
    def raise_index_not_ready(**kwargs):
        raise RecommendationIndexNotReadyError(
            "Recommendation index is not ready. Import tracks and run Chroma indexing first."
        )

    monkeypatch.setattr(
        recommendations_endpoint,
        "hybrid_recommendation_search",
        raise_index_not_ready,
    )

    request = HybridRecommendationRequest(
        query="calm acoustic songs",
        limit=5,
        candidate_pool_size=50,
    )

    with pytest.raises(HTTPException) as exc_info:
        recommendations_endpoint.read_hybrid_recommendations(
            request=request,
            db=None,
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "Recommendation index is not ready. Import tracks and run Chroma indexing first."
    )


def test_semantic_recommendations_index_corrupt_returns_500(monkeypatch):
    def raise_index_corrupt(**kwargs):
        raise RecommendationIndexCorruptError(
            "Recommendation index is inconsistent with the track database."
        )

    monkeypatch.setattr(
        recommendations_endpoint,
        "semantic_track_search",
        raise_index_corrupt,
    )

    request = SemanticRecommendationRequest(
        query="upbeat pop songs",
        limit=5,
    )

    with pytest.raises(HTTPException) as exc_info:
        recommendations_endpoint.read_semantic_recommendations(
            request=request,
            db=None,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == (
        "Recommendation index is inconsistent with the track database."
    )


def test_semantic_track_search_empty_index_raises_not_ready(db_session, monkeypatch):
    monkeypatch.setattr(
        semantic_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(count=0),
    )

    with pytest.raises(RecommendationIndexNotReadyError):
        semantic_recommendation_service.semantic_track_search(
            db=db_session,
            query="upbeat pop songs",
        )


def test_semantic_track_search_query_error_raises_dependency_unavailable(
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        semantic_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(query_error=RuntimeError("embedding failed")),
    )

    with pytest.raises(RecommendationDependencyUnavailableError):
        semantic_recommendation_service.semantic_track_search(
            db=db_session,
            query="upbeat pop songs",
        )


def test_semantic_track_search_no_results_returns_empty_list(db_session, monkeypatch):
    monkeypatch.setattr(
        semantic_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(
            count=10,
            query_result={
                "ids": [[]],
                "distances": [[]],
            },
        ),
    )

    results = semantic_recommendation_service.semantic_track_search(
        db=db_session,
        query="no matching songs",
    )

    assert results == []


def test_semantic_track_search_bad_chroma_id_raises_index_corrupt(
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        semantic_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(
            query_result={
                "ids": [["not-an-integer"]],
                "distances": [[0.1]],
            },
        ),
    )

    with pytest.raises(RecommendationIndexCorruptError):
        semantic_recommendation_service.semantic_track_search(
            db=db_session,
            query="upbeat pop songs",
        )


def test_semantic_track_search_bad_distance_raises_index_corrupt(
    db_session,
    monkeypatch,
    track_factory,
):
    track = track_factory()

    monkeypatch.setattr(
        semantic_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(
            query_result={
                "ids": [[str(track.id)]],
                "distances": [["not-a-distance"]],
            },
        ),
    )

    with pytest.raises(RecommendationIndexCorruptError):
        semantic_recommendation_service.semantic_track_search(
            db=db_session,
            query="upbeat pop songs",
        )


def test_semantic_track_search_missing_db_track_raises_index_corrupt(
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        semantic_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(
            query_result={
                "ids": [["999999"]],
                "distances": [[0.1]],
            },
        ),
    )

    with pytest.raises(RecommendationIndexCorruptError):
        semantic_recommendation_service.semantic_track_search(
            db=db_session,
            query="upbeat pop songs",
        )


def test_hybrid_get_chroma_candidates_query_error_raises_dependency_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        hybrid_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(query_error=RuntimeError("embedding failed")),
    )

    with pytest.raises(RecommendationDependencyUnavailableError):
        hybrid_recommendation_service.get_chroma_candidates(
            query="calm acoustic songs",
            candidate_pool_size=50,
        )


def test_hybrid_get_chroma_candidates_bad_distance_raises_index_corrupt(monkeypatch):
    monkeypatch.setattr(
        hybrid_recommendation_service,
        "get_track_collection",
        lambda: FakeCollection(
            query_result={
                "ids": [["1"]],
                "distances": [["not-a-distance"]],
            },
        ),
    )

    with pytest.raises(RecommendationIndexCorruptError):
        hybrid_recommendation_service.get_chroma_candidates(
            query="calm acoustic songs",
            candidate_pool_size=50,
        )


def test_hybrid_build_candidates_missing_db_tracks_raises_index_corrupt(db_session):
    with pytest.raises(RecommendationIndexCorruptError):
        hybrid_recommendation_service.build_candidates(
            db=db_session,
            track_ids=[999999],
            semantic_distances=[0.1],
        )
