from datetime import datetime

COLLECTION = "users"

def to_doc(user: dict) -> dict:
    """Return a Mongo document for a user, ensuring defaults."""
    doc = dict(user)
    doc.setdefault("skills", [])
    doc.setdefault("education", [])
    doc.setdefault("preferences", {})
    doc.setdefault("is_active", True)
    doc.setdefault("is_verified", False)
    doc.setdefault("is_admin", False)
    doc.setdefault("created_at", datetime.utcnow())
    doc.setdefault("updated_at", datetime.utcnow())
    return doc