from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio
from app.core.database import platform_connections, jobs, next_id, get_db
from app.routers.auth import get_current_user
from app.core.mongo_doc import Doc
from app.models.platform import to_doc
from app.models.job import to_doc as job_to_doc
from app.core.encryption import encrypt_secret, decrypt_secret

router = APIRouter()

class PlatformConnect(BaseModel):
    platform_name: str
    username: str
    password: Optional[str] = None
    auth_token: Optional[str] = None

class PlatformResponse(BaseModel):
    id: int
    platform_name: str
    is_connected: bool
    last_synced: Optional[str]
    username: Optional[str]
    has_credentials: bool = False
    class Config:
        from_attributes = True

class PlatformConfigResponse(BaseModel):
    name: str
    display_name: str
    url: str
    logo_url: Optional[str] = None
    auth_type: str
    difficulty_level: str
    is_active: bool
    class Config:
        from_attributes = True

class ScrapeRequest(BaseModel):
    query: str = "python developer"
    location: str = ""
    max_results: int = 20

SUPPORTED_PLATFORMS = [
    {"name": "indeed", "display_name": "Indeed", "url": "https://indeed.com", "difficulty_level": "medium", "auth_type": "credentials"},
    {"name": "linkedin", "display_name": "LinkedIn", "url": "https://linkedin.com", "difficulty_level": "hard", "auth_type": "oauth"},
    {"name": "naukri", "display_name": "Naukri.com", "url": "https://naukri.com", "difficulty_level": "medium", "auth_type": "credentials"},
    {"name": "unstop", "display_name": "Unstop", "url": "https://unstop.com", "difficulty_level": "medium", "auth_type": "credentials"},
    {"name": "foundit", "display_name": "Foundit (Monster)", "url": "https://foundit.com", "difficulty_level": "medium", "auth_type": "credentials"},
    {"name": "internshala", "display_name": "Internshala", "url": "https://internshala.com", "difficulty_level": "easy", "auth_type": "credentials"},
    {"name": "cutshort", "display_name": "CutShort", "url": "https://cutshort.io", "difficulty_level": "easy", "auth_type": "credentials"},
    {"name": "shine", "display_name": "Shine.com", "url": "https://shine.com", "difficulty_level": "medium", "auth_type": "credentials"},
    {"name": "timesjobs", "display_name": "TimesJobs", "url": "https://timesjobs.com", "difficulty_level": "medium", "auth_type": "credentials"},
    {"name": "hirist", "display_name": "Hirist", "url": "https://hirist.tech", "difficulty_level": "easy", "auth_type": "credentials"},
    {"name": "wellfound", "display_name": "Wellfound (AngelList)", "url": "https://wellfound.com", "difficulty_level": "medium", "auth_type": "credentials"},
    {"name": "remoteok", "display_name": "RemoteOK", "url": "https://remoteok.com", "difficulty_level": "easy", "auth_type": "api"},
    {"name": "freelancer", "display_name": "Freelancer.com", "url": "https://freelancer.com", "difficulty_level": "easy", "auth_type": "api"},
    {"name": "glassdoor", "display_name": "Glassdoor", "url": "https://glassdoor.com", "difficulty_level": "hard", "auth_type": "credentials"},
]

@router.get("/", response_model=List[PlatformConfigResponse])
async def get_platforms():
    return [PlatformConfigResponse(**p, is_active=True) for p in SUPPORTED_PLATFORMS]

class TestConnectionRequest(BaseModel):
    username: str
    password: str
    verify: bool = True


