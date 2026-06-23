import asyncio
import uuid
from datetime import date, timedelta, time

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.content import Notice, Event
from app.models.mess import MessSchedule, MessRating
from app.models.placement import PlacementDrive, PlacementNotice
from app.models.wellbeing import WellbeingCheckin
from app.models.user import UserProfile
from app.models.academic import Department

async def seed_data():
    async with AsyncSessionLocal() as db:
        # Get admin user if exists
        result = await db.execute(select(UserProfile).where(UserProfile.email == "admin@campusos.app"))
        admin = result.scalar_one_or_none()
        
        # Get demo user if exists
        result = await db.execute(select(UserProfile).where(UserProfile.email == "demo@campusos.app"))
        student = result.scalar_one_or_none()

        result = await db.execute(select(Department))
        dept = result.scalars().first()

        # Seed Notices
        notices = [
            Notice(
                title="Mid-term exams rescheduled",
                body="The mid-term exams scheduled for next week have been postponed by 2 days.",
                domain="academic",
                target_department_id=dept.id if dept else None,
                target_year=None,
                created_by=admin.id if admin else None,
                is_pinned=True
            ),
            Notice(
                title="Library timing extended",
                body="The central library will now remain open until 11 PM during the exam season.",
                domain="general",
                target_department_id=None,
                target_year=None,
                created_by=admin.id if admin else None,
                is_pinned=False
            )
        ]
        db.add_all(notices)

        # Seed Mess Schedule
        mess_items = [
            MessSchedule(day_of_week="Daily", meal_type="breakfast", start_time=time(7, 30), end_time=time(9, 30), items="Idli, Dosa, Sambar, Chutney, Tea/Coffee"),
            MessSchedule(day_of_week="Monday", meal_type="lunch", start_time=time(12, 30), end_time=time(14, 30), items="Rice, Dal, Paneer Butter Masala, Roti, Salad"),
            MessSchedule(day_of_week="Tuesday", meal_type="dinner", start_time=time(19, 30), end_time=time(21, 30), items="Chicken Curry, Veg Pulao, Raita", is_special=True),
            MessSchedule(day_of_week="Wednesday", meal_type="snacks", start_time=time(16, 30), end_time=time(17, 30), items="Samosa, Tea"),
        ]
        db.add_all(mess_items)

        # Seed Mess Ratings
        today = date.today()
        ratings = [
            MessRating(rating_date=today, meal_type="breakfast", rating=4, department_id=dept.id if dept else None, submitter_hash="hash1"),
            MessRating(rating_date=today, meal_type="breakfast", rating=5, department_id=dept.id if dept else None, submitter_hash="hash2"),
            MessRating(rating_date=today, meal_type="lunch", rating=3, department_id=dept.id if dept else None, submitter_hash="hash3"),
        ]
        db.add_all(ratings)

        # Seed Placement Drives
        drives = [
            PlacementDrive(
                company_name="Google",
                job_role="Software Engineer",
                package_lpa=30.0,
                drive_date=today + timedelta(days=14),
                registration_deadline=today + timedelta(days=7),
                description="Google is visiting campus for SDE roles.",
                created_by=admin.id if admin else None
            ),
            PlacementDrive(
                company_name="Microsoft",
                job_role="SDE 1",
                package_lpa=25.0,
                drive_date=today + timedelta(days=20),
                registration_deadline=today + timedelta(days=10),
                description="Microsoft campus hiring for 2026 batch.",
                created_by=admin.id if admin else None
            )
        ]
        db.add_all(drives)
        
        # Seed Placement Notices
        p_notices = [
            PlacementNotice(
                title="Google Drive Registration Open",
                body="Please register for the Google drive before the deadline.",
                created_by=admin.id if admin else None
            )
        ]
        db.add_all(p_notices)

        # Seed Wellbeing Checkins
        checkins = [
            WellbeingCheckin(
                week_start=today - timedelta(days=today.weekday()),
                department_id=dept.id if dept else None,
                year_of_study=3,
                mood=4,
                stress=2,
                sleep=4,
                note="Feeling good about the upcoming placements.",
                submitter_hash="wb_hash1"
            ),
            WellbeingCheckin(
                week_start=today - timedelta(days=today.weekday()),
                department_id=dept.id if dept else None,
                year_of_study=3,
                mood=2,
                stress=4,
                sleep=2,
                note="Too many assignments.",
                submitter_hash="wb_hash2"
            )
        ]
        db.add_all(checkins)

        await db.commit()
        print("Successfully seeded all dummy data.")

if __name__ == "__main__":
    asyncio.run(seed_data())
