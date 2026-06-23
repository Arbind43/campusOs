# Import ALL models so Alembic's autogenerate can detect every table.
# Order matters: models with FKs must come after their dependencies.
from app.models.academic import Department, ExamSchedule, Holiday, Timetable
from app.models.attendance import AttendanceRecord
from app.models.chat import ChatMessage
from app.models.club import Club, ClubMembership
from app.models.content import Assignment, Event, EventRegistration, Notice
from app.models.helpdesk import Ticket
from app.models.hostel import Hostel, HostelRoom, MessMenu, MessNotice
from app.models.mess import MessSchedule, MessRating
from app.models.placement import DriveRegistration, PlacementDrive, PlacementNotice
from app.models.rbac import Role, UserRole
from app.models.user import UserProfile
from app.models.wellbeing import WellbeingCheckin

__all__ = [
    "UserProfile",
    "Role",
    "UserRole",
    "Department",
    "Timetable",
    "ExamSchedule",
    "Holiday",
    "AttendanceRecord",
    "MessSchedule",
    "MessRating",
    "ChatMessage",
    "Hostel",
    "HostelRoom",
    "MessMenu",
    "MessNotice",
    "PlacementDrive",
    "DriveRegistration",
    "PlacementNotice",
    "Club",
    "ClubMembership",
    "Notice",
    "Event",
    "EventRegistration",
    "Assignment",
    "WellbeingCheckin",
    "Ticket",
]
