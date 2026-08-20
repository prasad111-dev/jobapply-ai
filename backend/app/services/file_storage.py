import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from app.core.config import get_settings

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = Path(settings.RESUME_STORAGE_PATH)
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BASE_DIR / UPLOAD_DIR
RESUME_DIR = UPLOAD_DIR / "resumes"
TEMP_DIR = UPLOAD_DIR / "temp"

def _ensure_dirs(base: Path):
    for d in [base, base / "resumes", base / "temp"]:
        d.mkdir(parents=True, exist_ok=True)

try:
    _ensure_dirs(UPLOAD_DIR)
    if not os.access(UPLOAD_DIR, os.W_OK):
        raise OSError("not writable")
except OSError:
    # Fall back to repo-local storage when the configured path isn't writable
    # (e.g. local dev without a mounted /data volume)
    UPLOAD_DIR = BASE_DIR / "uploads"
    RESUME_DIR = UPLOAD_DIR / "resumes"
    TEMP_DIR = UPLOAD_DIR / "temp"
    _ensure_dirs(UPLOAD_DIR)
    logger.warning(f"Configured RESUME_STORAGE_PATH not writable, using fallback {UPLOAD_DIR}")

def save_resume(user_id: int, filename: str, content: bytes) -> str:
    ext = Path(filename).suffix
    unique_name = f"{user_id}_{uuid.uuid4().hex}{ext}"
    file_path = RESUME_DIR / unique_name
    file_path.write_bytes(content)
    logger.info(f"Resume saved: {file_path}")
    return str(file_path)

def get_resume(file_path: str) -> Optional[bytes]:
    try:
        path = Path(file_path)
        if path.exists():
            return path.read_bytes()
    except Exception as e:
        logger.error(f"Failed to read resume: {e}")
    return None

def delete_resume(file_path: str) -> bool:
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
    except Exception as e:
        logger.error(f"Failed to delete resume: {e}")
    return False

def save_temp(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = TEMP_DIR / unique_name
    file_path.write_bytes(content)
    return str(file_path)

def cleanup_temp():
    for f in TEMP_DIR.glob("*"):
        if f.is_file():
            f.unlink()

def get_file_size(file_path: str) -> int:
    try:
        return Path(file_path).stat().st_size
    except:
        return 0
