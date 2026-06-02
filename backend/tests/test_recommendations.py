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