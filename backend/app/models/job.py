from datetime import datetime

COLLECTION = "jobs"

def to_doc(job: dict) -> dict:
    doc = dict(job)
    doc.setdefault("requirements", [])
    doc.setdefault("skills_required", [])
    doc.setdefault("job_type", "full-time")
    doc.setdefault("remote_option", False)
    doc.setdefault("match_score", 0.0)
    doc.setdefault("experience_required", 0)
    doc.setdefault("is_active", True)
    doc.setdefault("created_at", datetime.utcnow())
    return doc