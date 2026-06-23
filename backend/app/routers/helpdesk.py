import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.helpdesk import Ticket
from app.schemas.helpdesk import TicketCreate, TicketOut, TicketUpdate

router = APIRouter(prefix="/helpdesk", tags=["helpdesk"])


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: TicketCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketOut:
    """Create a new helpdesk ticket."""
    ticket = Ticket(
        id=uuid.uuid4(),
        title=body.title,
        description=body.description,
        category=body.category,
        priority=body.priority,
        location=body.location,
        created_by=user.id,
        status="Open",
    )
    db.add(ticket)
    await db.commit()
    
    # Reload with creator to populate creator name
    stmt = select(Ticket).options(selectinload(Ticket.creator)).where(Ticket.id == ticket.id)
    result = await db.execute(stmt)
    ticket_with_creator = result.scalar_one()
    
    out = TicketOut.model_validate(ticket_with_creator)
    out.creator_name = ticket_with_creator.creator.full_name
    out.creator_role = ticket_with_creator.creator.role
    return out


@router.get("/tickets", response_model=List[TicketOut])
async def get_tickets(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[TicketOut]:
    """
    Get tickets. 
    Admins see all tickets. Students/Professors see only their own.
    """
    stmt = select(Ticket).options(selectinload(Ticket.creator)).order_by(Ticket.created_at.desc())
    
    # Filter by user if not admin
    if user.role != "ACADEMIC_ADMIN":
        stmt = stmt.where(Ticket.created_by == user.id)
        
    result = await db.execute(stmt)
    tickets = result.scalars().all()
    
    out_list = []
    for t in tickets:
        out = TicketOut.model_validate(t)
        if t.creator:
            out.creator_name = t.creator.full_name
            out.creator_role = t.creator.role
        out_list.append(out)
        
    return out_list


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: uuid.UUID,
    body: TicketUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketOut:
    """Update ticket status, priority, or assignee. Admins only."""
    if user.role != "ACADEMIC_ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can update tickets")
        
    stmt = select(Ticket).options(selectinload(Ticket.creator)).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    if body.status is not None:
        ticket.status = body.status
    if body.priority is not None:
        ticket.priority = body.priority
    if body.assigned_to is not None:
        ticket.assigned_to = body.assigned_to
        
    await db.commit()
    await db.refresh(ticket)
    
    out = TicketOut.model_validate(ticket)
    if ticket.creator:
        out.creator_name = ticket.creator.full_name
        out.creator_role = ticket.creator.role
    return out
