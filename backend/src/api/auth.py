"""认证 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import (
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    require_user,
    verify_password,
)
from ..models.user import User

router = APIRouter(prefix="/api/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    display_name: str = Field(default="", description="显示名称")


class LoginRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    display_name: str
    avatar_url: str
    is_superuser: bool


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(
        (User.email == req.email) | (User.username == req.username)
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱或用户名已被注册")

    user = User(
        email=req.email,
        username=req.username,
        hashed_password=hash_password(req.password),
        display_name=req.display_name or req.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=_user_to_dict(user))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=_user_to_dict(user))


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_user)):
    return _user_to_dict(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(user: User = Depends(require_user)):
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=_user_to_dict(user))


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "is_superuser": user.is_superuser,
    }
