import asyncio
import logging
from datetime import datetime
from typing import List
from app.workers.celery_app import celery_app
from app.core.database import users, jobs, applications, platform_connections, job_alerts, next_id
from app.core.mongo_doc import Doc
from app.models.application import to_doc as app_to_doc
from app.models.job import to_doc as job_to_doc
from app.services.ai_engine import ai_engine
from app.services.browser_automation import BrowserAutomation

logger = logging.getLogger(__name__)

def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def apply_to_job_task(self, user_id: int, job_id: int, custom_cover_letter: str = None):
    try:
        result = run_async(_apply_to_job(user_id, job_id, custom_cover_letter))
        return result
    except Exception as exc:
        logger.error(f"Apply task failed for user={user_id} job={job_id}: {exc}")
        self.retry(exc=exc)

async def _apply_to_job(user_id: int, job_id: int, custom_cover_letter: str = None):
    user_doc = await users.find_one({"_id": user_id})
    job_doc = await jobs.find_one({"_id": job_id})

    if not user_doc or not job_doc:
        return {"status": "error", "message": "User or job not found"}

    user_profile = {
        "full_name": user_doc.get("full_name") or user_doc.get("username"),
        "email": user_doc.get("email"),
        "phone": user_doc.get("phone") or "",
        "skills": user_doc.get("skills") or [],
        "experience_years": user_doc.get("experience_years") or 0,
        "education": user_doc.get("education") or [],
        "linkedin_url": user_doc.get("linkedin_url") or "",
        "portfolio_url": user_doc.get("portfolio_url") or "",
        "location": user_doc.get("location") or "",
    }

    cover_letter = custom_cover_letter
    if not cover_letter:
        cover_letter = await ai_engine.generate_cover_letter(
            job_doc.get("title"), job_doc.get("company"), job_doc.get("description") or "", user_profile
        )

    existing = await applications.find_one({"user_id": user_id, "job_id": job_id})

    if existing and existing.get("status") == "submitted":
        return {"status": "skipped", "message": "Already applied"}

    browser = BrowserAutomation()
    form_data = await browser.fill_application_form(
        job_doc.get("platform_url") or f"https://{job_doc.get('platform_source')}.com",
        user_profile,
        cover_letter
    )

    app_id = await next_id("applications")
    application = app_to_doc({
        "_id": app_id,
        "id": app_id,
        "user_id": user_id,
        "job_id": job_id,
        "platform_name": job_doc.get("platform_source"),
        "status": "submitted",
        "cover_letter": cover_letter,
        "form_data": form_data,
        "submitted_at": datetime.utcnow(),
    })
    await applications.insert_one(application)

    return {"status": "submitted", "application_id": app_id}

@celery_app.task(bind=True, max_retries=2)
def bulk_apply_task(self, user_id: int, job_ids: List[int], custom_cover_letter: str = None):
    results = []
    for job_id in job_ids:
        try:
            result = run_async(_apply_to_job(user_id, job_id, custom_cover_letter))
            results.append({"job_id": job_id, **result})
        except Exception as e:
            results.append({"job_id": job_id, "status": "error", "message": str(e)})

    successful = sum(1 for r in results if r.get("status") == "submitted")
    return {"total": len(job_ids), "successful": successful, "results": results}

@celery_app.task
def sync_all_platforms():
    run_async(_sync_all_platforms())

async def _sync_all_platforms():
    cursor = platform_connections.find({"is_connected": True})
    connections = [doc async for doc in cursor]

    for conn in connections:
        try:
            browser = BrowserAutomation()
            jobs_data = await browser.scrape_jobs(conn.get("platform_name"), conn.get("username"))

            for job_data in jobs_data:
                existing = await jobs.find_one({"platform_job_id": job_data.get("platform_job_id")})
                if not existing:
                    job_id = await next_id("jobs")
                    doc = job_to_doc({"_id": job_id, "id": job_id, **job_data})
                    await jobs.insert_one(doc)

            await platform_connections.update_one(
                {"_id": conn["_id"]},
                {"$set": {"last_synced": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Sync failed for {conn.get('platform_name')}: {e}")

@celery_app.task
def check_job_alerts():
    run_async(_check_job_alerts())

async def _check_job_alerts():
    cursor = job_alerts.find({"is_active": True})
    alerts = [doc async for doc in cursor]

    for alert in alerts:
        query = {"is_active": True}
        if alert.get("keywords"):
            or_conds = [{"title": {"$regex": kw, "$options": "i"}} for kw in alert["keywords"]]
            query["$or"] = or_conds
        if alert.get("location"):
            query["location"] = {"$regex": alert["location"], "$options": "i"}
        if alert.get("min_salary"):
            query["salary_max"] = {"$gte": alert["min_salary"]}

        matching_jobs = [doc async for doc in jobs.find(query).limit(10)]
        if matching_jobs:
            from app.services.email_service import send_job_alert_email
            user = await users.find_one({"_id": alert.get("user_id")})
            if user:
                await send_job_alert_email(user.get("email"), [j.get("title") for j in matching_jobs])

        await job_alerts.update_one(
            {"_id": alert["_id"]},
            {"$set": {"last_checked": datetime.utcnow()}}
        )

@celery_app.task
def generate_cover_letter_task(job_title: str, company: str, job_description: str, user_id: int):
    async def _generate():
        user = await users.find_one({"_id": user_id})
        if not user:
            return {"error": "User not found"}

        user_profile = {
            "full_name": user.get("full_name") or user.get("username"),
            "skills": user.get("skills") or [],
            "experience_years": user.get("experience_years") or 0,
            "education": user.get("education") or [],
        }
        letter = await ai_engine.generate_cover_letter(job_title, company, job_description, user_profile)
        return {"cover_letter": letter}
    return run_async(_generate())