@router.post("/{platform_name}/test-connection")
async def test_connection(platform_name: str, data: TestConnectionRequest, current_user: Doc = Depends(get_current_user)):
    """Actually log into the platform with the given credentials to verify they work.

    On success, saves the session so auto-apply works without re-entering the password.
    If browser verification is unavailable, saves credentials anyway (unverified).
    """
    from app.services.browser_automation import browser_automation, PLAYWRIGHT_AVAILABLE

    if not PLAYWRIGHT_AVAILABLE:
        # Save credentials without verification
        existing_conn = await platform_connections.find_one({"user_id": current_user.id, "platform_name": platform_name})
        if existing_conn:
            await platform_connections.update_one({"_id": existing_conn["_id"]}, {"$set": {"username": data.username, "auth_token": encrypt_secret(data.password), "is_connected": True, "last_synced": datetime.utcnow()}})
        else:
            conn_id = await next_id("platform_connections")
            conn_doc = to_doc({"_id": conn_id, "id": conn_id, "user_id": current_user.id, "platform_name": platform_name, "username": data.username, "auth_token": encrypt_secret(data.password), "is_connected": True, "last_synced": datetime.utcnow()})
            await platform_connections.insert_one(conn_doc)
        return {"success": True, "message": "Playwright not available — credentials saved without verification.", "verified": False, "session_saved": False}

    try:
        result = await asyncio.wait_for(
            browser_automation.test_platform_connection(
                platform_name, data.username, data.password, user_id=current_user.id
            ),
            timeout=45,
        )
        if result.get("success"):
            return {
                "success": True,
                "verified": True,
                "session_saved": result.get("session_saved", False),
                "message": result.get("message", ""),
            }
        else:
            # Verification failed but still save credentials so the user isn't stuck
            existing_conn = await platform_connections.find_one({"user_id": current_user.id, "platform_name": platform_name})
            if existing_conn:
                await platform_connections.update_one({"_id": existing_conn["_id"]}, {"$set": {"username": data.username, "auth_token": encrypt_secret(data.password), "is_connected": True, "last_synced": datetime.utcnow()}})
            else:
                conn_id = await next_id("platform_connections")
                conn_doc = to_doc({"_id": conn_id, "id": conn_id, "user_id": current_user.id, "platform_name": platform_name, "username": data.username, "auth_token": encrypt_secret(data.password), "is_connected": True, "last_synced": datetime.utcnow()})
                await platform_connections.insert_one(conn_doc)
            return {
                "success": True,
                "verified": False,
                "session_saved": False,
                "message": f"Credentials saved. Login verification failed: {result.get('message', 'Unknown error')}. You can still try auto-apply — it may work if your session is valid.",
            }
    except Exception as e:
        # Browser launch timed out or crashed — save credentials anyway
        existing_conn = await platform_connections.find_one({"user_id": current_user.id, "platform_name": platform_name})
        if existing_conn:
            await platform_connections.update_one({"_id": existing_conn["_id"]}, {"$set": {"username": data.username, "auth_token": encrypt_secret(data.password), "is_connected": True, "last_synced": datetime.utcnow()}})
        else:
            conn_id = await next_id("platform_connections")
            conn_doc = to_doc({"_id": conn_id, "id": conn_id, "user_id": current_user.id, "platform_name": platform_name, "username": data.username, "auth_token": encrypt_secret(data.password), "is_connected": True, "last_synced": datetime.utcnow()})
            await platform_connections.insert_one(conn_doc)
        return {"success": True, "verified": False, "session_saved": False, "message": f"Credentials saved. Browser verification unavailable on this server: {str(e)[:120]}"}


