"""
Clubs router — list clubs, manage membership, club events.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import ClubWrite, CurrentUser
from app.models.club import Club, ClubMembership
from app.schemas.campus import ClubOut

router = APIRouter(prefix="/clubs", tags=["clubs"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[ClubOut])
async def list_clubs(_user: CurrentUser, db: DB) -> list[ClubOut]:
    result = await db.execute(select(Club).order_by(Club.name))
    return [ClubOut.model_validate(c) for c in result.scalars().all()]


@router.get("/{club_id}", response_model=ClubOut)
async def get_club(club_id: uuid.UUID, _user: CurrentUser, db: DB) -> ClubOut:
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return ClubOut.model_validate(club)


@router.post("/{club_id}/join", status_code=status.HTTP_201_CREATED)
async def join_club(
    club_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> dict:
    # Check club exists
    result = await db.execute(select(Club).where(Club.id == club_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Club not found")

    # Check not already a member
    mem_result = await db.execute(
        select(ClubMembership).where(
            ClubMembership.club_id == club_id,
            ClubMembership.user_id == current_user.id,
        )
    )
    if mem_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already a member")

    membership = ClubMembership(user_id=current_user.id, club_id=club_id)
    db.add(membership)
    await db.commit()
    return {"message": "Successfully joined club"}


@router.delete("/{club_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_club(
    club_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    result = await db.execute(
        select(ClubMembership).where(
            ClubMembership.club_id == club_id,
            ClubMembership.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    await db.delete(membership)
    await db.commit()
