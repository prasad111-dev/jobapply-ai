from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import users, next_id, get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_token
from app.models.user import to_doc
from app.core.mongo_doc import Doc

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


def _to_user_doc(user_dict: dict) -> Doc:
    return Doc(user_dict)


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_dict = await users.find_one({"_id": int(payload.get("sub"))})
    if not user_dict:
        raise HTTPException(status_code=401, detail="User not found")
    return _to_user_doc(user_dict)

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db=Depends(get_db)):
    existing = await users.find_one({"$or": [{"email": user_data.email}, {"username": user_data.username}]})
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already registered")

    user_id = await next_id("users")
    user_doc = to_doc({
        "_id": user_id,
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
    })
    await users.insert_one(user_doc)

    token = create_access_token(data={"sub": user_id})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(_to_user_doc(user_doc)))

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user_dict = await users.find_one({"username": form_data.username})
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token(data={"sub": user_dict["id"]})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(_to_user_doc(user_dict)))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Doc = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)