from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import asyncio
from app.core.database import jobs, applications, platform_connections, next_id, get_db
from app.routers.auth import get_current_user
from app.core.mongo_doc import Doc
from app.core.encryption import decrypt_secret
from app.services.ai_engine import ai_engine
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()
logger = logging.getLogger(__name__)

class ApplyRequest(BaseModel):
    job_ids: List[int]
    custom_cover_letter: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    platform_name: str
    platform_url: Optional[str] = None
    status: str
    cover_letter: Optional[str] = None
    form_data: Optional[dict] = None
    submitted_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class BulkApplyResponse(BaseModel):
    total: int
    successful: int
    failed: int
    pending: int
    applications: List[ApplicationResponse]


async def _bg_apply(application_id: int, platform: str, job_url: str, username: str, password: str, user_profile: dict, resume_path: str, cover_letter: str, auto_answers: dict = None, user_id: int = None):
    """Background task: opens Chrome, logs in (or reuses session), fills form, submits."""
    try:
        from app.services.browser_automation import browser_automation
        result = await asyncio.wait_for(
            browser_automation.apply_to_job_realtime(
                platform=platform, job_url=job_url,
                username=username, password=password,
                user_profile=user_profile, resume_path=resume_path,
                cover_letter=cover_letter, auto_answers=auto_answers,
                user_id=user_id,
            ),
            timeout=settings.BROWSER_TIMEOUT_SECONDS,
        )
        login_ok = result.get("login_success", False)
        apply_data = result.get("apply_result", {}) or {}
        error = result.get("error")
        filled = []

        if login_ok and apply_data:
            apply_status = apply_data.get("status", "failed")
            filled = apply_data.get("filled_fields", []) or []
            if apply_status == "submitted":
                new_status = "submitted"
                note = "Applied via browser automation! Filled: " + ", ".join(str(f) for f in filled)
            elif apply_status == "form_filled":
                new_status = "pending"
                note = f"Form auto-filled ({', '.join(str(f) for f in filled)}). Submit button not found. Please submit manually at {job_url}"
            else:
                new_status = "failed"
                note = f"Apply failed: {apply_data.get('error', 'Unknown error')}"
        else:
            new_status = "pending"
            note = f"Login failed: {error}. Please apply manually at {job_url}"

        app_doc = await applications.find_one({"_id": application_id})
        if app_doc:
            update = {
                "status": new_status,
                "updated_at": datetime.utcnow(),
            }
            fd = dict(app_doc.get("form_data") or {})
            fd["note"] = note
            fd["automation_result"] = {"login": login_ok, "filled": filled}
            update["form_data"] = fd
            if new_status == "submitted":
                update["submitted_at"] = datetime.utcnow()
            await applications.update_one({"_id": application_id}, {"$set": update})
        logger.info(f"BG apply #{application_id}: {new_status}")

    except asyncio.TimeoutError:
        logger.error(f"BG apply #{application_id} timed out after {settings.BROWSER_TIMEOUT_SECONDS}s")
        try:
            app_doc = await applications.find_one({"_id": application_id})
            if app_doc:
                fd = dict(app_doc.get("form_data") or {})
                fd["note"] = f"Browser automation timed out after {settings.BROWSER_TIMEOUT_SECONDS}s. Please apply manually at {job_url}"
                await applications.update_one({"_id": application_id}, {"$set": {
                    "status": "pending", "form_data": fd, "updated_at": datetime.utcnow()
                }})
        except:
            pass
    except Exception as e:
        logger.error(f"BG apply #{application_id} error: {e}")
        try:
            app_doc = await applications.find_one({"_id": application_id})
            if app_doc:
                fd = dict(app_doc.get("form_data") or {})
                fd["note"] = f"Error: {str(e)[:200]}"
                await applications.update_one({"_id": application_id}, {"$set": {
                    "status": "failed", "form_data": fd, "updated_at": datetime.utcnow()
                }})
        except:
            pass


