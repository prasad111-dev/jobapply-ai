from app.core.database import audit_logs, next_id
from app.models.alert import audit_to_doc

async def log_action(action: str, user_id: int = None, resource: str = None, resource_id: int = None, details: dict = None, ip_address: str = None, user_agent: str = None):
    log_id = await next_id("audit_logs")
    doc = audit_to_doc({
        "_id": log_id,
        "id": log_id,
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "details": details,
        "ip_address": ip_address,
        "user_agent": user_agent,
    })
    await audit_logs.insert_one(doc)