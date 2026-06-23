"""
Wellbeing check-in router.

- Students submit an anonymous weekly 3-question mood check-in.
- Counsellors / admins see aggregate insights with pattern detection
  (e.g. stress spikes that line up with upcoming exams).

Privacy: submissions store no user id. A one-way hash prevents duplicate
weekly submissions. Cohort breakdowns are hidden below `MIN_COHORT` responses.
"""
import hashlib
from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.models.academic import Department, ExamSchedule
from app.models.user import UserProfile
from app.models.wellbeing import WellbeingCheckin
from app.schemas.campus import (
    WellbeingCheckinCreate,
    WellbeingDeptStat,
    WellbeingInsights,
    WellbeingStatus,
    WellbeingWeekPoint,
)

router = APIRouter(prefix="/wellbeing", tags=["wellbeing"])
DB = Annotated[AsyncSession, Depends(get_db)]

CounsellorView = Annotated[
    UserProfile,
    Depends(require_role("SUPER_ADMIN", "ACADEMIC_ADMIN", "COUNSELLOR", "WELLBEING_ADMIN")),
]

MIN_COHORT = 3  # minimum responses before a cohort's stats are shown


def _current_week_start(d: date | None = None) -> date:
    d = d or date.today()
    return d - timedelta(days=d.weekday())  # Monday


def _submitter_hash(user_id, week_start: date) -> str:
    secret = settings.SUPABASE_JWT_SECRET or "campusos"
    raw = f"{user_id}:{week_start.isoformat()}:{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


@router.get("/status", response_model=WellbeingStatus, summary="Has the student checked in this week?")
async def checkin_status(current_user: CurrentUser, db: DB) -> WellbeingStatus:
    week = _current_week_start()
    h = _submitter_hash(current_user.id, week)
    result = await db.execute(
        select(WellbeingCheckin).where(
            WellbeingCheckin.week_start == week,
            WellbeingCheckin.submitter_hash == h,
        )
    )
    return WellbeingStatus(submitted=result.scalar_one_or_none() is not None, week_start=week)


