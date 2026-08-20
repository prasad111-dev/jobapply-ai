import asyncio
import logging
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.database import users, jobs, platform_connections, next_id
from app.core.mongo_doc import Doc
from app.models.job import to_doc as job_to_doc
from app.services.ai_engine import ai_engine
from app.services.email_service import send_email, build_job_digest_html, is_email_configured

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_digest_for_user(user: Doc) -> dict:
    """Scrape each connected platform's saved search, score jobs, email digest."""
    if not user.get("preferences") or not user["preferences"].get("digest_enabled"):
        return {"user": user.get("email"), "status": "skipped", "reason": "digest disabled"}

    if not is_email_configured():
        logger.info(f"Digest for {user.get('email')}: SMTP not configured, skipping email (enabled though)")
        return {"user": user.get("email"), "status": "email_disabled"}

    from app.services.browser_automation import browser_automation

    prefs = user.get("preferences") or {}
    queries = prefs.get("search_queries") or [prefs.get("search_query", "python developer")]
    if isinstance(queries, str):
        queries = [queries]

    cursor = platform_connections.find({
        "user_id": user.id, "is_connected": True
    })
    conns = [doc async for doc in cursor]
    platform_names = {c.get("platform_name") for c in conns}

    all_new = []
    for query in queries[:3]:
        for platform in list(platform_names)[:3]:
            try:
                scraped = await browser_automation.scrape_jobs(platform, query)
                for job_data in scraped:
                    url = job_data.get("platform_url", "")
                    if not url:
                        continue
                    exists = await jobs.find_one({"platform_url": url})
                    if exists:
                        continue
                    job_id = await next_id("jobs")
                    doc = job_to_doc(job_data)
                    doc["_id"] = job_id
                    doc["id"] = job_id
                    score = await ai_engine.match_job_to_profile(
                        {"skills_required": job_data.get("skills_required", [])},
                        {"skills": user.get("skills") or [], "experience_years": user.get("experience_years") or 0},
                    )
                    doc["match_score"] = score
                    if score >= 0.5:
                        await jobs.insert_one(doc)
                        all_new.append({
                            "title": doc.get("title"), "company": doc.get("company"), "location": doc.get("location"),
                            "platform_url": doc.get("platform_url"), "match_score": score,
                        })
            except Exception as e:
                logger.error(f"Digest scrape error {platform}/{query}: {e}")

    if all_new:
        html = build_job_digest_html(all_new, user.get("full_name") or user.get("username"))
        send_email(user.get("email"), f"JobApply AI: {len(all_new)} new matching jobs", html)
    else:
        logger.info(f"Digest for {user.get('email')}: no new matching jobs")

    return {"user": user.get("email"), "new_jobs": len(all_new), "status": "ok"}


async def digest_loop():
    """Background loop that runs the digest for all users on an interval."""
    await asyncio.sleep(30)
    logger.info(f"Digest scheduler started (every {settings.DIGEST_INTERVAL_HOURS}h)")
    while True:
        try:
            cursor = users.find({"is_active": True})
            user_docs = [doc async for doc in cursor]
            for user_doc in user_docs:
                try:
                    await run_digest_for_user(Doc(user_doc))
                except Exception as e:
                    logger.error(f"Digest failed for user {user_doc.get('id')}: {e}")
        except Exception as e:
            logger.error(f"Digest loop iteration error: {e}")
        await asyncio.sleep(settings.DIGEST_INTERVAL_HOURS * 3600)