"""
Events router — cross-domain events with student registration.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.models.content import Event, EventRegistration
from app.schemas.campus import EventCreate, EventOut

router = APIRouter(prefix="/events", tags=["events"])
DB = Annotated[AsyncSession, Depends(get_db)]

EventWrite = Annotated[
    __import__("app.models.user", fromlist=["UserProfile"]).UserProfile,
    Depends(require_role(
        "SUPER_ADMIN", "ACADEMIC_ADMIN", "HOSTEL_ADMIN",
        "PLACEMENT_ADMIN", "CLUB_ADMIN", "CLUB_COORDINATOR",
        "PLACEMENT_COORDINATOR", "HOSTEL_COORDINATOR"
    )),
]


@router.get("", response_model=list[EventOut])
async def list_events(
    _user: CurrentUser,
    db: DB,
    domain: str | None = None,
) -> list[EventOut]:
    query = select(Event).order_by(Event.event_date.asc())
    if domain:
        query = query.where(Event.domain == domain)
    result = await db.execute(query)
    return [EventOut.model_validate(e) for e in result.scalars().all()]


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    admin: EventWrite,
    db: DB,
) -> EventOut:
    event = Event(**body.model_dump(), created_by=admin.id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return EventOut.model_validate(event)


@router.post(
    "/{event_id}/register",
    status_code=status.HTTP_201_CREATED,
    summary="Student registers for an event",
)
async def register_for_event(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> dict:
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not event.requires_registration:
        raise HTTPException(status_code=400, detail="This event does not require registration")

    reg_result = await db.execute(
        select(EventRegistration).where(
            EventRegistration.event_id == event_id,
            EventRegistration.student_id == current_user.id,
        )
    )
    if reg_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already registered for this event")

    registration = EventRegistration(event_id=event_id, student_id=current_user.id)
    db.add(registration)
    await db.commit()
    return {"message": f"Successfully registered for '{event.title}'"}
