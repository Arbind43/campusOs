"""
Placement router — drives, notices, student registration.
Read: all authenticated users.
Write: SUPER_ADMIN, PLACEMENT_ADMIN, PLACEMENT_COORDINATOR.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, PlacementWrite
from app.models.placement import DriveRegistration, PlacementDrive, PlacementNotice
from app.schemas.campus import (
    PlacementDriveCreate,
    PlacementDriveOut,
    PlacementNoticeCreate,
    PlacementNoticeOut,
)

router = APIRouter(prefix="/placement", tags=["placement"])
DB = Annotated[AsyncSession, Depends(get_db)]


# ── Drives ────────────────────────────────────────────────────────────────── #

@router.get("/drives", response_model=list[PlacementDriveOut])
async def list_drives(_user: CurrentUser, db: DB, active_only: bool = True) -> list[PlacementDriveOut]:
    query = select(PlacementDrive)
    if active_only:
        query = query.where(PlacementDrive.is_active == True)
    query = query.order_by(PlacementDrive.registration_deadline.asc().nullslast(), PlacementDrive.created_at.desc())
    result = await db.execute(query)
    return [PlacementDriveOut.model_validate(d) for d in result.scalars().all()]


@router.post("/drives", response_model=PlacementDriveOut, status_code=status.HTTP_201_CREATED)
async def create_drive(
    body: PlacementDriveCreate,
    admin: PlacementWrite,
    db: DB,
) -> PlacementDriveOut:
    drive = PlacementDrive(**body.model_dump(), created_by=admin.id)
    db.add(drive)
    await db.commit()
    await db.refresh(drive)
    return PlacementDriveOut.model_validate(drive)


@router.delete("/drives/{drive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drive(drive_id: uuid.UUID, _admin: PlacementWrite, db: DB) -> None:
    result = await db.execute(select(PlacementDrive).where(PlacementDrive.id == drive_id))
    drive = result.scalar_one_or_none()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    await db.delete(drive)
    await db.commit()


@router.post(
    "/drives/{drive_id}/register",
    status_code=status.HTTP_201_CREATED,
    summary="Student registers for a placement drive",
)
async def register_for_drive(
    drive_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> dict:
    # Check drive exists
    result = await db.execute(select(PlacementDrive).where(PlacementDrive.id == drive_id))
    drive = result.scalar_one_or_none()
    if not drive or not drive.is_active:
        raise HTTPException(status_code=404, detail="Drive not found or inactive")

    # Check not already registered
    reg_result = await db.execute(
        select(DriveRegistration).where(
            DriveRegistration.drive_id == drive_id,
            DriveRegistration.student_id == current_user.id,
        )
    )
    if reg_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already registered for this drive")

    registration = DriveRegistration(drive_id=drive_id, student_id=current_user.id)
    db.add(registration)
    await db.commit()
    return {"message": f"Successfully registered for {drive.company_name} drive"}


# ── Notices ───────────────────────────────────────────────────────────────── #

@router.get("/notices", response_model=list[PlacementNoticeOut])
async def list_placement_notices(_user: CurrentUser, db: DB) -> list[PlacementNoticeOut]:
    result = await db.execute(
        select(PlacementNotice).order_by(PlacementNotice.created_at.desc()).limit(30)
    )
    return [PlacementNoticeOut.model_validate(n) for n in result.scalars().all()]


@router.post("/notices", response_model=PlacementNoticeOut, status_code=status.HTTP_201_CREATED)
async def create_placement_notice(
    body: PlacementNoticeCreate,
    admin: PlacementWrite,
    db: DB,
) -> PlacementNoticeOut:
    notice = PlacementNotice(
        title=body.title,
        body=body.body,
        drive_id=body.drive_id,
        created_by=admin.id,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return PlacementNoticeOut.model_validate(notice)


@router.delete("/notices/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_placement_notice(notice_id: int, _admin: PlacementWrite, db: DB) -> None:
    result = await db.execute(select(PlacementNotice).where(PlacementNotice.id == notice_id))
    notice = result.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    await db.delete(notice)
    await db.commit()
