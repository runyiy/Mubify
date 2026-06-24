def test_get_tracks_empty_returns_empty_list(client):
    response = client.get("/api/v1/tracks")

    assert response.status_code == 200
    assert response.json() == []


def test_get_tracks_returns_tracks_ordered_by_popularity(client, track_factory):
    low_popularity = track_factory(
        track_name="Low Popularity Song",
        popularity=10,
    )
    high_popularity = track_factory(
        track_name="High Popularity Song",
        popularity=90,
    )

    response = client.get("/api/v1/tracks?limit=10")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == high_popularity.id
    assert data[1]["id"] == low_popularity.id


def test_get_tracks_with_limit(client, track_factory):
    track_factory(track_name="Song 1")
    track_factory(track_name="Song 2")
    track_factory(track_name="Song 3")

    response = client.get("/api/v1/tracks?limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_tracks_with_skip(client, track_factory):
    track_factory(track_name="Song 1", popularity=90)
    track_factory(track_name="Song 2", popularity=80)
    track_factory(track_name="Song 3", popularity=70)

    response = client.get("/api/v1/tracks?skip=1&limit=10")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["track_name"] == "Song 2"


def test_get_tracks_filter_by_genre(client, track_factory):
    track_factory(track_name="Pop Song", track_genre="pop")
    track_factory(track_name="Rock Song", track_genre="rock")

    response = client.get("/api/v1/tracks?genre=pop")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["track_name"] == "Pop Song"
    assert data[0]["track_genre"] == "pop"


def test_get_tracks_search_by_track_name(client, track_factory):
    track_factory(track_name="Love Story")
    track_factory(track_name="Random Song")

    response = client.get("/api/v1/tracks?search=love")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["track_name"] == "Love Story"


def test_get_tracks_search_by_artist(client, track_factory):
    track_factory(track_name="Song A", artists="Taylor Swift")
    track_factory(track_name="Song B", artists="Another Artist")

    response = client.get("/api/v1/tracks?search=taylor")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["artists"] == "Taylor Swift"


def test_get_tracks_search_by_album_name(client, track_factory):
    track_factory(track_name="Song A", album_name="Midnights")
    track_factory(track_name="Song B", album_name="Other Album")

    response = client.get("/api/v1/tracks?search=midnights")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["album_name"] == "Midnights"


def test_get_paginated_tracks_returns_metadata(client, track_factory):
    track_factory(track_name="Song 1", popularity=90)
    track_factory(track_name="Song 2", popularity=80)
    track_factory(track_name="Song 3", popularity=70)

    response = client.get("/api/v1/tracks/paginated?skip=1&limit=1")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert set(data) == {"items", "total", "skip", "limit", "has_next"}
    assert len(data["items"]) == 1
    assert data["items"][0]["track_name"] == "Song 2"
    assert data["total"] == 3
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert data["has_next"] is True


def test_get_paginated_tracks_total_uses_search_and_genre_filters(
    client,
    track_factory,
):
    track_factory(
        track_name="Pop Love Song",
        track_genre="pop",
        popularity=90,
    )
    track_factory(
        track_name="Pop Dance Song",
        track_genre="pop",
        popularity=80,
    )
    track_factory(
        track_name="Rock Love Song",
        track_genre="rock",
        popularity=70,
    )

    response = client.get(
        "/api/v1/tracks/paginated?genre=pop&search=love&limit=1"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["track_name"] == "Pop Love Song"
    assert data["total"] == 1
    assert data["has_next"] is False


def test_get_track_by_database_id_success(client, track_factory):
    track = track_factory(track_name="Single Track")

    response = client.get(f"/api/v1/tracks/{track.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == track.id
    assert data["track_name"] == "Single Track"


def test_get_track_by_database_id_not_found(client):
    response = client.get("/api/v1/tracks/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found"


def test_get_track_by_spotify_id_success(client, track_factory):
    track = track_factory(
        track_id="spotify-special-id",
        track_name="Spotify ID Song",
    )

    response = client.get("/api/v1/tracks/spotify/spotify-special-id")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == track.id
    assert data["track_id"] == "spotify-special-id"


def test_get_track_by_spotify_id_not_found(client):
    response = client.get("/api/v1/tracks/spotify/not-found-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found"


def test_get_tracks_invalid_limit_returns_422(client):
    response = client.get("/api/v1/tracks?limit=0")

    assert response.status_code == 422


def test_get_tracks_limit_too_large_returns_422(client):
    response = client.get("/api/v1/tracks?limit=101")

    assert response.status_code == 422
