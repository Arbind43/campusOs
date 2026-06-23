"""
Notices router — domain-tagged notice board.
Anyone can read; posting requires domain-appropriate role.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.models.content import Notice
from app.models.user import UserProfile
from app.schemas.campus import NoticeCreate, NoticeOut

router = APIRouter(prefix="/notices", tags=["notices"])
DB = Annotated[AsyncSession, Depends(get_db)]

NOTICE_DOMAIN_ROLES = {
    "academic": ["SUPER_ADMIN", "ACADEMIC_ADMIN"],
    "hostel": ["SUPER_ADMIN", "HOSTEL_ADMIN", "HOSTEL_COORDINATOR"],
    "placement": ["SUPER_ADMIN", "PLACEMENT_ADMIN", "PLACEMENT_COORDINATOR"],
    "clubs": ["SUPER_ADMIN", "CLUB_ADMIN", "CLUB_COORDINATOR"],
    "general": ["SUPER_ADMIN", "ACADEMIC_ADMIN", "HOSTEL_ADMIN", "PLACEMENT_ADMIN"],
}


@router.get("", response_model=list[NoticeOut], summary="Get notices visible to current user")
async def list_notices(
    current_user: CurrentUser,
    db: DB,
    domain: str | None = None,
    limit: int = 50,
) -> list[NoticeOut]:
    query = select(Notice).order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).limit(limit)
    if domain:
        query = query.where(Notice.domain == domain)
    # Filter by department: global notices (NULL) always included.
    if current_user.department_id:
        query = query.where(
            (Notice.target_department_id == current_user.department_id) |
            (Notice.target_department_id.is_(None))
        )
    # Filter by year of study: notices targeting all years (NULL) always included.
    if current_user.year_of_study:
        query = query.where(
            (Notice.target_year == current_user.year_of_study) |
            (Notice.target_year.is_(None))
        )
    result = await db.execute(query)
    return [NoticeOut.model_validate(n) for n in result.scalars().all()]


@router.post(
    "",
    response_model=NoticeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Post a notice (domain admins / coordinators)",
)
async def create_notice(
    body: NoticeCreate,
    current_user: CurrentUser,
    db: DB,
) -> NoticeOut:
    # Check domain-specific permission
    allowed_roles = NOTICE_DOMAIN_ROLES.get(body.domain, ["SUPER_ADMIN"])
    user_role_names = [ur.role.name for ur in current_user.user_roles if ur.role]
    if not user_role_names:
        user_role_names = [current_user.role]
    if not any(r in user_role_names for r in allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You need one of {allowed_roles} to post {body.domain} notices",
        )

    notice = Notice(
        title=body.title,
        body=body.body,
        domain=body.domain,
        target_department_id=body.target_department_id,
        target_year=body.target_year,
        created_by=current_user.id,
        is_pinned=body.is_pinned,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return NoticeOut.model_validate(notice)


@router.delete(
    "/{notice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notice",
)
async def delete_notice(
    notice_id: uuid.UUID,
    current_user: Annotated[UserProfile, Depends(require_role("SUPER_ADMIN", "ACADEMIC_ADMIN", "HOSTEL_ADMIN", "PLACEMENT_ADMIN", "CLUB_ADMIN"))],
    db: DB,
) -> None:
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    notice = result.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    await db.delete(notice)
    await db.commit()
