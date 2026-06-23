"""
Super simple auth router - no Supabase, just email/password.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_simple_token, verify_simple_token
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.academic import Department
from app.models.user import UserProfile
from app.schemas.auth import UserProfileOut

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"  # student, admin, professor


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    """
    Simple login - checks if user exists, auto-creates if not.
    Password is ignored in dev mode (any password works).
    """
    # Find user by email
    result = await db.execute(select(UserProfile).where(UserProfile.email == body.email))
    profile = result.scalar_one_or_none()
    
    if profile is None:
        # Auto-create user
        role = "STUDENT"
        if "admin" in body.email.lower():
            role = "ACADEMIC_ADMIN"
        elif "professor" in body.email.lower() or "faculty" in body.email.lower():
            role = "FACULTY"
        
        # Get or create department
        dept_result = await db.execute(select(Department).limit(1))
        dept = dept_result.scalar_one_or_none()
        if dept is None:
            dept = Department(name="Computer Science & Engineering", code="CSE")
            db.add(dept)
            await db.flush()
        
        profile = UserProfile(
            id=uuid.uuid4(),
            email=body.email,
            full_name=body.email.split("@")[0].title(),
            role=role,
            is_demo=False,
            department_id=dept.id,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    
    # Create token
    token = create_simple_token(str(profile.id), profile.email)
    
    # Build response
    user_out = UserProfileOut.model_validate(profile)
    user_out.roles = [profile.role]
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_out,
    )


@router.post("/register", response_model=LoginResponse)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    """
    Register a new user.
    """
    # Check if user exists
    result = await db.execute(select(UserProfile).where(UserProfile.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Map role
    role_map = {
        "student": "STUDENT",
        "admin": "ACADEMIC_ADMIN",
        "professor": "FACULTY",
        "faculty": "FACULTY",
    }
    role = role_map.get(body.role.lower(), "STUDENT")
    
    # Get or create department
    dept_result = await db.execute(select(Department).limit(1))
    dept = dept_result.scalar_one_or_none()
    if dept is None:
        dept = Department(name="Computer Science & Engineering", code="CSE")
        db.add(dept)
        await db.flush()
    
    # Create user
    profile = UserProfile(
        id=uuid.uuid4(),
        email=body.email,
        full_name=body.full_name,
        role=role,
        is_demo=False,
        department_id=dept.id,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    
    # Create token
    token = create_simple_token(str(profile.id), profile.email)
    
    # Build response
    user_out = UserProfileOut.model_validate(profile)
    user_out.roles = [profile.role]
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_out,
    )


@router.get("/me", response_model=UserProfileOut)
async def me(user: CurrentUser) -> UserProfileOut:
    """Return the currently authenticated user's profile."""
    out = UserProfileOut.model_validate(user)
    out.roles = [user.role]
    return out


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Dummy endpoint for forgot password in dev mode.
    Always returns success to prevent email enumeration.
    """
    result = await db.execute(select(UserProfile).where(UserProfile.email == body.email))
    profile = result.scalar_one_or_none()
    
    # In a real app, generate a secure token and send an email here.
    return {"success": True, "message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    """
    Dummy endpoint for resetting password.
    Always returns success in dev mode.
    """
    # In a real app, verify the token and update the user's password hash in the database.
    return {"success": True, "message": "Password reset successfully. You can now log in with your new password."}
