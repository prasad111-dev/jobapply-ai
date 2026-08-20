import pytest

@pytest.mark.asyncio
async def test_generate_cover_letter(client, auth_headers):
    response = await client.post("/api/ai/cover-letter", json={
        "job_title": "Software Engineer",
        "company": "Tech Corp",
        "job_description": "Build Python applications"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert "cover_letter" in response.json()
    assert len(response.json()["cover_letter"]) > 0

@pytest.mark.asyncio
async def test_match_score(client, auth_headers):
    response = await client.post("/api/ai/match-score", json={
        "skills_required": ["python", "fastapi"],
        "experience_required": 2
    }, headers=auth_headers)
    assert response.status_code == 200
    assert "match_score" in response.json()

@pytest.mark.asyncio
async def test_optimize_resume(client, auth_headers):
    response = await client.post("/api/ai/optimize-resume", params={
        "job_description": "Looking for Python developer with FastAPI experience"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert "relevant_skills" in response.json()
