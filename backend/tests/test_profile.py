import pytest

@pytest.mark.asyncio
async def test_get_profile(client, auth_headers):
    response = await client.get("/api/profile/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    response = await client.put("/api/profile/", json={
        "full_name": "Updated Name",
        "phone": "1234567890",
        "location": "New York",
        "skills": ["python", "fastapi"]
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["phone"] == "1234567890"
    assert "python" in data["skills"]

@pytest.mark.asyncio
async def test_get_profile_unauthorized(client):
    response = await client.get("/api/profile/")
    assert response.status_code == 403
