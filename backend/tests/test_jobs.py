import pytest

@pytest.mark.asyncio
async def test_create_job(client, auth_headers):
    response = await client.post("/api/jobs/", json={
        "title": "Software Engineer",
        "company": "Tech Corp",
        "location": "Remote",
        "description": "Build amazing things",
        "skills_required": ["python", "fastapi"],
        "platform_source": "manual"
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Software Engineer"
    assert data["company"] == "Tech Corp"

@pytest.mark.asyncio
async def test_get_jobs(client, auth_headers):
    await client.post("/api/jobs/", json={
        "title": "Frontend Dev", "company": "Web Inc", "platform_source": "manual"
    }, headers=auth_headers)
    response = await client.get("/api/jobs/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_search_jobs(client, auth_headers):
    await client.post("/api/jobs/", json={
        "title": "Python Developer", "company": "Code Co", "platform_source": "manual"
    }, headers=auth_headers)
    response = await client.get("/api/jobs/?search=Python", headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_job_not_found(client, auth_headers):
    response = await client.get("/api/jobs/99999", headers=auth_headers)
    assert response.status_code == 404
