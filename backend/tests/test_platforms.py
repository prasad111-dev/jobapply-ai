import pytest

@pytest.mark.asyncio
async def test_get_platforms(client):
    response = await client.get("/api/platforms/")
    assert response.status_code == 200
    platforms = response.json()
    assert len(platforms) > 0
    assert any(p["name"] == "indeed" for p in platforms)

@pytest.mark.asyncio
async def test_connect_platform(client, auth_headers):
    response = await client.post("/api/platforms/connect", json={
        "platform_name": "indeed",
        "username": "test@email.com",
        "password": "testpass"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["platform"] == "indeed"

@pytest.mark.asyncio
async def test_get_connected_platforms(client, auth_headers):
    await client.post("/api/platforms/connect", json={
        "platform_name": "linkedin", "username": "test"
    }, headers=auth_headers)
    response = await client.get("/api/platforms/connected", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_disconnect_platform(client, auth_headers):
    await client.post("/api/platforms/connect", json={
        "platform_name": "naukri", "username": "test"
    }, headers=auth_headers)
    response = await client.delete("/api/platforms/naukri", headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_disconnect_nonexistent(client, auth_headers):
    response = await client.delete("/api/platforms/nonexistent", headers=auth_headers)
    assert response.status_code == 404
