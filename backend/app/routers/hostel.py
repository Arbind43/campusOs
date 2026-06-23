"""
Hostel router — mess menu, notices, rooms.
Read: all authenticated users.
Write: SUPER_ADMIN, HOSTEL_ADMIN, HOSTEL_COORDINATOR (menu/notices).
       SUPER_ADMIN, HOSTEL_ADMIN (rooms).
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, HostelWrite, MessWrite
from app.models.hostel import Hostel, HostelRoom, MessMenu, MessNotice
from app.schemas.campus import (
    HostelOut,
    HostelRoomCreate,
    HostelRoomOut,
    MessMenuCreate,
    MessMenuOut,
    MessNoticeCreate,
    MessNoticeOut,
)

router = APIRouter(prefix="/hostel", tags=["hostel"])
DB = Annotated[AsyncSession, Depends(get_db)]


# ── Hostels ───────────────────────────────────────────────────────────────── #

@router.get("", response_model=list[HostelOut])
async def list_hostels(_user: CurrentUser, db: DB) -> list[HostelOut]:
    result = await db.execute(select(Hostel).order_by(Hostel.name))
    return [HostelOut.model_validate(h) for h in result.scalars().all()]


# ── Rooms ─────────────────────────────────────────────────────────────────── #

@router.get("/rooms", response_model=list[HostelRoomOut])
async def list_rooms(
    _user: CurrentUser,
    db: DB,
    hostel_id: uuid.UUID | None = None,
) -> list[HostelRoomOut]:
    query = select(HostelRoom)
    if hostel_id:
        query = query.where(HostelRoom.hostel_id == hostel_id)
    result = await db.execute(query.order_by(HostelRoom.room_number))
    return [HostelRoomOut.model_validate(r) for r in result.scalars().all()]


@router.post("/rooms", response_model=HostelRoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(
    body: HostelRoomCreate,
    _admin: HostelWrite,
    db: DB,
) -> HostelRoomOut:
    room = HostelRoom(**body.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return HostelRoomOut.model_validate(room)


# ── Mess Menu ─────────────────────────────────────────────────────────────── #

@router.get("/menu", response_model=list[MessMenuOut])
async def get_mess_menu(
    _user: CurrentUser,
    db: DB,
    hostel_id: uuid.UUID | None = None,
) -> list[MessMenuOut]:
    query = select(MessMenu)
    if hostel_id:
        query = query.where(MessMenu.hostel_id == hostel_id)
    query = query.order_by(MessMenu.week_start.desc(), MessMenu.day_of_week, MessMenu.meal_type)
    result = await db.execute(query)
    return [MessMenuOut.model_validate(m) for m in result.scalars().all()]


@router.post("/menu", response_model=MessMenuOut, status_code=status.HTTP_201_CREATED)
async def create_mess_menu(
    body: MessMenuCreate,
    _admin: MessWrite,
    db: DB,
) -> MessMenuOut:
    menu = MessMenu(**body.model_dump())
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return MessMenuOut.model_validate(menu)


# ── Mess Notices ──────────────────────────────────────────────────────────── #

@router.get("/notices", response_model=list[MessNoticeOut])
async def get_mess_notices(
    _user: CurrentUser,
    db: DB,
    hostel_id: uuid.UUID | None = None,
) -> list[MessNoticeOut]:
    query = select(MessNotice)
    if hostel_id:
        query = query.where(MessNotice.hostel_id == hostel_id)
    query = query.order_by(MessNotice.created_at.desc())
    result = await db.execute(query)
    return [MessNoticeOut.model_validate(n) for n in result.scalars().all()]


@router.post("/notices", response_model=MessNoticeOut, status_code=status.HTTP_201_CREATED)
async def create_mess_notice(
    body: MessNoticeCreate,
    admin: HostelWrite,
    db: DB,
) -> MessNoticeOut:
    notice = MessNotice(
        hostel_id=body.hostel_id,
        title=body.title,
        body=body.body,
        created_by=admin.id,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return MessNoticeOut.model_validate(notice)
