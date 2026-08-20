from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from app.core.config import get_settings

settings = get_settings()

client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=10000)

db = client[settings.MONGODB_DB_NAME]

counters = db.counters
users = db.users
platform_connections = db.platform_connections
platform_configs = db.platform_configs
jobs = db.jobs
applications = db.applications
job_alerts = db.job_alerts
audit_logs = db.audit_logs


async def next_id(collection_name: str) -> int:
    """Return the next auto-increment integer id for a collection."""
    counter = await counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return counter["seq"]


async def init_indexes():
    await users.create_index([("email", ASCENDING)], unique=True)
    await users.create_index([("username", ASCENDING)], unique=True)
    await platform_connections.create_index([("user_id", ASCENDING), ("platform_name", ASCENDING)])
    await jobs.create_index([("platform_url", ASCENDING)], unique=True, sparse=True)
    await jobs.create_index([("title", ASCENDING)])
    await applications.create_index([("user_id", ASCENDING)])
    await applications.create_index([("job_id", ASCENDING)])


async def get_db():
    """FastAPI dependency that yields the Motor database object."""
    yield db