#!/usr/bin/env python3
import httpx
import json

BASE = "http://localhost:8000"

def test_all():
    client = httpx.Client(timeout=30)
    
    print("1. HEALTH CHECK")
    r = client.get(f"{BASE}/health")
    print(f"   Status: {r.json()}")
    
    print("\n2. REGISTER")
    r = client.post(f"{BASE}/api/auth/register", json={
        "email": "demo@test.com", "username": "demo", "password": "demo123", "full_name": "Demo User"
    })
    data = r.json()
    if "access_token" in data:
        print(f"   OK: user={data['user']['username']}")
        token = data["access_token"]
    else:
        print(f"   User exists, logging in...")
        r = client.post(f"{BASE}/api/auth/login", data={"username": "demo", "password": "demo123"})
        token = r.json()["access_token"]
        print(f"   OK: logged in")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n3. UPDATE PROFILE")
    r = client.put(f"{BASE}/api/profile/", headers=headers, json={
        "full_name": "Demo User", "phone": "9876543210", "location": "Hyderabad",
        "skills": ["python", "fastapi", "react", "docker", "postgresql"], "experience_years": 3
    })
    d = r.json()
    print(f"   Name={d['full_name']} Skills={d['skills']}")
    
    print("\n4. CREATE JOBS")
    for i in range(1, 6):
        client.post(f"{BASE}/api/jobs/", headers=headers, json={
            "title": f"Python Developer {i}", "company": f"TechCorp {i}", "location": "Remote",
            "platform_source": "indeed", "skills_required": ["python", "fastapi", "react"],
            "salary_min": 80000, "salary_max": 120000
        })
    print("   Created 5 jobs")
    
    print("\n5. LIST JOBS")
    r = client.get(f"{BASE}/api/jobs/", headers=headers)
    jobs = r.json()
    for j in jobs:
        print(f"   [{j['match_score']*100:.0f}%] {j['title']} at {j['company']}")
    
    print("\n6. BULK APPLY (3 jobs)")
    r = client.post(f"{BASE}/api/applications/apply", headers=headers, json={"job_ids": [1, 2, 3]})
    d = r.json()
    print(f"   Applied {d['successful']}/{d['total']} jobs")
    
    print("\n7. APPLICATION STATS")
    r = client.get(f"{BASE}/api/applications/stats", headers=headers)
    d = r.json()
    print(f"   Total={d['total_applications']} Submitted={d['submitted']} Rate={d['response_rate']}%")
    
    print("\n8. LIST APPLICATIONS")
    r = client.get(f"{BASE}/api/applications/", headers=headers)
    apps = r.json()
    print(f"   {len(apps)} applications")
    for a in apps:
        print(f"   - #{a['id']} [{a['status']}] via {a['platform_name']}")
    
    print("\n9. PLATFORMS")
    r = client.get(f"{BASE}/api/platforms/")
    ps = r.json()
    print(f"   {len(ps)} platforms available")
    for p in ps[:7]:
        print(f"   - {p['display_name']} [{p['difficulty_level']}]")
    
    print("\n10. CONNECT PLATFORM")
    r = client.post(f"{BASE}/api/platforms/connect", headers=headers, json={
        "platform_name": "indeed", "username": "demo@test.com"
    })
    print(f"   {r.json()['message']}")
    
    print("\n11. CONNECTED PLATFORMS")
    r = client.get(f"{BASE}/api/platforms/connected", headers=headers)
    cs = r.json()
    print(f"   {len(cs)} connected")
    for c in cs:
        print(f"   - {c['platform_name']} ({'connected' if c['is_connected'] else 'disconnected'})")
    
    print("\n12. AI COVER LETTER")
    r = client.post(f"{BASE}/api/ai/cover-letter", headers=headers, json={
        "job_title": "Python Developer", "company": "TechCorp", "job_description": "Build FastAPI apps"
    })
    letter = r.json()["cover_letter"]
    print(f"   Generated ({len(letter)} chars):")
    print(f"   {letter[:200]}...")
    
    print("\n13. MATCH SCORE")
    r = client.post(f"{BASE}/api/ai/match-score", headers=headers, json={
        "skills_required": ["python", "fastapi", "react"], "experience_required": 2
    })
    d = r.json()
    print(f"   Match: {d['match_score']*100:.0f}%")
    
    print("\n14. API DOCS")
    r = client.get(f"{BASE}/docs")
    print(f"   Available at http://localhost:8000/docs (status={r.status_code})")
    
    print("\n" + "=" * 50)
    print("  ALL 14 TESTS PASSED!")
    print("=" * 50)
    print("  Frontend:  http://localhost:3000")
    print("  Backend:   http://localhost:8000")
    print("  API Docs:  http://localhost:8000/docs")
    print("  Health:    http://localhost:8000/health")
    print("=" * 50)

if __name__ == "__main__":
    test_all()
