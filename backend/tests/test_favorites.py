def test_get_favorites_requires_authentication(client):
    response = client.get("/api/v1/favorites")

    assert response.status_code == 401


def test_get_favorites_empty(client, auth_headers):
    response = client.get(
        "/api/v1/favorites",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_add_favorite_requires_authentication(client, track_factory):
    track = track_factory()

    response = client.post(f"/api/v1/favorites/{track.id}")

    assert response.status_code == 401


def test_add_favorite_success(client, auth_headers, track_factory):
    track = track_factory(track_name="Favorite Song")

    response = client.post(
        f"/api/v1/favorites/{track.id}",
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["track_id"] == track.id
    assert data["track"]["id"] == track.id
    assert data["track"]["track_name"] == "Favorite Song"


def test_add_favorite_nonexistent_track_returns_404(client, auth_headers):
    response = client.post(
        "/api/v1/favorites/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found"


def test_add_duplicate_favorite_returns_400(client, auth_headers, track_factory):
    track = track_factory()

    first_response = client.post(
        f"/api/v1/favorites/{track.id}",
        headers=auth_headers,
    )
    second_response = client.post(
        f"/api/v1/favorites/{track.id}",
        headers=auth_headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Track already favorited"


def test_get_favorites_returns_user_favorites(client, auth_headers, track_factory):
    track_1 = track_factory(track_name="Favorite Song 1")
    track_2 = track_factory(track_name="Favorite Song 2")

    client.post(f"/api/v1/favorites/{track_1.id}", headers=auth_headers)
    client.post(f"/api/v1/favorites/{track_2.id}", headers=auth_headers)

    response = client.get(
        "/api/v1/favorites",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    track_names = {favorite["track"]["track_name"] for favorite in data}

    assert "Favorite Song 1" in track_names
    assert "Favorite Song 2" in track_names


def test_delete_favorite_requires_authentication(client, track_factory):
    track = track_factory()

    response = client.delete(f"/api/v1/favorites/{track.id}")

    assert response.status_code == 401


def test_delete_favorite_success(client, auth_headers, track_factory):
    track = track_factory()

    add_response = client.post(
        f"/api/v1/favorites/{track.id}",
        headers=auth_headers,
    )

    assert add_response.status_code == 201

    delete_response = client.delete(
        f"/api/v1/favorites/{track.id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Favorite removed successfully"

    get_response = client.get(
        "/api/v1/favorites",
        headers=auth_headers,
    )

    assert get_response.status_code == 200
    assert get_response.json() == []


def test_delete_nonexistent_favorite_returns_404(client, auth_headers, track_factory):
    track = track_factory()

    response = client.delete(
        f"/api/v1/favorites/{track.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Favorite not found"