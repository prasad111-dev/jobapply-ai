"""Background scraper that pulls jobs across ALL categories from ALL platforms.

Runs on startup and periodically. No fake data — every job is real.
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Every major job category — these are the queries sent to scrapers
JOB_CATEGORIES = [
    # Software & IT
    "software engineer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "python developer",
    "java developer",
    "react developer",
    "node js developer",
    "android developer",
    "ios developer",
    "devops engineer",
    "cloud engineer",
    "aws developer",
    "machine learning engineer",
    "data scientist",
    "data analyst",
    "data engineer",
    "artificial intelligence",
    "blockchain developer",
    "cyber security",
    "network engineer",
    "system administrator",
    "database administrator",
    "QA engineer",
    "test engineer",
    "software tester",
    # Design & Creative
    "ui ux designer",
    "graphic designer",
    "web designer",
    "product designer",
    "motion graphics",
    "video editor",
    # Marketing & Sales
    "digital marketing",
    "content writer",
    "social media manager",
    "seo specialist",
    "sales executive",
    "business development",
    "marketing manager",
    "account executive",
    "growth hacker",
    "email marketing",
    # Finance & Accounting
    "accountant",
    "financial analyst",
    "chartered accountant",
    "tax consultant",
    "audit",
    "finance manager",
    # HR & Admin
    "human resources",
    "recruiter",
    "talent acquisition",
    "hr manager",
    "office administrator",
    # Operations & Management
    "project manager",
    "product manager",
    "operations manager",
    "supply chain",
    "logistics",
    "procurement",
    "warehouse",
    # Education & Training
    "teacher",
    "trainer",
    "tutor",
    "lecturer",
    "educational consultant",
    # Healthcare
    "nurse",
    "doctor",
    "pharmacist",
    "medical",
    "healthcare",
    # Legal
    "lawyer",
    "legal advisor",
    "paralegal",
    # Customer Support
    "customer support",
    "customer service",
    "technical support",
    "call center",
    # Internships
    "internship",
    "fresher",
    "entry level",
    # Remote specific
    "remote software",
    "work from home",
    "freelancer",
    # Industry specific
    "electrical engineer",
    "mechanical engineer",
    "civil engineer",
    "architecture",
    "journalism",
    "journalist",
    "content creator",
    "animation",
    "photography",
    "interior design",
    "fashion designer",
    "hospitality",
    "hotel management",
    "chef",
    "restaurant",
    "travel agent",
    "event management",
]

# Fewer queries for the free-tier JSearch (200 req/month)
# These are the most important categories
JSEARCH_CATEGORIES = [
    "software engineer",
    "data scientist",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "digital marketing",
    "sales executive",
    "project manager",
    "product manager",
    "human resources",
    "accountant",
    "graphic designer",
    "customer support",
    "devops engineer",
    "cloud engineer",
    "ui ux designer",
    "content writer",
    "business development",
    "financial analyst",
    "operations manager",
]


async def scrape_all_categories(max_per_source: int = 50) -> dict:
    """Scrape ALL job categories from ALL platforms.

    Returns summary of how many jobs found per platform.
    """
    from app.services.real_scraper import (
        scrape_remoteok, scrape_remotive, scrape_internshala, scrape_jsearch,
    )

    total_saved = 0
    summary = {}

    # ---- Free scrapers (unlimited) ----
    free_scrapers = {
        "internshala": scrape_internshala,
        "remoteok": scrape_remoteok,
        "remotive": scrape_remotive,
    }

    for source_name, scraper_fn in free_scrapers.items():
        count = 0
        # Split categories into small batches to get diverse results
        query_batches = [
            " ".join(JOB_CATEGORIES[i:i+3])
            for i in range(0, len(JOB_CATEGORIES), 3)
        ]
        for batch_query in query_batches:
            try:
                jobs = await scraper_fn(batch_query, max_per_source=5)
                count += len(jobs)
                if count >= max_per_source * 2:
                    break
            except Exception as e:
                logger.warning("Category scrape %s/%s failed: %s", source_name, batch_query[:30], e)
        summary[source_name] = count
        total_saved += count

    # ---- JSearch (200 req/month free tier) ----
    # Use the key categories only to conserve requests
    jsearch_count = 0
    for category in JSEARCH_CATEGORIES:
        try:
            jobs = await scrape_jsearch(category, max_results=10, country="in", num_pages=1)
            jsearch_count += len(jobs)
        except Exception as e:
            logger.warning("JSearch category scrape %s failed: %s", category, e)
    # One more batch for remote/global jobs
    for category in JSEARCH_CATEGORIES[:10]:
        try:
            jobs = await scrape_jsearch(category, max_results=5, country="us", num_pages=1)
            jsearch_count += len(jobs)
        except Exception as e:
            logger.warning("JSearch remote category scrape %s failed: %s", category, e)
    summary["jsearch"] = jsearch_count
    total_saved += jsearch_count

    return {"total": total_saved, "summary": summary}


async def save_jobs_to_db(scraped_jobs: list) -> int:
    """Save scraped jobs to MongoDB, skip duplicates. Returns count saved."""
    from app.core.database import jobs, next_id

    saved = 0
    seen_urls = set()

    # Pre-fetch existing URLs for fast dedup
    existing_urls = set()
    cursor = jobs.find({}, {"platform_url": 1})
    async for doc in cursor:
        if doc.get("platform_url"):
            existing_urls.add(doc["platform_url"])

    from app.models.job import to_doc as job_to_doc

    for job_data in scraped_jobs:
        url = job_data.get("platform_url", "")
        if not url or url in seen_urls or url in existing_urls:
            continue
        seen_urls.add(url)
        existing_urls.add(url)

        job_id = await next_id("jobs")
        doc = job_to_doc(job_data)
        doc["_id"] = job_id
        doc["id"] = job_id
        await jobs.insert_one(doc)
        saved += 1

    return saved


async def background_scrape_all():
    """Run full scrape in background. Called on startup."""
    try:
        logger.info("Starting background full-category scrape...")
        result = await scrape_all_categories(max_per_source=50)
        logger.info("Background scrape complete: %s", result)
        return result
    except Exception as e:
        logger.error("Background scrape failed: %s", e)
        return {"error": str(e)}