@router.post("/connect")
async def connect_platform(data: PlatformConnect, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    existing_conn = await platform_connections.find_one({
        "user_id": current_user.id,
        "platform_name": data.platform_name
    })

    if existing_conn:
        update = {"username": data.username, "is_connected": True, "last_synced": datetime.utcnow()}
        if data.password:
            update["auth_token"] = encrypt_secret(data.password)
        if data.auth_token:
            update["refresh_token"] = encrypt_secret(data.auth_token)
        await platform_connections.update_one({"_id": existing_conn["_id"]}, {"$set": update})
    else:
        conn_id = await next_id("platform_connections")
        conn_doc = to_doc({
            "_id": conn_id,
            "id": conn_id,
            "user_id": current_user.id,
            "platform_name": data.platform_name,
            "username": data.username,
            "auth_token": encrypt_secret(data.password),
            "refresh_token": encrypt_secret(data.auth_token),
            "is_connected": True,
            "last_synced": datetime.utcnow(),
        })
        await platform_connections.insert_one(conn_doc)

    if data.password:
        note = " Credentials stored. Will be used for auto-apply."
    elif data.auth_token:
        note = " OAuth token stored."
    else:
        note = " Connected without credentials. Add password to enable auto-apply."

    return {
        "message": f"Connected to {data.platform_name} successfully{note}",
        "platform": data.platform_name,
        "has_credentials": bool(data.password or data.auth_token)
    }

@router.get("/connected", response_model=List[PlatformResponse])
async def get_connected_platforms(current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    cursor = platform_connections.find({"user_id": current_user.id})
    connections = [doc async for doc in cursor]
    return [PlatformResponse(
        id=c["id"], platform_name=c["platform_name"], is_connected=c.get("is_connected", False),
        last_synced=str(c.get("last_synced")) if c.get("last_synced") else None, username=c.get("username"),
        has_credentials=bool(c.get("auth_token") or c.get("refresh_token"))
    ) for c in connections]

@router.delete("/{platform_name}")
async def disconnect_platform(platform_name: str, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    result = await platform_connections.delete_one({
        "user_id": current_user.id,
        "platform_name": platform_name
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Platform connection not found")
    return {"message": f"Disconnected from {platform_name}"}

class DigestPreferences(BaseModel):
    digest_enabled: bool = False
    search_queries: Optional[List[str]] = None
    search_query: Optional[str] = None


class DigestResponse(BaseModel):
    digest_enabled: bool
    search_queries: List[str]
    email_configured: bool


@router.put("/preferences/digest", response_model=DigestResponse)
async def set_digest_preferences(data: DigestPreferences, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    from app.core.database import users
    prefs = dict(current_user.get("preferences") or {})
    prefs["digest_enabled"] = data.digest_enabled
    if data.search_queries:
        prefs["search_queries"] = data.search_queries
    if data.search_query:
        prefs["search_query"] = data.search_query
        qs = prefs.get("search_queries") or []
        if data.search_query not in qs:
            qs.append(data.search_query)
            prefs["search_queries"] = qs
    await users.update_one({"_id": current_user.id}, {"$set": {"preferences": prefs, "updated_at": datetime.utcnow()}})

    from app.services.email_service import is_email_configured
    return DigestResponse(
        digest_enabled=prefs.get("digest_enabled", False),
        search_queries=prefs.get("search_queries") or [prefs.get("search_query", "python developer")],
        email_configured=is_email_configured(),
    )


@router.get("/preferences/digest", response_model=DigestResponse)
async def get_digest_preferences(current_user: Doc = Depends(get_current_user)):
    prefs = current_user.get("preferences") or {}
    from app.services.email_service import is_email_configured
    return DigestResponse(
        digest_enabled=prefs.get("digest_enabled", False),
        search_queries=prefs.get("search_queries") or [prefs.get("search_query", "python developer")],
        email_configured=is_email_configured(),
    )


@router.post("/digest/run")
async def run_digest_now(current_user: Doc = Depends(get_current_user)):
    """Manually trigger the job digest for the current user."""
    from app.services.scheduler import run_digest_for_user
    from app.services.email_service import is_email_configured

    if not is_email_configured():
        return {"message": "Digest ran, but email sending is not configured. Add SMTP settings to send emails.", "new_jobs": 0}
    result = await run_digest_for_user(current_user)
    return {"message": f"Digest complete: {result.get('new_jobs', 0)} new matching jobs found", "new_jobs": result.get("new_jobs", 0), "status": result.get("status")}


@router.post("/scrape")
async def scrape_jobs_from_platform(
    request: ScrapeRequest,
    platform_name: str = "indeed",
    current_user: Doc = Depends(get_current_user),
    db=Depends(get_db)
):
    """Scrape REAL jobs. Never generates sample/fake data.

    Uses live public APIs and direct HTTP scrapers (RemoteOK, Remotive,
    Naukri). Platforms without a real scraper return an empty result.
    """
    from app.services.real_scraper import scrape_real, scrape_all_real

    platform = platform_name.lower()

    try:
        if platform == "all":
            scraped = await scrape_all_real(request.query, request.max_results)
        else:
            scraped = await scrape_real(platform, request.query, request.max_results)
    except Exception as e:
        return {"message": f"Real scraping failed: {str(e)[:150]}", "jobs_found": 0, "jobs": [], "error": str(e)[:300]}

    saved = []
    seen_urls = set()
    for job_data in scraped:
        job_url = job_data.get("platform_url", "")
        if not job_url or job_url in seen_urls:
            continue
        seen_urls.add(job_url)
        existing = await jobs.find_one({"platform_url": job_url})
        if existing:
            continue
        job_id = await next_id("jobs")
        doc = job_to_doc(job_data)
        doc["_id"] = job_id
        doc["id"] = job_id
        await jobs.insert_one(doc)
        saved.append(doc)

    return {
        "message": f"Scraped {len(saved)} new real jobs from {platform if platform != 'all' else 'Naukri + Internshala + RemoteOK + Remotive'}",
        "jobs_found": len(saved),
        "total_found": len(scraped),
        "jobs": [{"id": j["id"], "title": j.get("title"), "company": j.get("company"), "platform_source": j.get("platform_source"), "platform_url": j.get("platform_url")} for j in saved]
    }