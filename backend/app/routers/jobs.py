from fastapi import APIRouter, Depends, HTTPException, Query
import re
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.core.database import jobs, next_id, get_db
from app.routers.auth import get_current_user
from app.core.mongo_doc import Doc
from app.models.job import to_doc
from app.services.ai_engine import ai_engine

router = APIRouter()

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    description: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    job_type: str
    remote_option: bool
    platform_source: str
    platform_url: Optional[str] = None
    match_score: float
    skills_required: list
    posted_date: Optional[datetime]
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: str = "full-time"
    remote_option: bool = False
    platform_source: str = "manual"
    platform_url: Optional[str] = None
    skills_required: List[str] = []


def _regex_insensitive(text: str):
    return {"$regex": re.escape(text), "$options": "i"}


@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    search: Optional[str] = None,
    location: Optional[str] = None,
    platform: Optional[str] = None,
    min_match: float = 0.0,
    skip: int = 0,
    limit: int = 50,
    current_user: Doc = Depends(get_current_user),
    db=Depends(get_db)
):
    query = {}
    if search:
        query["$or"] = [
            {"title": _regex_insensitive(search)},
            {"company": _regex_insensitive(search)},
            {"description": _regex_insensitive(search)},
        ]
    if location:
        query["location"] = _regex_insensitive(location)
    if platform:
        query["platform_source"] = platform
    if min_match > 0:
        query["match_score"] = {"$gte": min_match}

    cursor = jobs.find(query).skip(skip).limit(limit)
    job_docs = [doc async for doc in cursor]

    user_profile = {
        "skills": current_user.get("skills") or [],
        "experience_years": current_user.get("experience_years") or 0,
    }

    jobs_list = []
    for jd in job_docs:
        jd["match_score"] = await ai_engine.match_job_to_profile(
            {"skills_required": jd.get("skills_required") or []},
            user_profile
        )
        jobs_list.append(jd)

    jobs_list.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return [JobResponse.model_validate(j) for j in jobs_list]

@router.post("/", response_model=JobResponse)
async def create_job(job_data: JobCreate, current_user: Doc = Depends(get_current_user), db=Depends(get_db)):
    job_id = await next_id("jobs")
    doc = to_doc(job_data.model_dump())
    doc["_id"] = job_id
    doc["id"] = job_id
    await jobs.insert_one(doc)
    return JobResponse.model_validate(doc)

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db=Depends(get_db)):
    doc = await jobs.find_one({"_id": job_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(doc)