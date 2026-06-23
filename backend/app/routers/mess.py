"""
Mess router — campus-wide mess schedule.

Read: any authenticated user.
Write (upload/confirm): SUPER_ADMIN, ACADEMIC_ADMIN, HOSTEL_ADMIN, MESS_ADMIN.
"""
import hashlib
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.models.mess import MessRating, MessSchedule
from app.models.user import UserProfile
from app.schemas.campus import (
    MealSentiment,
    MessConfirmRequest,
    MessRateRequest,
    MessScheduleOut,
    MessSentiment,
    MessTodayRatings,
    MessUploadResponse,
    SentimentTrendPoint,
)
from app.services.ocr import parse_mess_image, parse_time

router = APIRouter(prefix="/mess", tags=["mess"])
DB = Annotated[AsyncSession, Depends(get_db)]

MessWriteAny = Annotated[
    UserProfile,
    Depends(require_role("SUPER_ADMIN", "ACADEMIC_ADMIN", "HOSTEL_ADMIN", "MESS_ADMIN")),
]

WardenView = Annotated[
    UserProfile,
    Depends(require_role(
        "SUPER_ADMIN", "ACADEMIC_ADMIN", "HOSTEL_ADMIN", "HOSTEL_COORDINATOR", "MESS_ADMIN"
    )),
]

MEALS = ["breakfast", "lunch", "snacks", "dinner"]
LOW_RATING_THRESHOLD = 2.5   # avg below this is "low"
NUDGE_MIN_RATINGS = 5        # need at least this many ratings in the window to nudge

