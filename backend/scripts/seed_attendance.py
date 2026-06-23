"""
Seed sample attendance data into `attendance_marks` for all students.

Creates a realistic mix per student so the Attendance Predictor shows
safe / warning / critical cases (threshold = 80%):

  - Data Structures   19/22  (~86%)  -> safe
  - Mathematics       16/20  (80%)   -> warning (on the edge)
  - Operating Systems 13/20  (65%)   -> critical (recovery needed)
  - Web Development    17/22  (~77%) -> critical

Existing marks for each seeded student are cleared first so it is re-runnable.

Run:  venv\\Scripts\\python.exe -m scripts.seed_attendance
"""
import asyncio
from datetime import date, timedelta

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models.attendance import AttendanceRecord
from app.models.academic import Timetable
from app.models.user import UserProfile

# (subject_fallback, present, total)
SUBJECT_TARGETS = [
    ("Data Structures", 19, 22),
    ("Mathematics", 16, 20),
    ("Operating Systems", 13, 20),
    ("Web Development", 17, 22),
]


def weekdays_back(n: int) -> list[date]:
    """Return the most recent `n` weekdays (Mon–Fri), oldest first."""
    days: list[date] = []
    d = date.today()
    while len(days) < n:
        if d.weekday() < 5:  # 0=Mon .. 4=Fri
            days.append(d)
        d -= timedelta(days=1)
    return list(reversed(days))


async def subjects_for(session, student: UserProfile) -> list[str]:
    """Return 4 distinct subjects: department timetable subjects, padded with defaults."""
    chosen: list[str] = []
    if student.department_id:
        res = await session.execute(
            select(Timetable.subject)
            .where(Timetable.department_id == student.department_id)
            .distinct()
        )
        chosen = [s for s in res.scalars().all() if s][:4]

    # Pad with default names not already present, to reach 4 distinct subjects
    for name, _, _ in SUBJECT_TARGETS:
        if len(chosen) >= 4:
            break
        if name not in chosen:
            chosen.append(name)
    return chosen[:4]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.role == "STUDENT")
        )
        students = list(result.scalars().all())
        if not students:
            print("No STUDENT users found. Create/assign students first (User Management).")
            return

        total_rows = 0
        for student in students:
            # Clean reseed for this student
            await session.execute(
                delete(AttendanceRecord).where(AttendanceRecord.student_id == student.id)
            )

            subject_names = await subjects_for(session, student)
            # Pair chosen subject names with target ratios (cycle if fewer names)
            for i, (_, present, total) in enumerate(SUBJECT_TARGETS):
                subject = subject_names[i % len(subject_names)]
                dates = weekdays_back(total)
                absent_count = total - present
                # Spread absences evenly across the period
                absent_idx = set(
                    round(j * (total - 1) / max(absent_count - 1, 1))
                    for j in range(absent_count)
                ) if absent_count > 0 else set()

                for idx, d in enumerate(dates):
                    status = "absent" if idx in absent_idx else "present"
                    session.add(
                        AttendanceRecord(
                            student_id=student.id,
                            department_id=student.department_id,
                            year_of_study=student.year_of_study,
                            subject=subject,
                            attend_date=d,
                            status=status,
                        )
                    )
                    total_rows += 1

            print(f"  seeded {student.email} ({', '.join(subject_names[:4])})")

        await session.commit()
        print(f"\nDone. Inserted {total_rows} attendance rows for {len(students)} student(s).")


if __name__ == "__main__":
    asyncio.run(main())
