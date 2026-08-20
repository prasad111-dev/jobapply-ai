from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.core.database import users, platform_connections, get_db
from app.routers.auth import get_current_user
from app.core.mongo_doc import Doc
from app.services.resume_ai import resume_ai
from app.services.file_storage import save_resume

router = APIRouter()

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    education: Optional[List[dict]] = None
    preferences: Optional[dict] = None

class ProfileResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    linkedin_url: Optional[str]
    portfolio_url: Optional[str]
    skills: list
    experience_years: int
    education: list
    preferences: dict
    has_resume: bool = False
    class Config:
        from_attributes = True

@router.get("/", response_model=ProfileResponse)
async def get_profile(current_user: Doc = Depends(get_current_user)):
    resp = ProfileResponse.model_validate(current_user)
    resp.has_resume = bool(current_user.get("resume_file_path"))
    return resp

@router.put("/", response_model=ProfileResponse)
async def update_profile(profile_data: ProfileUpdate, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    update_dict = profile_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    await users.update_one({"_id": current_user.id}, {"$set": update_dict})
    user_dict = await users.find_one({"_id": current_user.id})
    updated = Doc(user_dict)
    resp = ProfileResponse.model_validate(updated)
    resp.has_resume = bool(updated.get("resume_file_path"))
    return resp

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    if not file.filename.endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    file_path = save_resume(current_user.id, file.filename, content)

    parsed_data = await resume_ai.parse(content, file.filename)

    update = {
        "resume_text": parsed_data.get("raw_text", ""),
        "resume_parsed": parsed_data,
        "resume_file_path": file_path,
        "updated_at": datetime.utcnow(),
    }

    if parsed_data.get("full_name"):
        update["full_name"] = parsed_data["full_name"]
    if parsed_data.get("phone"):
        update["phone"] = parsed_data["phone"]
    if parsed_data.get("location"):
        update["location"] = parsed_data["location"]
    if parsed_data.get("linkedin_url"):
        update["linkedin_url"] = parsed_data["linkedin_url"]
    if parsed_data.get("portfolio_url"):
        update["portfolio_url"] = parsed_data["portfolio_url"]
    if parsed_data.get("skills"):
        update["skills"] = parsed_data["skills"]
    if parsed_data.get("experience_years") is not None:
        update["experience_years"] = parsed_data["experience_years"]
    if parsed_data.get("education"):
        update["education"] = parsed_data["education"]

    prefs = dict(current_user.get("preferences") or {})
    if parsed_data.get("expected_salary"):
        prefs["expected_salary"] = parsed_data["expected_salary"]
    update["preferences"] = prefs

    await users.update_one({"_id": current_user.id}, {"$set": update})
    user_dict = await users.find_one({"_id": current_user.id})
    updated = Doc(user_dict)

    return {
        "message": "Resume uploaded and parsed successfully",
        "parsed_data": parsed_data,
        "file_path": file_path,
        "auto_filled": {
            "full_name": updated.get("full_name"),
            "phone": updated.get("phone"),
            "location": updated.get("location"),
            "linkedin_url": updated.get("linkedin_url"),
            "portfolio_url": updated.get("portfolio_url"),
            "skills_count": len(updated.get("skills") or []),
        },
    }


def _completeness(user: Doc) -> dict:
    prefs = user.get("preferences") or {}
    checks = {
        "resume": {
            "done": bool(user.get("resume_file_path")),
            "label": "Upload your resume",
            "hint": "Upload a PDF/DOCX — AI fills your profile automatically",
            "route": "/profile",
        },
        "contact": {
            "done": bool(user.get("full_name") and user.get("phone") and user.get("email")),
            "label": "Add your name & phone",
            "hint": "Platforms require contact details on every application",
            "route": "/profile",
        },
        "skills": {
            "done": bool(user.get("skills")),
            "label": "Add your skills",
            "hint": "Skills are used to match and auto-answer questions",
            "route": "/profile",
        },
        "answers": {
            "done": bool(
                prefs.get("current_salary") and prefs.get("expected_salary")
                and prefs.get("notice_period") and prefs.get("availability")
            ),
            "label": "Fill application answers (salary, notice period, availability)",
            "hint": "These auto-answer common questions on every application",
            "route": "/profile",
        },
    }
    done_count = sum(1 for c in checks.values() if c["done"])
    total = len(checks)
    score = round((done_count / total) * 100) if total else 100
    return {
        "score": score,
        "complete": score == 100,
        "completed": done_count,
        "total": total,
        "steps": checks,
        "missing": [k for k, c in checks.items() if not c["done"]],
    }


@router.get("/completeness")
async def profile_completeness(current_user: Doc = Depends(get_current_user)):
    return _completeness(current_user)


@router.get("/readiness")
async def profile_readiness(current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    """Whether the user can apply right now: profile complete + a real connection exists."""
    comp = _completeness(current_user)
    cursor = platform_connections.find({
        "user_id": current_user.id,
        "is_connected": True,
    })
    conns = [doc async for doc in cursor]
    connections = [
        {"platform_name": c.get("platform_name"), "username": c.get("username"),
         "has_credentials": bool(c.get("auth_token") or c.get("refresh_token"))}
        for c in conns
    ]
    ready = comp["complete"] and any(c["has_credentials"] for c in connections)
    return {
        "ready": ready,
        "profile": comp,
        "connections": connections,
        "message": (
            "You're all set — pick jobs and click Apply!"
            if ready else
            "Complete your profile and connect a real account to enable auto-apply."
        ),
    }