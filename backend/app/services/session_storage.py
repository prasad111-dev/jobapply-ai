import json
import logging
from pathlib import Path
from typing import List, Optional

from app.core.encryption import encrypt_secret, decrypt_secret

logger = logging.getLogger(__name__)

SESSION_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(user_id: int, platform: str) -> Path:
    return SESSION_DIR / f"u{user_id}_{platform}.enc"


def save_session_cookies(user_id: int, platform: str, cookies: List[dict]) -> bool:
    """Persist browser cookies so the user logs into a platform only ONCE."""
    if not cookies:
        return False
    try:
        payload = json.dumps(cookies)
        encrypted = encrypt_secret(payload)
        _session_path(user_id, platform).write_text(encrypted or "")
        logger.info(f"Saved session cookies for user {user_id} on {platform} ({len(cookies)} cookies)")
        return True
    except Exception as e:
        logger.error(f"Failed to save session cookies: {e}")
        return False


def load_session_cookies(user_id: int, platform: str) -> Optional[List[dict]]:
    path = _session_path(user_id, platform)
    if not path.exists():
        return None
    try:
        decrypted = decrypt_secret(path.read_text())
        if not decrypted:
            return None
        cookies = json.loads(decrypted)
        logger.info(f"Loaded session cookies for user {user_id} on {platform} ({len(cookies)} cookies)")
        return cookies
    except Exception as e:
        logger.error(f"Failed to load session cookies: {e}")
        return None


def delete_session_cookies(user_id: int, platform: str) -> None:
    path = _session_path(user_id, platform)
    if path.exists():
        try:
            path.unlink()
            logger.info(f"Deleted session cookies for user {user_id} on {platform}")
        except Exception as e:
            logger.error(f"Failed to delete session cookies: {e}")