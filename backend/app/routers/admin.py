from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.core.database import users, applications, platform_connections, jobs, get_db
from app.routers.auth import get_admin_user
from app.core.mongo_doc import Doc

router = APIRouter()


class AdminUserDetail(BaseModel):
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
    is_active: bool
    is_admin: bool
    has_resume: bool
    resume_file_path: Optional[str]
    created_at: Optional[datetime]
    last_login_at: Optional[datetime]
    preferences: dict
    applications_count: int
    connections_count: int

    class Config:
        from_attributes = True


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_applications: int
    total_jobs: int
    connected_platforms: int
    users_today: int

    class Config:
        from_attributes = True


@router.get("/stats", response_model=AdminStats)
async def admin_stats(admin: Doc = Depends(get_admin_user)):
    now = datetime.utcnow()
    start_of_day = datetime(now.year, now.month, now.day)
    return AdminStats(
        total_users=await users.count_documents({}),
        active_users=await users.count_documents({"is_active": True}),
        total_applications=await applications.count_documents({}),
        total_jobs=await jobs.count_documents({}),
        connected_platforms=await platform_connections.count_documents({"is_connected": True}),
        users_today=await users.count_documents({"created_at": {"$gte": start_of_day}}),
    )


@router.get("/users", response_model=List[AdminUserDetail])
async def list_users(admin: Doc = Depends(get_admin_user), db=Depends(get_db), limit: int = 100, offset: int = 0):
    cursor = users.find({}).sort("created_at", -1).skip(offset).limit(limit)
    user_docs = [doc async for doc in cursor]

    app_counts = {}
    async for row in applications.aggregate([
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
    ]):
        app_counts[row["_id"]] = row["count"]

    conn_counts = {}
    async for row in platform_connections.aggregate([
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
    ]):
        conn_counts[row["_id"]] = row["count"]

    result = []
    for doc in user_docs:
        u = Doc(doc)
        result.append(AdminUserDetail(
            id=u.id,
            email=u.get("email"),
            username=u.get("username"),
            full_name=u.get("full_name"),
            phone=u.get("phone"),
            location=u.get("location"),
            linkedin_url=u.get("linkedin_url"),
            portfolio_url=u.get("portfolio_url"),
            skills=u.get("skills") or [],
            experience_years=u.get("experience_years") or 0,
            education=u.get("education") or [],
            is_active=bool(u.get("is_active", True)),
            is_admin=bool(u.get("is_admin", False)),
            has_resume=bool(u.get("resume_file_path")),
            resume_file_path=u.get("resume_file_path"),
            created_at=u.get("created_at"),
            last_login_at=u.get("last_login_at"),
            preferences=u.get("preferences") or {},
            applications_count=app_counts.get(u.id, 0),
            connections_count=conn_counts.get(u.id, 0),
        ))
    return result


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(user_id: int, admin: Doc = Depends(get_admin_user), db=Depends(get_db)):
    doc = await users.find_one({"_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    u = Doc(doc)
    return AdminUserDetail(
        id=u.id,
        email=u.get("email"),
        username=u.get("username"),
        full_name=u.get("full_name"),
        phone=u.get("phone"),
        location=u.get("location"),
        linkedin_url=u.get("linkedin_url"),
        portfolio_url=u.get("portfolio_url"),
        skills=u.get("skills") or [],
        experience_years=u.get("experience_years") or 0,
        education=u.get("education") or [],
        is_active=bool(u.get("is_active", True)),
        is_admin=bool(u.get("is_admin", False)),
        has_resume=bool(u.get("resume_file_path")),
        resume_file_path=u.get("resume_file_path"),
        created_at=u.get("created_at"),
        last_login_at=u.get("last_login_at"),
        preferences=u.get("preferences") or {},
        applications_count=await applications.count_documents({"user_id": user_id}),
        connections_count=await platform_connections.count_documents({"user_id": user_id}),
    )