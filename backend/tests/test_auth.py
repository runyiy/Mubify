def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email_or_username_returns_400(client):
    payload = {
        "email": "duplicate@example.com",
        "username": "duplicateuser",
        "password": "password123",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Email or username already registered"


def test_login_success(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_unknown_user_returns_401(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_get_current_user_requires_authentication(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_get_current_user_success(client, auth_headers):
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data