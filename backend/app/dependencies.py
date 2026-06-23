"""
FastAPI dependency injection utilities - SUPER SIMPLIFIED.
"""
import uuid
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_simple_token
from app.database import get_db
from app.models.user import UserProfile

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProfile:
    """Get current user from JWT token."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = verify_simple_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Look up user
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.id == uuid.UUID(user_id))
        )
        profile = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"DB lookup error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    if profile is None:
        raise HTTPException(status_code=401, detail="User not found")

    return profile


async def get_user_role_names(user: UserProfile) -> list[str]:
    """Return role names for a user. Uses simple role field for now."""
    if user.role:
        return [user.role]
    return ["STUDENT"]  # Default fallback


def require_role(*roles: str):
    """Require user to have one of the specified roles."""
    async def _check(
        current_user: Annotated[UserProfile, Depends(get_current_user)],
    ) -> UserProfile:
        user_roles = await get_user_role_names(current_user)
        if not any(r in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(roles)}",
            )
        return current_user
    return _check


# Pre-built dependencies
CurrentUser = Annotated[UserProfile, Depends(get_current_user)]
SuperAdmin = Annotated[UserProfile, Depends(require_role("SUPER_ADMIN"))]
AcademicWrite = Annotated[UserProfile, Depends(require_role("SUPER_ADMIN", "ACADEMIC_ADMIN"))]
HostelWrite = Annotated[UserProfile, Depends(require_role("SUPER_ADMIN", "HOSTEL_ADMIN", "HOSTEL_COORDINATOR"))]
MessWrite = Annotated[UserProfile, Depends(require_role("SUPER_ADMIN", "HOSTEL_ADMIN", "MESS_ADMIN"))]
PlacementWrite = Annotated[UserProfile, Depends(require_role("SUPER_ADMIN", "ACADEMIC_ADMIN", "PLACEMENT_ADMIN", "PLACEMENT_COORDINATOR"))]
ClubWrite = Annotated[UserProfile, Depends(require_role("SUPER_ADMIN", "CLUB_ADMIN", "CLUB_COORDINATOR"))]
FacultyWrite = Annotated[UserProfile, Depends(require_role("SUPER_ADMIN", "FACULTY"))]
