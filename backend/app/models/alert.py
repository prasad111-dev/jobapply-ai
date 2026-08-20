from datetime import datetime

COLLECTION = "job_alerts"

def to_doc(alert: dict) -> dict:
    doc = dict(alert)
    doc.setdefault("keywords", [])
    doc.setdefault("is_active", True)
    doc.setdefault("created_at", datetime.utcnow())
    return doc


AUDIT_COLLECTION = "audit_logs"

def audit_to_doc(log: dict) -> dict:
    doc = dict(log)
    doc.setdefault("created_at", datetime.utcnow())
    return doc