import asyncio
import logging
from app.core.database import users, jobs, next_id
from app.core.security import get_password_hash
from app.models.user import to_doc as user_to_doc
from app.models.job import to_doc as job_to_doc
from app.core.config import get_settings

logger = logging.getLogger(__name__)

ADMIN_EMAILS = ["prasadghavghave0@gmail.com"]

async def ensure_admins():
    """Promote configured admin emails. Safe to run on every startup."""
    for email in ADMIN_EMAILS:
        doc = await users.find_one({"email": email})
        if doc:
            if not doc.get("is_admin"):
                await users.update_one({"_id": doc["_id"]}, {"$set": {"is_admin": True}})
                logger.info(f"Promoted {email} to admin")
            else:
                logger.info(f"{email} already admin")
        else:
            logger.warning(f"Admin email {email} not found in users collection - register it first")
    for email in get_settings().EXTRA_ADMIN_EMAILS:
        doc = await users.find_one({"email": email})
        if doc and not doc.get("is_admin"):
            await users.update_one({"_id": doc["_id"]}, {"$set": {"is_admin": True}})
            logger.info(f"Promoted {email} to admin")

async def seed_database():
    existing = await users.find_one({"email": "admin@jobapply.ai"})
    if existing:
        logger.info("Database already seeded")
        return

    user_id = await next_id("users")
    admin = user_to_doc({
        "_id": user_id,
        "id": user_id,
        "email": "admin@jobapply.ai",
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),
        "full_name": "Admin User",
        "is_active": True,
        "is_verified": True,
        "skills": ["python", "fastapi", "react", "postgresql"],
        "experience_years": 5,
    })
    await users.insert_one(admin)

    await seed_jobs()
    logger.info("Database seeded successfully with admin user")


async def seed_jobs():
    existing_count = await jobs.count_documents({})
    if existing_count > 0:
        logger.info("Jobs already exist, skipping sample job seed")
        return

    sample_jobs = [
        {"title": "Senior Python Developer", "company": "TechCorp", "location": "Remote", "platform_source": "indeed", "skills_required": ["python", "fastapi", "postgresql"], "salary_min": 80000, "salary_max": 120000},
        {"title": "Full Stack Engineer", "company": "StartupXYZ", "location": "Bangalore", "platform_source": "naukri", "skills_required": ["react", "node.js", "python"], "salary_min": 60000, "salary_max": 100000},
        {"title": "DevOps Engineer", "company": "CloudInc", "location": "Mumbai", "platform_source": "linkedin", "skills_required": ["aws", "docker", "kubernetes", "terraform"], "salary_min": 90000, "salary_max": 140000},
        {"title": "ML Engineer", "company": "AI Labs", "location": "Hyderabad", "platform_source": "hirist", "skills_required": ["python", "tensorflow", "pytorch", "machine learning"], "salary_min": 100000, "salary_max": 160000},
        {"title": "Frontend Developer", "company": "WebCo", "location": "Pune", "platform_source": "internshala", "skills_required": ["react", "typescript", "css", "html"], "salary_min": 40000, "salary_max": 70000},
        {"title": "Backend Developer", "company": "DataFlow", "location": "Remote", "platform_source": "cutshort", "skills_required": ["python", "django", "redis", "celery"], "salary_min": 70000, "salary_max": 110000},
        {"title": "iOS Developer", "company": "AppStudio", "location": "Chennai", "platform_source": "shine", "skills_required": ["swift", "ios", "xcode", "core data"], "salary_min": 50000, "salary_max": 90000},
        {"title": "Data Engineer", "company": "BigData Corp", "location": "Delhi", "platform_source": "timesjobs", "skills_required": ["python", "spark", "hadoop", "sql"], "salary_min": 75000, "salary_max": 120000},
        {"title": "QA Automation Engineer", "company": "QualityFirst", "location": "Noida", "platform_source": "foundit", "skills_required": ["python", "selenium", "playwright", "pytest"], "salary_min": 55000, "salary_max": 85000},
        {"title": "Cloud Architect", "company": "CloudNative", "location": "Remote", "platform_source": "wellfound", "skills_required": ["aws", "azure", "gcp", "terraform", "docker"], "salary_min": 120000, "salary_max": 180000},
    ]

    for job_data in sample_jobs:
        job_id = await next_id("jobs")
        doc = job_to_doc({
            "_id": job_id,
            "id": job_id,
            **job_data,
            "description": f"Looking for a skilled {job_data['title']} to join our team.",
            "job_type": "full-time",
        })
        await jobs.insert_one(doc)
    logger.info("Sample jobs seeded")

if __name__ == "__main__":
    asyncio.run(seed_database())