@router.post("/checkin", response_model=WellbeingStatus, status_code=status.HTTP_201_CREATED)
async def submit_checkin(
    body: WellbeingCheckinCreate,
    current_user: CurrentUser,
    db: DB,
) -> WellbeingStatus:
    week = _current_week_start()
    h = _submitter_hash(current_user.id, week)

    existing = await db.execute(
        select(WellbeingCheckin).where(
            WellbeingCheckin.week_start == week,
            WellbeingCheckin.submitter_hash == h,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You've already checked in this week.")

    db.add(
        WellbeingCheckin(
            week_start=week,
            department_id=current_user.department_id,
            year_of_study=current_user.year_of_study,
            mood=body.mood,
            stress=body.stress,
            sleep=body.sleep,
            note=body.note,
            submitter_hash=h,
        )
    )
    await db.commit()
    return WellbeingStatus(submitted=True, week_start=week)


def _stats(rows: list[WellbeingCheckin]) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0, "mood": 0.0, "stress": 0.0, "sleep": 0.0, "high_stress": 0.0, "low_mood": 0.0}
    return {
        "n": n,
        "mood": round(sum(r.mood for r in rows) / n, 2),
        "stress": round(sum(r.stress for r in rows) / n, 2),
        "sleep": round(sum(r.sleep for r in rows) / n, 2),
        "high_stress": round(sum(1 for r in rows if r.stress >= 4) / n * 100, 1),
        "low_mood": round(sum(1 for r in rows if r.mood <= 2) / n * 100, 1),
    }


@router.get("/insights", response_model=WellbeingInsights, summary="Counsellor insights")
async def insights(_counsellor: CounsellorView, db: DB) -> WellbeingInsights:
    today = date.today()
    this_week = _current_week_start(today)
    last_week = this_week - timedelta(days=7)
    since = this_week - timedelta(days=28)

    result = await db.execute(
        select(WellbeingCheckin).where(WellbeingCheckin.week_start >= since)
    )
    all_rows = list(result.scalars().all())

    by_week: dict[date, list[WellbeingCheckin]] = {}
    for r in all_rows:
        by_week.setdefault(r.week_start, []).append(r)

    cur_rows = by_week.get(this_week, [])
    prev_rows = by_week.get(last_week, [])
    cur = _stats(cur_rows)
    prev = _stats(prev_rows)

    # Department breakdown (current week, only cohorts >= MIN_COHORT)
    dept_groups: dict = {}
    for r in cur_rows:
        dept_groups.setdefault(r.department_id, []).append(r)
    dept_stats: list[WellbeingDeptStat] = []
    if cur_rows:
        # resolve department names
        dept_ids = [d for d in dept_groups if d is not None]
        names: dict = {}
        if dept_ids:
            dres = await db.execute(select(Department).where(Department.id.in_(dept_ids)))
            names = {d.id: d.name for d in dres.scalars().all()}
        for dept_id, rows in dept_groups.items():
            if len(rows) < MIN_COHORT:
                continue
            s = _stats(rows)
            dept_stats.append(
                WellbeingDeptStat(
                    department=names.get(dept_id, "Unspecified"),
                    responses=s["n"],
                    avg_stress=s["stress"],
                    high_stress_pct=s["high_stress"],
                )
            )
        dept_stats.sort(key=lambda x: x.high_stress_pct, reverse=True)

    # Trend (last 4 weeks)
    trend: list[WellbeingWeekPoint] = []
    for i in range(3, -1, -1):
        wk = this_week - timedelta(days=7 * i)
        s = _stats(by_week.get(wk, []))
        trend.append(
            WellbeingWeekPoint(
                week_start=wk, responses=s["n"], avg_mood=s["mood"],
                avg_stress=s["stress"], avg_sleep=s["sleep"], high_stress_pct=s["high_stress"],
            )
        )

    # Upcoming exams in the next 14 days (campus-wide signal)
    exam_res = await db.execute(
        select(ExamSchedule).where(
            ExamSchedule.exam_date >= today,
            ExamSchedule.exam_date <= today + timedelta(days=14),
        )
    )
    exams_soon = len(list(exam_res.scalars().all()))

    # Status + insight
    high = cur["high_stress"]
    if cur["n"] == 0:
        statusv = "calm"
    elif high >= 50 or cur["stress"] >= 3.8:
        statusv = "elevated"
    elif high >= 30:
        statusv = "watch"
    else:
        statusv = "calm"

    insight_parts: list[str] = []
    if cur["n"] == 0:
        insight_parts.append("No check-ins yet this week. Encourage students to share how they're doing.")
    else:
        insight_parts.append(
            f"{cur['n']} check-in(s) this week — average mood {cur['mood']}/5, "
            f"stress {cur['stress']}/5, sleep {cur['sleep']}/5."
        )
        delta = round(high - prev["high_stress"], 1) if prev["n"] else None
        if delta is not None and delta >= 15:
            line = f"High-stress reports jumped {delta:+} pts vs last week ({prev['high_stress']}% → {high}%)."
            if exams_soon:
                line += f" This lines up with {exams_soon} exam(s) in the next two weeks — likely exam pressure."
            insight_parts.append("⚠️ " + line)
        elif high >= 50:
            insight_parts.append(f"⚠️ {high}% of respondents report high stress this week.")
        if cur["low_mood"] >= 40:
            insight_parts.append(f"{cur['low_mood']}% reported low mood.")
        if cur["sleep"] and cur["sleep"] <= 2.5:
            insight_parts.append("Sleep quality is low across respondents.")
        hotspots = [d.department for d in dept_stats if d.high_stress_pct >= 50]
        if hotspots:
            insight_parts.append("Hotspots: " + ", ".join(hotspots) + ".")

    recommendations: list[str] = []
    if statusv == "elevated":
        recommendations.append("Open extra counselling slots this week.")
        if exams_soon:
            recommendations.append("Share exam stress-management resources and study-break tips.")
        recommendations.append("Consider a short wellbeing session or relaxation activity.")
    elif statusv == "watch":
        recommendations.append("Monitor closely and send a supportive check-in message.")
    else:
        recommendations.append("Wellbeing looks stable — keep the weekly check-in going.")

    return WellbeingInsights(
        week_start=this_week,
        responses=cur["n"],
        avg_mood=cur["mood"],
        avg_stress=cur["stress"],
        avg_sleep=cur["sleep"],
        high_stress_pct=cur["high_stress"],
        low_mood_pct=cur["low_mood"],
        status=statusv,
        insight=" ".join(insight_parts),
        recommendations=recommendations,
        departments=dept_stats,
        trend=trend,
        min_cohort=MIN_COHORT,
    )
