from datetime import datetime

COLLECTION = "applications"

def to_doc(app: dict) -> dict:
    doc = dict(app)
    doc.setdefault("status", "pending")
    doc.setdefault("form_data", {})
    doc.setdefault("response_received", False)
    doc.setdefault("retry_count", 0)
    doc.setdefault("max_retries", 3)
    doc.setdefault("created_at", datetime.utcnow())
    doc.setdefault("updated_at", datetime.utcnow())
    return doc