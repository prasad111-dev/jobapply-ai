import pytest

@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/auth/register", json={
        "email": "new@test.com",
        "username": "newuser",
        "password": "pass123",
        "full_name": "New User"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@test.com"
    assert data["user"]["username"] == "newuser"

@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/api/auth/register", json={
        "email": "dup@test.com", "username": "dupuser", "password": "pass123"
    })
    response = await client.post("/api/auth/register", json={
        "email": "dup@test.com", "username": "dupuser2", "password": "pass123"
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login(client, test_user):
    response = await client.post("/api/auth/login", data={
        "username": "testuser", "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    response = await client.post("/api/auth/login", data={
        "username": "testuser", "password": "wrongpass"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

@pytest.mark.asyncio
async def test_get_me_no_token(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 403
