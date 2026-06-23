import asyncio
from app.database import engine
from app.database import Base
# ensure models are imported
from app.models.academic import Department, Timetable, ExamSchedule, Holiday
from app.models.attendance import AttendanceRecord
from app.models.mess import MessSchedule, MessRating
from app.models.chat import ChatMessage
from app.models.hostel import Hostel, HostelRoom, MessMenu, MessNotice
from app.models.placement import PlacementDrive, DriveRegistration, PlacementNotice
from app.models.club import Club, ClubMembership
from app.models.content import Notice, Event, EventRegistration, Assignment
from app.models.wellbeing import WellbeingCheckin
from app.models.user import UserProfile
from app.models.rbac import Role, UserRole
from app.models.helpdesk import Ticket

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Created tables!")

if __name__ == "__main__":
    asyncio.run(init_models())