MEAL_ORDER = {"breakfast": 0, "lunch": 1, "snacks": 2, "dinner": 3}
DAY_ORDER = {
    "Daily": -1, "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}


@router.get("", response_model=list[MessScheduleOut], summary="Get the mess schedule")
async def get_mess(_user: CurrentUser, db: DB) -> list[MessScheduleOut]:
    result = await db.execute(select(MessSchedule))
    rows = result.scalars().all()
    rows = sorted(
        rows,
        key=lambda r: (DAY_ORDER.get(r.day_of_week, 99), MEAL_ORDER.get(r.meal_type, 99)),
    )
    return [MessScheduleOut.model_validate(r) for r in rows]


@router.post("/upload", response_model=MessUploadResponse, summary="Upload mess menu image (admin)")
async def upload_mess(
    _admin: MessWriteAny,
    db: DB,
    file: UploadFile = File(...),
) -> MessUploadResponse:
    if file.content_type not in ["image/jpeg", "image/png"]:
        return MessUploadResponse(
            success=False, message="Only JPEG and PNG images are allowed.",
            errors=["Unsupported file format"],
        )
    content = await file.read()
    if not content:
        return MessUploadResponse(success=False, message="Empty file", errors=["Empty file"])
    if len(content) > 10 * 1024 * 1024:
        return MessUploadResponse(success=False, message="File exceeds 10 MB", errors=["Too large"])

    result = await parse_mess_image(content)
    if not result["success"]:
        return MessUploadResponse(
            success=False, message="Failed to parse menu image.",
            extracted_text=result.get("extracted_text", ""),
            errors=result.get("errors", []),
        )

    entries = result.get("entries", [])
    return MessUploadResponse(
        success=True,
        message=f"Parsed {len(entries)} meal entries. Review and confirm to save.",
        extracted_text=result.get("extracted_text", ""),
        entries=entries,
        errors=result.get("errors", []),
    )


@router.post("/confirm", response_model=MessUploadResponse, summary="Save mess schedule (admin)")
async def confirm_mess(
    body: MessConfirmRequest,
    _admin: MessWriteAny,
    db: DB,
) -> MessUploadResponse:
    """Replace the entire mess schedule with the reviewed entries."""
    valid_meals = {"breakfast", "lunch", "snacks", "dinner"}
    valid_days = {
        "Daily", "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    }

    await db.execute(delete(MessSchedule))

    saved = 0
    skipped = 0
    for e in body.entries:
        meal = str(e.get("meal_type", "")).lower().strip()
        day = str(e.get("day_of_week", "Daily")).strip().capitalize()
        if day.lower() == "daily":
            day = "Daily"
        if meal not in valid_meals or day not in valid_days:
            skipped += 1
            continue
        items = str(e.get("items", "")).strip()
        start = e.get("start_time")
        end = e.get("end_time")
        db.add(
            MessSchedule(
                day_of_week=day,
                meal_type=meal,
                start_time=parse_time(start) if start else None,
                end_time=parse_time(end) if end else None,
                items=items,
                is_special=bool(e.get("is_special", False)),
            )
        )
        saved += 1

    await db.commit()
    msg = f"Saved {saved} meal entries."
    if skipped:
        msg += f" {skipped} skipped (invalid day/meal)."
    return MessUploadResponse(success=True, message=msg, entries=[])


# ── Mess sentiment loop (1-tap ratings) ──────────────────────────────────── #

def _rating_hash(user_id) -> str:
    secret = settings.SUPABASE_JWT_SECRET or "campusos"
    return hashlib.sha256(f"{user_id}:{secret}".encode()).hexdigest()


@router.post("/rate", response_model=MessTodayRatings, summary="One-tap rate today's meal")
async def rate_meal(
    body: MessRateRequest,
    current_user: CurrentUser,
    db: DB,
) -> MessTodayRatings:
    today = date.today()
    h = _rating_hash(current_user.id)

    existing = await db.execute(
        select(MessRating).where(
            MessRating.rating_date == today,
            MessRating.meal_type == body.meal_type,
            MessRating.submitter_hash == h,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.rating = body.rating  # re-tap updates
    else:
        db.add(
            MessRating(
                rating_date=today,
                meal_type=body.meal_type,
                rating=body.rating,
                department_id=current_user.department_id,
                submitter_hash=h,
            )
        )
    await db.commit()
    return await _today_ratings(current_user, db)


@router.get("/rate/today", response_model=MessTodayRatings, summary="My ratings for today")
async def my_today_ratings(current_user: CurrentUser, db: DB) -> MessTodayRatings:
    return await _today_ratings(current_user, db)


async def _today_ratings(current_user, db: AsyncSession) -> MessTodayRatings:
    today = date.today()
    h = _rating_hash(current_user.id)
    result = await db.execute(
        select(MessRating).where(
            MessRating.rating_date == today,
            MessRating.submitter_hash == h,
        )
    )
    ratings = {r.meal_type: r.rating for r in result.scalars().all()}
    return MessTodayRatings(rating_date=today, ratings=ratings)


def _meal_stats(rows: list[MessRating]) -> tuple[int, float, float, float]:
    n = len(rows)
    if n == 0:
        return 0, 0.0, 0.0, 0.0
    avg = round(sum(r.rating for r in rows) / n, 2)
    pos = round(sum(1 for r in rows if r.rating >= 4) / n * 100, 1)
    neg = round(sum(1 for r in rows if r.rating <= 2) / n * 100, 1)
    return n, avg, pos, neg


@router.get("/sentiment", response_model=MessSentiment, summary="Warden sentiment dashboard")
async def sentiment(_warden: WardenView, db: DB) -> MessSentiment:
    today = date.today()
    since = today - timedelta(days=6)

    result = await db.execute(
        select(MessRating).where(MessRating.rating_date >= since)
    )
    rows = list(result.scalars().all())

    today_rows = [r for r in rows if r.rating_date == today]

    # Per-meal sentiment (today)
    meals: list[MealSentiment] = []
    for meal in MEALS:
        mrows = [r for r in today_rows if r.meal_type == meal]
        n, avg, pos, neg = _meal_stats(mrows)
        meals.append(MealSentiment(meal_type=meal, count=n, avg=avg, positive_pct=pos, negative_pct=neg))

    t_n, t_avg, _, _ = _meal_stats(today_rows)

    # 7-day trend (overall avg per day)
    trend: list[SentimentTrendPoint] = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        drows = [r for r in rows if r.rating_date == d]
        n, avg, _, _ = _meal_stats(drows)
        trend.append(SentimentTrendPoint(day=d, count=n, avg=avg))

    # Automatic nudges — persistent low ratings over the last 3 days, per meal
    alerts: list[str] = []
    window_start = today - timedelta(days=2)
    for meal in MEALS:
        wrows = [r for r in rows if r.meal_type == meal and r.rating_date >= window_start]
        n, avg, _, neg = _meal_stats(wrows)
        if n >= NUDGE_MIN_RATINGS and avg and avg < LOW_RATING_THRESHOLD:
            alerts.append(
                f"⚠️ {meal.capitalize()} has averaged {avg}/5 over the last 3 days "
                f"({n} ratings, {neg}% negative). Time to review the {meal} menu."
            )
    # Today-specific strong negative signal
    for m in meals:
        if m.count >= NUDGE_MIN_RATINGS and m.negative_pct >= 60:
            alerts.append(
                f"🔴 {m.negative_pct}% of students disliked today's {m.meal_type}. "
                f"Consider an immediate menu change."
            )

    return MessSentiment(
        day=today,
        total=t_n,
        overall_avg=t_avg,
        meals=meals,
        trend=trend,
        alerts=alerts,
    )
