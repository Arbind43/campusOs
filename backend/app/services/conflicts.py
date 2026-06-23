"""
Schedule conflict detector.

Scans exams, the weekly timetable, and events to auto-flag:
  - exam room double-bookings (same date + room, overlapping time)
  - student exam overlaps (same department + semester, overlapping exams)
  - timetable room clashes (same day + room, overlapping time)
  - faculty clashes (same faculty, same day, overlapping time)
  - event venue clashes (same date + venue)

Exams store only a start time, so a fixed exam duration is assumed.
"""
from datetime import date, datetime, time, timedelta
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import Department, ExamSchedule, Timetable
from app.models.content import Event
from app.schemas.campus import ConflictScanResult, ScheduleConflict

EXAM_DURATION_MIN = 180  # assumed exam length when computing overlaps


def _end(t: time, minutes: int) -> time:
    return (datetime.combine(date.today(), t) + timedelta(minutes=minutes)).time()


def _overlaps(s1: time, e1: time, s2: time, e2: time) -> bool:
    return s1 < e2 and s2 < e1


def _fmt(t: time) -> str:
    try:
        return t.strftime("%I:%M %p").lstrip("0")
    except Exception:  # noqa: BLE001
        return str(t)


async def scan_conflicts(db: AsyncSession) -> ConflictScanResult:
    exams = list((await db.execute(select(ExamSchedule))).scalars().all())
    classes = list((await db.execute(select(Timetable))).scalars().all())
    events = list((await db.execute(select(Event))).scalars().all())
    depts = {d.id: d.code for d in (await db.execute(select(Department))).scalars().all()}

    conflicts: list[ScheduleConflict] = []

    # ── Exam room double-bookings ──────────────────────────────────────────
    room_groups: dict[tuple, list] = {}
    for e in exams:
        if e.room:
            room_groups.setdefault((e.exam_date, e.room.strip().lower()), []).append(e)
    for (d, _room), group in room_groups.items():
        for a, b in combinations(group, 2):
            ae, be = _end(a.start_time, EXAM_DURATION_MIN), _end(b.start_time, EXAM_DURATION_MIN)
            if _overlaps(a.start_time, ae, b.start_time, be):
                conflicts.append(ScheduleConflict(
                    type="exam_room",
                    severity="high",
                    title=f"Room {a.room} double-booked",
                    detail=f"{a.subject} ({_fmt(a.start_time)}) and {b.subject} ({_fmt(b.start_time)}) share room {a.room}.",
                    when=str(d),
                    items=[a.subject, b.subject],
                ))

    # ── Student exam overlaps (same dept + semester) ───────────────────────
    cohort_groups: dict[tuple, list] = {}
    for e in exams:
        cohort_groups.setdefault((e.exam_date, e.department_id, e.semester), []).append(e)
    for (d, dept_id, sem), group in cohort_groups.items():
        for a, b in combinations(group, 2):
            ae, be = _end(a.start_time, EXAM_DURATION_MIN), _end(b.start_time, EXAM_DURATION_MIN)
            if _overlaps(a.start_time, ae, b.start_time, be):
                code = depts.get(dept_id, "—")
                conflicts.append(ScheduleConflict(
                    type="exam_student_overlap",
                    severity="high",
                    title=f"{code} Sem {sem} exam overlap",
                    detail=f"Students sit {a.subject} and {b.subject} at the same time "
                           f"({_fmt(a.start_time)} / {_fmt(b.start_time)}).",
                    when=str(d),
                    items=[a.subject, b.subject],
                ))

    # ── Timetable room clashes ─────────────────────────────────────────────
    tt_room: dict[tuple, list] = {}
    for c in classes:
        if c.room:
            tt_room.setdefault((c.day_of_week, c.room.strip().lower()), []).append(c)
    for (day, _room), group in tt_room.items():
        for a, b in combinations(group, 2):
            if _overlaps(a.start_time, a.end_time, b.start_time, b.end_time):
                conflicts.append(ScheduleConflict(
                    type="class_room",
                    severity="medium",
                    title=f"Room {a.room} clash on {day}",
                    detail=f"{a.subject} ({_fmt(a.start_time)}–{_fmt(a.end_time)}) overlaps "
                           f"{b.subject} ({_fmt(b.start_time)}–{_fmt(b.end_time)}).",
                    when=day,
                    items=[a.subject, b.subject],
                ))

    # ── Faculty clashes ────────────────────────────────────────────────────
    tt_fac: dict[tuple, list] = {}
    for c in classes:
        if c.faculty_name:
            tt_fac.setdefault((c.day_of_week, c.faculty_name.strip().lower()), []).append(c)
    for (day, _fac), group in tt_fac.items():
        for a, b in combinations(group, 2):
            if _overlaps(a.start_time, a.end_time, b.start_time, b.end_time):
                conflicts.append(ScheduleConflict(
                    type="class_faculty",
                    severity="medium",
                    title=f"{a.faculty_name} double-booked on {day}",
                    detail=f"Teaching {a.subject} and {b.subject} at overlapping times "
                           f"({_fmt(a.start_time)} / {_fmt(b.start_time)}).",
                    when=day,
                    items=[a.subject, b.subject],
                ))

    # ── Event venue clashes ────────────────────────────────────────────────
    ev_groups: dict[tuple, list] = {}
    for e in events:
        if e.venue:
            ev_groups.setdefault((e.event_date, e.venue.strip().lower()), []).append(e)
    for (d, _venue), group in ev_groups.items():
        if len(group) > 1:
            titles = [e.title for e in group]
            conflicts.append(ScheduleConflict(
                type="event_venue",
                severity="low",
                title=f"Venue {group[0].venue} booked twice",
                detail="Multiple events booked the same venue: " + ", ".join(titles) + ".",
                when=str(d),
                items=titles,
            ))

    # Sort: high severity first
    order = {"high": 0, "medium": 1, "low": 2}
    conflicts.sort(key=lambda c: order.get(c.severity, 9))

    counts: dict[str, int] = {}
    for c in conflicts:
        counts[c.type] = counts.get(c.type, 0) + 1

    return ConflictScanResult(
        scanned_at=datetime.now(),
        total=len(conflicts),
        counts=counts,
        conflicts=conflicts,
    )
