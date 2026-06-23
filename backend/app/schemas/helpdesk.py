import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TicketCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    category: str = Field(..., max_length=50)
    priority: str = Field("Medium", max_length=50)
    location: str | None = Field(None, max_length=255)

class TicketUpdate(BaseModel):
    status: str | None = Field(None, max_length=50)
    priority: str | None = Field(None, max_length=50)
    assigned_to: uuid.UUID | None = None

class TicketOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    category: str
    status: str
    priority: str
    location: str | None
    created_by: uuid.UUID
    assigned_to: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    
    # Creator info returned for ease of UI display
    creator_name: str | None = None
    creator_role: str | None = None

    class Config:
        from_attributes = True