async def _apply_to_single_job(job_id: int, user: Doc, db, custom_cover_letter: Optional[str] = None):
    job = await jobs.find_one({"_id": job_id})
    if not job:
        return None, "Job not found"

    user_profile = {
        "full_name": user.get("full_name") or user.get("username"),
        "email": user.get("email"),
        "phone": user.get("phone") or "",
        "skills": user.get("skills") or [],
        "experience_years": user.get("experience_years") or 0,
        "education": user.get("education") or [],
        "linkedin_url": user.get("linkedin_url") or "",
        "portfolio_url": user.get("portfolio_url") or "",
        "location": user.get("location") or "",
        "expected_salary": (user.get("preferences") or {}).get("expected_salary", ""),
        "current_salary": (user.get("preferences") or {}).get("current_salary", ""),
        "notice_period": (user.get("preferences") or {}).get("notice_period", ""),
        "work_authorization": (user.get("preferences") or {}).get("work_authorization", ""),
        "availability": (user.get("preferences") or {}).get("availability", ""),
        "preferred_location": (user.get("preferences") or {}).get("preferred_location", user.get("location") or ""),
        "willing_to_relocate": (user.get("preferences") or {}).get("willing_to_relocate", True),
        "current_company": (user.get("preferences") or {}).get("current_company", ""),
        "current_title": (user.get("preferences") or {}).get("current_title", ""),
        "resume_link": (user.get("preferences") or {}).get("resume_link", ""),
    }

    cover_letter = custom_cover_letter
    if not cover_letter:
        cover_letter = await ai_engine.generate_cover_letter(
            job["title"], job["company"], job.get("description") or "", user_profile
        )

    auto_answers = await ai_engine.generate_auto_answers(
        {"title": job["title"], "company": job["company"], "description": job.get("description") or ""},
        user_profile,
    )

    platform_url = job.get("platform_url") or ""
    form_data = {}
    status = "processing"

    app_id = await next_id("applications")
    app_doc = {
        "_id": app_id,
        "id": app_id,
        "user_id": user.id,
        "job_id": job_id,
        "platform_name": job.get("platform_source"),
        "status": status,
        "cover_letter": cover_letter,
        "form_data": {
            "note": "Processing... Browser automation is running.",
            "platform_url": platform_url,
            "user_profile": user_profile,
            "auto_answers": auto_answers,
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await applications.insert_one(app_doc)

    app_record = Doc(app_doc)

    return {
        "record": app_record,
        "needs_browser": bool(platform_url and "http" in platform_url),
        "platform": job.get("platform_source"),
        "job_url": platform_url,
        "user_profile": user_profile,
        "resume_path": user.get("resume_file_path"),
        "cover_letter": cover_letter,
        "auto_answers": auto_answers,
    }, None


def _create_app(user_id, job, status, cover_letter, form_data):
    return {
        "user_id": user_id, "job_id": job["id"], "platform_name": job["platform_source"],
        "status": status, "cover_letter": cover_letter, "form_data": form_data,
        "submitted_at": datetime.utcnow() if status == "submitted" else None,
    }


async def _get_creds(user_id, platform_name, db):
    conn = await platform_connections.find_one({
        "user_id": user_id,
        "platform_name": platform_name,
        "is_connected": True,
    })
    return conn


def _has_session(user_id: int, platform: str) -> bool:
    """Check if a saved browser session exists for this user+platform."""
    try:
        from app.services.session_storage import load_session_cookies
        return bool(load_session_cookies(user_id, platform))
    except Exception:
        return False


async def _schedule_apply(background_tasks: BackgroundTasks, result: dict, user_id: int, db):
    """Schedule the background apply if credentials OR a saved session exist.

    Returns True if the automation was scheduled, False otherwise.
    """
    platform = result["platform"]
    creds = await _get_creds(user_id, platform, db)

    password = None
    username = None
    if creds and creds.get("auth_token"):
        password = decrypt_secret(creds["auth_token"]) or creds["auth_token"]
        username = creds.get("username")

    has_creds = bool(username and password)
    has_session = _has_session(user_id, platform)

    if has_creds or has_session:
        background_tasks.add_task(
            _bg_apply, result["record"].id,
            platform, result["job_url"],
            username or "", password or "",
            result["user_profile"], result["resume_path"], result["cover_letter"],
            result["auto_answers"], user_id,
        )
        return True
    else:
        await applications.update_one({"_id": result["record"].id}, {"$set": {
            "status": "pending",
            "form_data": {
                **dict(result["record"].get("form_data") or {}),
                "note": f"No credentials or saved session for {platform}. Connect the platform to enable auto-apply.",
            },
            "updated_at": datetime.utcnow(),
        }})
        return False


def _enrich(app_doc: dict, job_doc: dict):
    ar = ApplicationResponse.model_validate(app_doc)
    if job_doc:
        ar.job_title = job_doc.get("title")
        ar.job_company = job_doc.get("company")
        ar.platform_url = job_doc.get("platform_url")
    return ar


@router.post("/apply", response_model=BulkApplyResponse)
async def apply_to_jobs(request: ApplyRequest, background_tasks: BackgroundTasks, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    applications_done = []
    successful = 0
    failed = 0
    pending = 0

    # Pre-flight check: profile + connections must be ready for real auto-apply
    from app.routers.profile import _completeness
    comp = _completeness(current_user)
    cursor = platform_connections.find({
        "user_id": current_user.id,
        "is_connected": True,
    })
    conns = [doc async for doc in cursor]
    conn_platforms = {c.get("platform_name"): bool(c.get("auth_token") or c.get("refresh_token")) for c in conns}

    for job_id in request.job_ids:
        try:
            result, error = await _apply_to_single_job(job_id, current_user, db, request.custom_cover_letter)
            if result:
                applications_done.append(result)
                platform = result["platform"]
                has_creds_for_platform = conn_platforms.get(platform, False)
                needs_browser = result["needs_browser"]

                if needs_browser and not has_creds_for_platform:
                    await applications.update_one({"_id": result["record"].id}, {"$set": {
                        "status": "pending",
                        "form_data": {
                            **dict(result["record"].get("form_data") or {}),
                            "note": (f"No {platform} credentials connected. Connect your {platform} account "
                                     "on the Platforms tab to enable one-click auto-apply."),
                        },
                        "updated_at": datetime.utcnow(),
                    }})
                    pending += 1
                    continue

                if needs_browser:
                    scheduled = await _schedule_apply(background_tasks, result, current_user.id, db)
                    if scheduled:
                        successful += 1
                    else:
                        pending += 1
                else:
                    successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Bulk apply error for job {job_id}: {e}")
            failed += 1

    result_apps = []
    for r in applications_done:
        app_doc = await applications.find_one({"_id": r["record"].id})
        job_doc = await jobs.find_one({"_id": r["record"].get("job_id")})
        result_apps.append(_enrich(app_doc or {}, job_doc))

    return BulkApplyResponse(total=len(request.job_ids), successful=successful, failed=failed, pending=pending, applications=result_apps)


class ApplyMatchingRequest(BaseModel):
    platform: Optional[str] = None
    min_match_score: float = 0.5
    max_jobs: int = 10
    keywords: Optional[str] = None
    locations: Optional[List[str]] = None
    remote_only: bool = False


@router.post("/apply-matching", response_model=BulkApplyResponse)
async def apply_to_matching_jobs(request: ApplyMatchingRequest, background_tasks: BackgroundTasks, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    """Find the best-matching saved jobs and apply automatically in one click."""
    query = {"is_active": True}
    if request.platform:
        query["platform_source"] = request.platform
    if request.remote_only:
        query["remote_option"] = True

    job_docs = [doc async for doc in jobs.find(query)]

    user_profile = {
        "full_name": current_user.get("full_name") or current_user.get("username"),
        "email": current_user.get("email"),
        "phone": current_user.get("phone") or "",
        "skills": current_user.get("skills") or [],
        "experience_years": current_user.get("experience_years") or 0,
        "education": current_user.get("education") or [],
        "linkedin_url": current_user.get("linkedin_url") or "",
        "portfolio_url": current_user.get("portfolio_url") or "",
        "location": current_user.get("location") or "",
    }

    scored = []
    for job in job_docs:
        score = await ai_engine.match_job_to_profile(
            {"title": job.get("title"), "skills_required": job.get("skills_required") or [], "experience_required": job.get("experience_required") or 0},
            user_profile,
        )
        if score < request.min_match_score:
            continue
        if request.keywords:
            kw = request.keywords.lower()
            if kw not in ((job.get("title") or "") + " " + (job.get("description") or "")).lower():
                continue
        if request.locations and job.get("location"):
            if not any(loc.lower() in job["location"].lower() for loc in request.locations):
                continue
        scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [job for _, job in scored[:request.max_jobs]]

    applications_done = []
    successful = 0
    failed = 0
    pending = 0

    for job in selected:
        try:
            res, error = await _apply_to_single_job(job["id"], current_user, db)
            if res:
                applications_done.append(res)
                if res["needs_browser"]:
                    scheduled = await _schedule_apply(background_tasks, res, current_user.id, db)
                    if scheduled:
                        successful += 1
                    else:
                        pending += 1
                else:
                    successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Apply-matching error for job {job['id']}: {e}")
            failed += 1

    result_apps = []
    for r in applications_done:
        app_doc = await applications.find_one({"_id": r["record"].id})
        job_doc = await jobs.find_one({"_id": r["record"].get("job_id")})
        result_apps.append(_enrich(app_doc or {}, job_doc))

    return BulkApplyResponse(
        total=len(selected), successful=successful, failed=failed, pending=pending,
        applications=result_apps,
    )


@router.get("/matching-preview")
async def matching_preview(
    min_match_score: float = 0.5, limit: int = 10,
    platform: Optional[str] = None,
    current_user: Doc = Depends(get_current_user), db=Depends(get_db)
):
    """Preview which saved jobs the one-click apply would target."""
    query = {"is_active": True}
    if platform:
        query["platform_source"] = platform
    job_docs = [doc async for doc in jobs.find(query)]

    user_profile = {
        "skills": current_user.get("skills") or [],
        "experience_years": current_user.get("experience_years") or 0,
    }

    scored = []
    for job in job_docs:
        score = await ai_engine.match_job_to_profile(
            {"skills_required": job.get("skills_required") or [], "experience_required": job.get("experience_required") or 0},
            user_profile,
        )
        if score >= min_match_score:
            scored.append((score, job))
    scored.sort(key=lambda x: x[0], reverse=True)

    return {
        "total_matching": len(scored),
        "jobs": [
            {"id": job["id"], "title": job.get("title"), "company": job.get("company"), "match_score": score,
             "platform_source": job.get("platform_source"), "platform_url": job.get("platform_url")}
            for score, job in scored[:limit]
        ],
    }


@router.post("/{job_id}/apply", response_model=ApplicationResponse)
async def apply_single(job_id: int, background_tasks: BackgroundTasks, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    result, error = await _apply_to_single_job(job_id, current_user, db)
    if error:
        raise HTTPException(status_code=404, detail=error)

    if result["needs_browser"]:
        await _schedule_apply(background_tasks, result, current_user.id, db)

    app_doc = await applications.find_one({"_id": result["record"].id})
    job_doc = await jobs.find_one({"_id": job_id})
    return _enrich(app_doc or {}, job_doc)


@router.get("/", response_model=List[ApplicationResponse])
async def get_my_applications(
    status: Optional[str] = None, skip: int = 0, limit: int = 50,
    current_user: Doc = Depends(get_current_user), db=Depends(get_db)
):
    query = {"user_id": current_user.id}
    if status:
        query["status"] = status
    cursor = applications.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
    app_docs = [doc async for doc in cursor]
    enriched = []
    for a in app_docs:
        job_doc = await jobs.find_one({"_id": a.get("job_id")})
        enriched.append(_enrich(a, job_doc))
    return enriched


@router.get("/stats")
async def get_stats(current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    cursor = applications.find({"user_id": current_user.id})
    app_docs = [doc async for doc in cursor]
    total = len(app_docs)
    submitted = sum(1 for a in app_docs if a.get("status") == "submitted")
    pending = sum(1 for a in app_docs if a.get("status") == "pending")
    failed = sum(1 for a in app_docs if a.get("status") == "failed")
    interview = sum(1 for a in app_docs if a.get("status") == "interview")
    processing = sum(1 for a in app_docs if a.get("status") == "processing")
    return {
        "total_applications": total, "submitted": submitted, "pending": pending,
        "failed": failed, "interview": interview, "processing": processing,
        "response_rate": round((interview / total * 100) if total > 0 else 0, 1),
    }


@router.post("/reconcile")
async def reconcile_stuck_applications(current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    """Fix applications stuck in 'processing' (e.g. server restarted mid-task)."""
    cutoff = datetime.utcnow().timestamp() - 300
    cursor = applications.find({"user_id": current_user.id, "status": "processing"})
    app_docs = [doc async for doc in cursor]
    fixed = 0
    for app in app_docs:
        created_ts = app.get("created_at").timestamp() if app.get("created_at") else 0
        if created_ts < cutoff:
            fd = dict(app.get("form_data") or {})
            fd["note"] = "Automation interrupted (server restart). Please apply manually."
            await applications.update_one({"_id": app["_id"]}, {"$set": {
                "status": "pending", "form_data": fd, "updated_at": datetime.utcnow()
            }})
            fixed += 1
    return {"fixed": fixed, "message": f"Reset {fixed} stuck applications to pending"}