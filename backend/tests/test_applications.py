import pytest

@pytest.mark.asyncio
async def test_bulk_apply(client, auth_headers):
    job1 = (await client.post("/api/jobs/", json={
        "title": "Dev 1", "company": "Co1", "platform_source": "indeed"
    }, headers=auth_headers)).json()
    job2 = (await client.post("/api/jobs/", json={
        "title": "Dev 2", "company": "Co2", "platform_source": "naukri"
    }, headers=auth_headers)).json()

    response = await client.post("/api/applications/apply", json={
        "job_ids": [job1["id"], job2["id"]]
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["successful"] == 2

@pytest.mark.asyncio
async def test_get_applications(client, auth_headers):
    response = await client.get("/api/applications/", headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_application_stats(client, auth_headers):
    response = await client.get("/api/applications/stats", headers=auth_headers)
    assert response.status_code == 200
    assert "total_applications" in response.json()
