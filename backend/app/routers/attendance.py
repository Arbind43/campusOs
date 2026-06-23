"""
Attendance router.

- Admins/Faculty list students by department + year and bulk-mark attendance.
- Students view their own attendance summary.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.models.attendance import AttendanceRecord
from app.models.user import UserProfile
from app.schemas.campus import (
    AttendanceMarkRequest,
    AttendanceMarkResponse,
    AttendancePrediction,
    AttendanceRecordOut,
    AttendanceSummaryOut,
    StudentBrief,
    SubjectPrediction,
)
from app.config import settings

router = APIRouter(prefix="/attendance", tags=["attendance"])
DB = Annotated[AsyncSession, Depends(get_db)]

AttendanceWrite = Annotated[
    UserProfile, Depends(require_role("SUPER_ADMIN", "ACADEMIC_ADMIN", "FACULTY"))
]


@router.get("/students", response_model=list[StudentBrief], summary="Roster for marking")
async def list_students(
    _admin: AttendanceWrite,
    db: DB,
    department_id: uuid.UUID,
    year_of_study: int | None = None,
) -> list[StudentBrief]:
    """List students in a department (optionally filtered by year) for the roster."""
    query = select(UserProfile).where(
        UserProfile.department_id == department_id,
        UserProfile.role == "STUDENT",
    )
    if year_of_study:
        query = query.where(UserProfile.year_of_study == year_of_study)
    query = query.order_by(UserProfile.full_name)
    result = await db.execute(query)
    return [StudentBrief.model_validate(s) for s in result.scalars().all()]


@router.post("/mark", response_model=AttendanceMarkResponse, summary="Bulk mark attendance")
async def mark_attendance(
    body: AttendanceMarkRequest,
    admin: AttendanceWrite,
    db: DB,
) -> AttendanceMarkResponse:
    """
    Upsert attendance for the given date + subject. Existing records for the same
    student/date/subject are updated; new ones are inserted.
    """
    saved = 0
    for item in body.records:
        existing = await db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == item.student_id,
                    AttendanceRecord.attend_date == body.attend_date,
                    AttendanceRecord.subject == body.subject,
                )
            )
        )
        record = existing.scalar_one_or_none()
        if record:
            record.status = item.status
            record.marked_by = admin.id
        else:
            db.add(
                AttendanceRecord(
                    student_id=item.student_id,
                    department_id=body.department_id,
                    year_of_study=body.year_of_study,
                    subject=body.subject,
                    attend_date=body.attend_date,
                    status=item.status,
                    marked_by=admin.id,
                )
            )
        saved += 1

    await db.commit()
    return AttendanceMarkResponse(
        success=True, message=f"Saved attendance for {saved} students.", saved=saved
    )


@router.get("/me", response_model=AttendanceSummaryOut, summary="My attendance summary")
async def my_attendance(current_user: CurrentUser, db: DB) -> AttendanceSummaryOut:
    result = await db.execute(
        select(AttendanceRecord)
        .where(AttendanceRecord.student_id == current_user.id)
        .order_by(AttendanceRecord.attend_date.desc())
    )
    records = list(result.scalars().all())
    present = sum(1 for r in records if r.status == "present")
    late = sum(1 for r in records if r.status == "late")
    absent = sum(1 for r in records if r.status == "absent")
    total = len(records)
    # Treat 'late' as attended for percentage purposes.
    attended = present + late
    percentage = round((attended / total) * 100, 1) if total else 0.0
    return AttendanceSummaryOut(
        total=total,
        present=present,
        absent=absent,
        late=late,
        percentage=percentage,
        records=[AttendanceRecordOut.model_validate(r) for r in records],
    )


@router.get(
    "/records",
    response_model=list[AttendanceRecordOut],
    summary="Records for a date + subject (admin)",
)
async def list_records(
    _admin: AttendanceWrite,
    db: DB,
    department_id: uuid.UUID,
    attend_date: str,
    subject: str = "General",
) -> list[AttendanceRecordOut]:
    query = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.department_id == department_id,
            AttendanceRecord.attend_date == attend_date,
            AttendanceRecord.subject == subject,
        )
        .order_by(AttendanceRecord.created_at)
    )
    result = await db.execute(query)
    return [AttendanceRecordOut.model_validate(r) for r in result.scalars().all()]


# ── Attendance Predictor AI ──────────────────────────────────────────────── #

def _predict_subject(subject: str, present: int, total: int, threshold: int) -> SubjectPrediction:
    """Compute risk + recovery guidance for a single subject (integer-exact math)."""
    pct = round((present / total) * 100, 1) if total else 0.0
    T = threshold

    if pct >= threshold:
        # max future classes that can be missed while staying >= threshold:
        # 100*present >= T*(total+k)  ->  k <= 100*present/T - total
        can_miss = max((100 * present) // T - total, 0) if T > 0 else 0
        must_attend = 0
        recoverable = True
    else:
        can_miss = 0
        # consecutive classes to attend to reach threshold:
        # (present+x)/(total+x) >= T/100  ->  x >= (T*total - 100*present)/(100 - T)
        if T >= 100:
            must_attend = -1
            recoverable = False
        else:
            num = T * total - 100 * present
            den = 100 - T
            must_attend = max(-(-num // den), 0)  # ceil division for positive num
            recoverable = True

    if pct < threshold:
        status = "critical"
        if must_attend > 0:
            msg = (f"Below the {threshold}% requirement. Attend the next "
                   f"{must_attend} {subject} class(es) in a row to recover.")
        else:
            msg = f"Below the {threshold}% requirement for {subject}."
    elif can_miss == 0:
        status = "warning"
        msg = f"Right on the edge — don't miss any more {subject} classes."
    elif pct < threshold + 5:
        status = "warning"
        msg = f"Close to the limit. You can miss only {can_miss} more {subject} class(es)."
    else:
        status = "safe"
        msg = f"You're safe — up to {can_miss} {subject} class(es) can still be missed."

    return SubjectPrediction(
        subject=subject,
        present=present,
        total=total,
        percentage=pct,
        status=status,
        can_miss=can_miss,
        must_attend=must_attend,
        recoverable=recoverable,
        message=msg,
    )


@router.get("/predict", response_model=AttendancePrediction, summary="Attendance risk prediction")
async def predict_attendance(current_user: CurrentUser, db: DB) -> AttendancePrediction:
    """Per-subject attendance risk analysis with early-warning + recovery guidance."""
    threshold = settings.ATTENDANCE_THRESHOLD

    result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.student_id == current_user.id)
    )
    records = list(result.scalars().all())

    by_subject: dict[str, dict] = {}
    for r in records:
        s = by_subject.setdefault(r.subject, {"present": 0, "total": 0})
        s["total"] += 1
        if r.status in ("present", "late"):
            s["present"] += 1

    subjects = [
        _predict_subject(name, v["present"], v["total"], threshold)
        for name, v in sorted(by_subject.items())
    ]

    total_present = sum(v["present"] for v in by_subject.values())
    total_all = sum(v["total"] for v in by_subject.values())
    overall_pct = round((total_present / total_all) * 100, 1) if total_all else 0.0

    at_risk = [s for s in subjects if s.status in ("warning", "critical")]
    critical = [s for s in subjects if s.status == "critical"]

    if not subjects:
        overall_status = "safe"
        summary = "No attendance recorded yet. Once classes are marked, I'll track your risk here."
    elif critical:
        overall_status = "critical"
        names = ", ".join(s.subject for s in critical)
        summary = f"⚠️ You're below {threshold}% in {names}. Act now to recover."
    elif at_risk:
        overall_status = "warning"
        names = ", ".join(s.subject for s in at_risk)
        summary = f"Heads up — {names} {'is' if len(at_risk) == 1 else 'are'} close to the {threshold}% limit."
    else:
        overall_status = "safe"
        summary = f"All subjects are comfortably above {threshold}%. Keep it up! 🎯"

    return AttendancePrediction(
        threshold=threshold,
        overall_percentage=overall_pct,
        overall_status=overall_status,
        at_risk_count=len(at_risk),
        subjects=subjects,
        summary=summary,
    )
