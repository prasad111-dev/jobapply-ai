from datetime import datetime

COLLECTION = "platform_connections"

def to_doc(conn: dict) -> dict:
    doc = dict(conn)
    doc.setdefault("is_connected", False)
    doc.setdefault("settings", {})
    doc.setdefault("created_at", datetime.utcnow())
    return doc


CONFIG_COLLECTION = "platform_configs"

def config_to_doc(cfg: dict) -> dict:
    doc = dict(cfg)
    doc.setdefault("form_fields", [])
    doc.setdefault("is_active", True)
    doc.setdefault("difficulty_level", "medium")
    return doc