from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.routers.auth import get_current_user
from app.core.mongo_doc import Doc
from app.services.ai_engine import ai_engine

router = APIRouter()

class CoverLetterRequest(BaseModel):
    job_title: str
    company: str
    job_description: str

class CoverLetterResponse(BaseModel):
    cover_letter: str

class JobMatchRequest(BaseModel):
    skills_required: List[str]
    experience_required: int = 0

@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(request: CoverLetterRequest, current_user: Doc = Depends(get_current_user)):
    user_profile = {
        "full_name": current_user.get("full_name") or current_user.get("username"),
        "skills": current_user.get("skills") or [],
        "experience_years": current_user.get("experience_years") or 0,
        "education": current_user.get("education") or [],
    }
    
    cover_letter = await ai_engine.generate_cover_letter(
        request.job_title, request.company, request.job_description, user_profile
    )
    return CoverLetterResponse(cover_letter=cover_letter)

@router.post("/match-score")
async def calculate_match(request: JobMatchRequest, current_user: Doc = Depends(get_current_user)):
    job = {"skills_required": request.skills_required, "experience_required": request.experience_required}
    user_profile = {"skills": current_user.get("skills") or [], "experience_years": current_user.get("experience_years") or 0}
    
    score = await ai_engine.match_job_to_profile(job, user_profile)
    return {"match_score": score, "user_skills": user_profile["skills"], "required_skills": request.skills_required}

@router.post("/optimize-resume")
async def optimize_resume(job_description: str, current_user: Doc = Depends(get_current_user)):
    user_skills = current_user.get("skills") or []
    
    job_desc_lower = job_description.lower()
    missing_skills = [s for s in user_skills if s not in job_desc_lower]
    relevant_skills = [s for s in user_skills if s in job_desc_lower]
    
    return {
        "relevant_skills": relevant_skills,
        "missing_skills": missing_skills,
        "suggestion": f"Consider adding these skills to your resume if you have them: {', '.join(missing_skills[:5])}",
        "current_skills": user_skills
    }
