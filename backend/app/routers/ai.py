"""
AI router — intelligent campus assistant chatbot for students.

Aggregates the student's live data (timetable, attendance, notices, mess,
exams, assignments, events) and answers natural-language questions.

Uses Groq (llama-3.3-70b) when GROQ_API_KEY is set; otherwise falls back to an
intent-aware offline responder so the demo works without any API key.
"""
import os
import re
from datetime import date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.academic import ExamSchedule, Timetable
from app.models.attendance import AttendanceRecord
from app.models.chat import ChatMessage
from app.models.content import Assignment, Event, Notice
from app.models.mess import MessSchedule
from app.models.placement import PlacementDrive, PlacementNotice
from app.schemas.campus import (
    AIQueryRequest,
    AIQueryResponse,
    ChatMessageOut,
    DigestClass,
    DigestItem,
    DigestResponse,
)

router = APIRouter(prefix="/ai", tags=["ai"])
DB = Annotated[AsyncSession, Depends(get_db)]

# How many recent messages to feed back into the model for context.
HISTORY_TURNS = 10

MEAL_ORDER = {"breakfast": 0, "lunch": 1, "snacks": 2, "dinner": 3}
DAY_ORDER = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}


def _fmt_time(t) -> str:
    try:
        return t.strftime("%I:%M %p").lstrip("0")
    except Exception:  # noqa: BLE001
        return str(t)


async def _gather_context(current_user, db: AsyncSession) -> dict:
    """Collect all student-relevant data into a structured dict."""
    today = date.today()
    today_name = today.strftime("%A")
    next_week = today + timedelta(days=7)
    ctx: dict = {
        "name": current_user.full_name,
        "today_name": today_name,
        "today_classes": [],
        "week_timetable": {},
        "attendance": None,
        "mess": [],
        "notices": [],
        "exams": [],
        "assignments": [],
        "events": [],
        "placements": [],
        "placement_notices": [],
    }

    # ── Timetable (full week + today) ──────────────────────────────────────
    if current_user.department_id:
        tt = await db.execute(
            select(Timetable)
            .where(Timetable.department_id == current_user.department_id)
            .order_by(Timetable.start_time)
        )
        for c in tt.scalars().all():
            entry = {
                "subject": c.subject,
                "start": _fmt_time(c.start_time),
                "end": _fmt_time(c.end_time),
                "room": c.room,
                "faculty": c.faculty_name,
                "day": c.day_of_week,
            }
            ctx["week_timetable"].setdefault(c.day_of_week, []).append(entry)
            if c.day_of_week == today_name:
                ctx["today_classes"].append(entry)

    # ── Attendance summary (from per-day marks) ────────────────────────────
    att = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.student_id == current_user.id)
    )
    records = list(att.scalars().all())
    if records:
        present = sum(1 for r in records if r.status in ("present", "late"))
        total = len(records)
        pct = round((present / total) * 100, 1) if total else 0.0
        # per-subject
        by_subject: dict[str, dict] = {}
        for r in records:
            s = by_subject.setdefault(r.subject, {"present": 0, "total": 0})
            s["total"] += 1
            if r.status in ("present", "late"):
                s["present"] += 1
        ctx["attendance"] = {
            "present": present,
            "total": total,
            "percentage": pct,
            "by_subject": {
                k: round((v["present"] / v["total"]) * 100, 1)
                for k, v in by_subject.items()
            },
        }

    # ── Mess schedule ──────────────────────────────────────────────────────
    mess = await db.execute(select(MessSchedule))
    mess_rows = sorted(
        mess.scalars().all(),
        key=lambda r: (DAY_ORDER.get(r.day_of_week, -1), MEAL_ORDER.get(r.meal_type, 99)),
    )
    for m in mess_rows:
        ctx["mess"].append({
            "day": m.day_of_week,
            "meal": m.meal_type,
            "start": _fmt_time(m.start_time) if m.start_time else None,
            "end": _fmt_time(m.end_time) if m.end_time else None,
            "items": m.items,
            "special": m.is_special,
        })

    # ── Notices (filtered by dept + year) ─────────────────────────────────
    nq = select(Notice).order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).limit(8)
    if current_user.department_id:
        nq = nq.where(
            (Notice.target_department_id == current_user.department_id)
            | (Notice.target_department_id.is_(None))
        )
    if current_user.year_of_study:
        nq = nq.where(
            (Notice.target_year == current_user.year_of_study)
            | (Notice.target_year.is_(None))
        )
    notices = await db.execute(nq)
    for n in notices.scalars().all():
        ctx["notices"].append({"title": n.title, "body": n.body, "pinned": n.is_pinned})

    # ── Exams & assignments ────────────────────────────────────────────────
    if current_user.department_id:
        ex = await db.execute(
            select(ExamSchedule)
            .where(
                ExamSchedule.department_id == current_user.department_id,
                ExamSchedule.exam_date >= today,
                ExamSchedule.exam_date <= next_week,
            )
            .order_by(ExamSchedule.exam_date)
            .limit(5)
        )
        for e in ex.scalars().all():
            ctx["exams"].append({
                "subject": e.subject,
                "date": e.exam_date.isoformat(),
                "time": _fmt_time(e.start_time),
                "room": e.room,
            })

        asg = await db.execute(
            select(Assignment)
            .where(
                Assignment.department_id == current_user.department_id,
                Assignment.due_date >= today,
                Assignment.due_date <= next_week,
            )
            .order_by(Assignment.due_date)
            .limit(5)
        )
        for a in asg.scalars().all():
            ctx["assignments"].append({
                "title": a.title,
                "subject": a.subject,
                "due": a.due_date.isoformat(),
            })

    # ── Events ─────────────────────────────────────────────────────────────
    ev = await db.execute(
        select(Event)
        .where(Event.event_date >= today, Event.event_date <= next_week)
        .order_by(Event.event_date)
        .limit(5)
    )
    for e in ev.scalars().all():
        ctx["events"].append({"title": e.title, "date": e.event_date.isoformat()})

    # ── Placement drives (active) + placement notices/resources ────────────
    pd = await db.execute(
        select(PlacementDrive)
        .where(PlacementDrive.is_active == True)  # noqa: E712
        .order_by(PlacementDrive.registration_deadline.asc().nullslast())
        .limit(10)
    )
    for d in pd.scalars().all():
        ctx["placements"].append({
            "company": d.company_name,
            "role": d.job_role,
            "package": float(d.package_lpa) if d.package_lpa is not None else None,
            "drive_date": d.drive_date.isoformat() if d.drive_date else None,
            "deadline": d.registration_deadline.isoformat() if d.registration_deadline else None,
            "description": d.description or "",
        })

    pn = await db.execute(
        select(PlacementNotice).order_by(PlacementNotice.created_at.desc()).limit(8)
    )
    for n in pn.scalars().all():
        ctx["placement_notices"].append({"title": n.title, "body": n.body})

    return ctx


def _context_to_text(ctx: dict) -> str:
    """Render context as a compact text block for the LLM prompt."""
    lines: list[str] = [f"Student: {ctx['name']} | Today: {ctx['today_name']}"]

    if ctx["today_classes"]:
        cls = "; ".join(
            f"{c['subject']} {c['start']}-{c['end']} ({c['room'] or 'TBD'})"
            for c in ctx["today_classes"]
        )
        lines.append(f"Today's classes: {cls}")
    else:
        lines.append("Today's classes: none scheduled")

    if ctx["week_timetable"]:
        for day in sorted(ctx["week_timetable"], key=lambda d: DAY_ORDER.get(d, 9)):
            cls = "; ".join(f"{c['subject']} {c['start']}-{c['end']}" for c in ctx["week_timetable"][day])
            lines.append(f"{day}: {cls}")

    if ctx["attendance"]:
        a = ctx["attendance"]
        lines.append(f"Attendance: {a['percentage']}% ({a['present']}/{a['total']} attended)")
        if a["by_subject"]:
            subj = ", ".join(f"{k}: {v}%" for k, v in a["by_subject"].items())
            lines.append(f"Attendance by subject: {subj}")

    if ctx["mess"]:
        for m in ctx["mess"]:
            t = f" [{m['start']}-{m['end']}]" if m["start"] else ""
            lines.append(f"Mess {m['day']} {m['meal']}{t}: {m['items']}")

    for n in ctx["notices"]:
        pin = "PINNED " if n["pinned"] else ""
        lines.append(f"Notice: {pin}{n['title']} — {n['body'][:120]}")

    for e in ctx["exams"]:
        lines.append(f"Exam: {e['subject']} on {e['date']} at {e['time']} ({e['room'] or 'TBD'})")
    for a in ctx["assignments"]:
        lines.append(f"Assignment: {a['title']} ({a['subject']}) due {a['due']}")
    for e in ctx["events"]:
        lines.append(f"Event: {e['title']} on {e['date']}")

    for p in ctx["placements"]:
        pkg = f", {p['package']} LPA" if p["package"] is not None else ""
        dl = f", apply by {p['deadline']}" if p["deadline"] else ""
        dd = f", drive on {p['drive_date']}" if p["drive_date"] else ""
        desc = f" — {p['description'][:100]}" if p["description"] else ""
        lines.append(f"Placement: {p['company']} ({p['role']}{pkg}){dd}{dl}{desc}")
    for n in ctx["placement_notices"]:
        lines.append(f"Placement info: {n['title']} — {n['body'][:120]}")

    return "\n".join(lines)


def _build_prompt(ctx: dict, user_message: str, history: list[dict]) -> str:
    history_text = ""
    if history:
        turns = "\n".join(
            f"{'Student' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
            for h in history
        )
        history_text = f"\nRECENT CONVERSATION (for context, resolve follow-ups like 'what about tomorrow'):\n{turns}\n"

    return f"""You are CampusOS AI, a friendly, concise campus assistant for {ctx['name']}.
Answer ONLY using the student's data below. If the data doesn't contain the answer, say so honestly.
Use the recent conversation to understand follow-up questions and pronouns.

STUDENT DATA:
{_context_to_text(ctx)}
{history_text}
ATTENDANCE RULE: The minimum required attendance is {settings.ATTENDANCE_THRESHOLD}% and the
critical floor is {settings.CRITICAL_ATTENDANCE_FLOOR}%. If the student asks whether they can
miss/skip/bunk a class, estimate the impact and advise clearly (safe to skip, or risky).

Current question: "{user_message}"

Reply in a warm, helpful tone. Be specific (real subjects, times, dishes, dates). Keep it under 180 words."""


async def _call_llm(prompt: str, ctx: dict, message: str, history: list[dict]) -> str:
    """Generate a reply with Groq's chat API; fall back to offline logic without a key."""
    api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return _offline_answer(ctx, message, history)
    try:
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are CampusOS AI, a friendly, concise campus assistant. "
                    "Answer only from the data provided in the user message. Keep replies under 180 words.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 500,
        }
        async with httpx.AsyncClient(timeout=settings.AI_ASSISTANT_LLM_TIMEOUT or 15) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            text = (resp.json()["choices"][0]["message"]["content"] or "").strip()
        return text or _offline_answer(ctx, message, history)
    except Exception:  # noqa: BLE001
        return _offline_answer(ctx, message, history)


def _offline_answer(ctx: dict, message: str, history: list[dict] | None = None) -> str:
    """Intent-aware responder used when no LLM key is configured."""
    msg = message.lower()
    history = history or []

    def has(*words: str) -> bool:
        return any(w in msg for w in words)

    # ── Follow-up resolution ──────────────────────────────────────────────
    # If the message is a short follow-up with no clear topic of its own
    # (e.g. "what about tomorrow?", "and lunch?"), inherit the topic from the
    # most recent user question so context isn't lost.
    KNOWN_TOPICS = (
        "miss", "skip", "bunk", "mess", "food", "lunch", "dinner", "breakfast",
        "snacks", "menu", "eat", "canteen", "attendance", "present", "absent",
        "schedule", "timetable", "class", "lecture", "notice", "announce",
        "exam", "test", "assignment", "homework", "due",
        "placement", "placements", "drive", "company", "companies", "job",
        "package", "lpa", "recruit", "internship", "career", "prep", "interview",
    )
    if not has(*KNOWN_TOPICS):
        last_user = next(
            (h["content"].lower() for h in reversed(history) if h["role"] == "user"),
            "",
        )
        if last_user:
            # Carry over the previous topic keywords into this message's intent.
            inherited = " ".join(w for w in KNOWN_TOPICS if w in last_user)
            if inherited:
                msg = f"{msg} {inherited}"

                def has(*words: str) -> bool:  # noqa: F811 — rebind with enriched msg
                    return any(w in msg for w in words)

    # ── Can I miss / skip / bunk a class? ─────────────────────────────────
    if has("miss", "skip", "bunk", "leave the class", "not attend"):
        a = ctx["attendance"]
        if not a or a["total"] == 0:
            return ("I don't have any attendance records for you yet, so I can't estimate the "
                    "impact of missing a class. Once attendance is marked, ask me again!")
        threshold = settings.ATTENDANCE_THRESHOLD
        present, total = a["present"], a["total"]
        projected = round((present / (total + 1)) * 100, 1)
        cur = a["percentage"]
        if projected >= threshold:
            return (f"📊 Your attendance is **{cur}%** ({present}/{total}). If you miss one more "
                    f"class it drops to about **{projected}%**, still above the {threshold}% "
                    f"requirement. You can afford to miss it — but don't make it a habit! 🙂")
        return (f"⚠️ Your attendance is **{cur}%** ({present}/{total}). Missing one more class "
                f"would bring it to about **{projected}%**, below the {threshold}% requirement. "
                f"I'd recommend attending this one.")

    # ── Mess / food ───────────────────────────────────────────────────────
    if has("mess", "food", "lunch", "dinner", "breakfast", "snacks", "menu", "eat", "canteen"):
        if not ctx["mess"]:
            return "The mess menu hasn't been uploaded yet. Please check back once the admin adds it. 🍽️"
        # specific meal?
        for meal in ("breakfast", "lunch", "snacks", "dinner"):
            if meal in msg:
                rows = [m for m in ctx["mess"] if m["meal"] == meal]
                if rows:
                    m = rows[0]
                    t = f" ({m['start']}–{m['end']})" if m["start"] else ""
                    return f"🍽️ **{meal.capitalize()}**{t}: {m['items']}"
        lines = []
        for m in ctx["mess"][:8]:
            t = f" {m['start']}–{m['end']}" if m["start"] else ""
            lines.append(f"• **{m['meal'].capitalize()}**{t}: {m['items']}")
        return "🍽️ **Mess menu:**\n" + "\n".join(lines)

    # ── Attendance ─────────────────────────────────────────────────────────
    if has("attendance", "present", "absent", "percentage", "risk", "predict"):
        a = ctx["attendance"]
        if not a:
            return "You have no attendance records yet. 📋"
        threshold = settings.ATTENDANCE_THRESHOLD
        out = f"📊 Your overall attendance is **{a['percentage']}%** ({a['present']}/{a['total']} classes attended)."
        if a["by_subject"]:
            out += "\n\nBy subject:\n" + "\n".join(
                f"• {k}: {v}%" + (" ⚠️ at risk" if v < threshold else "")
                for k, v in a["by_subject"].items()
            )
            at_risk = [k for k, v in a["by_subject"].items() if v < threshold]
            if at_risk:
                out += (f"\n\n⚠️ You're below the {threshold}% requirement in "
                        f"{', '.join(at_risk)}. Attend the next few classes to recover — "
                        f"check the Attendance page for an exact recovery plan.")
            else:
                out += f"\n\n✅ All subjects are above the {threshold}% requirement. Nice work!"
        return out

    # ── Schedule / timetable ────────────────────────────────────────────────
    if has("schedule", "timetable", "class", "today", "tomorrow", "next class", "lecture"):
        if "tomorrow" in msg:
            tmr = (date.today() + timedelta(days=1)).strftime("%A")
            rows = ctx["week_timetable"].get(tmr, [])
            if not rows:
                return f"🎉 You have no classes scheduled for {tmr}!"
            lines = [f"• {c['subject']} {c['start']}–{c['end']} ({c['room'] or 'TBD'})" for c in rows]
            return f"📅 **{tmr}'s classes:**\n" + "\n".join(lines)
        rows = ctx["today_classes"]
        if not rows:
            return f"🎉 No classes scheduled for today ({ctx['today_name']}). Enjoy your day!"
        lines = [f"• {c['subject']} {c['start']}–{c['end']} ({c['room'] or 'TBD'})" for c in rows]
        return f"📅 **Today's classes ({ctx['today_name']}):**\n" + "\n".join(lines)

    # ── Notices ──────────────────────────────────────────────────────────────
    if has("notice", "announce", "news", "update"):
        if not ctx["notices"]:
            return "No notices for you right now. 📭"
        lines = [f"• {'📌 ' if n['pinned'] else ''}{n['title']}: {n['body'][:100]}" for n in ctx["notices"][:5]]
        return "📢 **Latest notices:**\n" + "\n".join(lines)

    # ── Placement (drives + prep resources) ─────────────────────────────────
    if has("placement", "drive", "company", "companies", "job", "package", "lpa",
           "recruit", "internship", "career", "interview", "prep"):
        drives = ctx["placements"]
        notes = ctx["placement_notices"]
        if not drives and not notes:
            return "No placement drives or resources have been posted yet. 💼"
        out: list[str] = []
        if drives:
            out.append("💼 **Placement drives:**")
            for d in drives[:6]:
                pkg = f" — {d['package']} LPA" if d["package"] is not None else ""
                dl = f" (apply by {d['deadline']})" if d["deadline"] else ""
                out.append(f"• {d['company']} — {d['role']}{pkg}{dl}")
        if notes:
            if out:
                out.append("")
            out.append("📌 **Placement info & prep:**")
            for n in notes[:5]:
                out.append(f"• {n['title']}: {n['body'][:100]}")
        return "\n".join(out)

    # ── Exams / assignments ──────────────────────────────────────────────────
    if has("exam", "test"):
        if not ctx["exams"]:
            return "No exams scheduled in the next week. 📚"
        lines = [f"• {e['subject']} on {e['date']} at {e['time']} ({e['room'] or 'TBD'})" for e in ctx["exams"]]
        return "📝 **Upcoming exams:**\n" + "\n".join(lines)
    if has("assignment", "homework", "due", "submit"):
        if not ctx["assignments"]:
            return "No assignments due in the next week. ✅"
        lines = [f"• {a['title']} ({a['subject']}) due {a['due']}" for a in ctx["assignments"]]
        return "📑 **Upcoming assignments:**\n" + "\n".join(lines)

    # ── Default: brief overview ──────────────────────────────────────────────
    parts = [f"👋 Hi {ctx['name'].split(' ')[0]}! Here's a quick overview:"]
    if ctx["today_classes"]:
        parts.append(f"📅 {len(ctx['today_classes'])} class(es) today — first: {ctx['today_classes'][0]['subject']} at {ctx['today_classes'][0]['start']}.")
    if ctx["attendance"]:
        parts.append(f"📊 Attendance: {ctx['attendance']['percentage']}%.")
    if ctx["mess"]:
        nxt = ctx["mess"][0]
        parts.append(f"🍽️ Mess {nxt['meal']}: {nxt['items'][:50]}.")
    if ctx["notices"]:
        parts.append(f"📢 {len(ctx['notices'])} notice(s) for you.")
    if ctx["placements"]:
        parts.append(f"💼 {len(ctx['placements'])} placement drive(s) open.")
    parts.append('\nAsk me about your schedule, mess menu, attendance, notices, placements, or "can I miss my next class?"')
    return "\n".join(parts)


# ── Admin agentic actions (CRUD via chat) ─────────────────────────────────── #

ADMIN_ROLES = {"ACADEMIC_ADMIN", "SUPER_ADMIN"}
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _is_admin(user) -> bool:
    return user.role in ADMIN_ROLES


def _find_day(msg: str) -> str | None:
    for d in DAY_NAMES:
        if d.lower() in msg:
            return d
    if "tomorrow" in msg:
        return (date.today() + timedelta(days=1)).strftime("%A")
    if "today" in msg:
        return date.today().strftime("%A")
    return None


def _parse_time_phrase(msg: str) -> time | None:
    """Parse the first time mention, e.g. '7 pm', '7:30pm', '14:00', '9 am'."""
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", msg)
    if m:
        hour = int(m.group(1)) % 12
        minute = int(m.group(2) or 0)
        if m.group(3) == "pm":
            hour += 12
        return time(hour=min(hour, 23), minute=min(minute, 59))
    m = re.search(r"\b(\d{1,2}):(\d{2})\b", msg)
    if m:
        return time(hour=min(int(m.group(1)), 23), minute=min(int(m.group(2)), 59))
    return None


def _add_hour(t: time) -> time:
    total = (t.hour * 60 + t.minute + 60) % (24 * 60)
    return time(hour=total // 60, minute=total % 60)


async def _try_admin_action(message: str, user, db: AsyncSession) -> str | None:
    """
    If the (admin) message is a CRUD command, perform it and return a
    confirmation string. Otherwise return None so normal Q&A runs.
    """
    if not _is_admin(user):
        return None

    msg = message.lower().strip()

    def has(*words: str) -> bool:
        return any(w in msg for w in words)

    add_verbs = has("add", "create", "put", "schedule", "post", "make", "announce", "set up")
    del_verbs = has("cancel", "remove", "delete", "drop")

    # ── Cancel / delete a class ───────────────────────────────────────────
    if del_verbs and has("class", "lecture", "period"):
        m = re.search(r"(?:cancel|remove|delete|drop)\s+(?:the\s+)?(.+?)\s+(?:class|lecture)", msg)
        subject = m.group(1).strip() if m else None
        day = _find_day(msg)
        if not subject:
            return "Which class should I cancel? Try: \"cancel Bengali class on Monday\"."
        q = select(Timetable).where(Timetable.subject.ilike(f"%{subject}%"))
        if user.department_id:
            q = q.where(Timetable.department_id == user.department_id)
        if day:
            q = q.where(Timetable.day_of_week == day)
        result = await db.execute(q)
        rows = list(result.scalars().all())
        if not rows:
            return f"I couldn't find a {subject.title()} class{f' on {day}' if day else ''} to cancel."
        for r in rows:
            await db.delete(r)
        await db.commit()
        return f"🗑️ Cancelled {len(rows)} {subject.title()} class(es){f' on {day}' if day else ''}."

    # ── Add a timetable class ─────────────────────────────────────────────
    if add_verbs and has("class", "lecture", "period"):
        if not user.department_id:
            return ("You don't have a department assigned, so I can't add a class. "
                    "Set your department first (User Management).")
        m = re.search(
            r"(?:add|create|put|schedule|set up)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+(?:class|lecture|period)",
            msg,
        )
        if not m:
            m = re.search(r"(?:class|lecture)\s+(?:of|for)\s+(\w[\w ]*?)\s+on", msg)
        subject = m.group(1).strip() if m else None
        day = _find_day(msg)
        start = _parse_time_phrase(msg)
        sem_m = re.search(r"sem(?:ester)?\s*(\d)", msg)
        semester = int(sem_m.group(1)) if sem_m else 1
        room_m = re.search(r"(?:room|in)\s+([a-z]?\d{1,4}[a-z]?)", msg)
        room = room_m.group(1).upper() if room_m else None

        missing = []
        if not subject:
            missing.append("subject")
        if not day:
            missing.append("day")
        if not start:
            missing.append("time")
        if missing:
            return ("To add a class I need the " + ", ".join(missing) +
                    ". Try: \"put Bengali class on Monday 7 pm\".")

        end = _add_hour(start)
        entry = Timetable(
            department_id=user.department_id,
            semester=semester,
            day_of_week=day,
            start_time=start,
            end_time=end,
            subject=subject.title(),
            room=room,
            faculty_name=None,
        )
        db.add(entry)
        await db.commit()
        return (f"✅ Added **{subject.title()}** on **{day}** "
                f"{start.strftime('%I:%M %p').lstrip('0')}–{end.strftime('%I:%M %p').lstrip('0')}"
                f"{f' in {room}' if room else ''} (Sem {semester}) to the timetable.")

    # ── Post a notice (incl. holiday/off-day announcements) ───────────────
    notice_intent = (
        (has("notice", "announcement", "announce") and add_verbs)
        or (add_verbs and has("off day", "offday", "holiday", "no class", "no classes", "closed", "leave"))
    )
    if notice_intent:
        content = message.strip()
        # Strip leading command phrasing to get the announcement text.
        m = re.search(
            r"(?:notice|announcement|announce)\s+(?:about|that|saying|regarding|:)?\s*(.+)",
            content, re.IGNORECASE,
        )
        if m and m.group(1).strip():
            content = m.group(1).strip()
        else:
            content = re.sub(
                r"^\s*(?:please\s+)?(?:add|create|post|make|put|send)\s+(?:a\s+|an\s+|the\s+)?(?:notice|announcement)?\s*(?:about|that|saying|regarding|:)?\s*",
                "", content, flags=re.IGNORECASE,
            ).strip()
        if not content:
            return "What should the notice say? Try: \"post a notice that tomorrow is a holiday\"."

        is_holiday = bool(re.search(r"off\s*day|offday|holiday|no class|closed", msg))
        title = "Holiday / Off Day" if is_holiday else (content[:60] + ("…" if len(content) > 60 else ""))
        notice = Notice(
            title=title,
            body=content[0].upper() + content[1:],
            domain="academic",
            target_department_id=user.department_id,
            target_year=None,
            created_by=user.id,
            is_pinned=is_holiday,
        )
        db.add(notice)
        await db.commit()
        scope = "your department" if user.department_id else "all students"
        return (f"📢 Posted notice **\"{title}\"** to {scope}. "
                f"Students will see it in their notifications.")

    return None


@router.get("/history", response_model=list[ChatMessageOut], summary="Load saved chat history")
async def get_history(
    current_user: CurrentUser,
    db: DB,
    limit: int = 100,
) -> list[ChatMessageOut]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .limit(limit)
    )
    return [ChatMessageOut.model_validate(m) for m in result.scalars().all()]


@router.delete("/history", status_code=204, summary="Clear chat history")
async def clear_history(current_user: CurrentUser, db: DB) -> None:
    await db.execute(
        ChatMessage.__table__.delete().where(ChatMessage.user_id == current_user.id)
    )
    await db.commit()


@router.post("/query", response_model=AIQueryResponse)
async def ai_query(
    body: AIQueryRequest,
    current_user: CurrentUser,
    db: DB,
) -> AIQueryResponse:
    # Load recent conversation for context
    hist_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(HISTORY_TURNS)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(hist_result.scalars().all())
    ]

    ctx = await _gather_context(current_user, db)

    # Admins can issue CRUD commands (add notice / add or cancel a class).
    action_reply = await _try_admin_action(body.message, current_user, db)
    if action_reply is not None:
        reply = action_reply
        labels = ["action"]
    else:
        prompt = _build_prompt(ctx, body.message, history)
        reply = await _call_llm(prompt, ctx, body.message, history)
        labels = []
        if ctx["today_classes"] or ctx["week_timetable"]:
            labels.append("timetable")
        if ctx["attendance"]:
            labels.append("attendance")
        if ctx["mess"]:
            labels.append("mess")
        if ctx["notices"]:
            labels.append("notices")
        if ctx["placements"] or ctx["placement_notices"]:
            labels.append("placement")

    # Persist this turn (user message + assistant reply)
    db.add(ChatMessage(user_id=current_user.id, role="user", content=body.message))
    db.add(ChatMessage(user_id=current_user.id, role="assistant", content=reply))
    await db.commit()

    return AIQueryResponse(reply=reply, context_used=labels)


# ── Smart Daily Digest ────────────────────────────────────────────────────── #

def _days_until(iso: str) -> int | None:
    try:
        return (date.fromisoformat(iso) - date.today()).days
    except Exception:  # noqa: BLE001
        return None


def _when_label(days: int | None) -> str:
    if days is None:
        return ""
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


@router.get("/digest", response_model=DigestResponse, summary="Smart daily digest for the student")
async def daily_digest(current_user: CurrentUser, db: DB) -> DigestResponse:
    ctx = await _gather_context(current_user, db)
    threshold = settings.ATTENDANCE_THRESHOLD
    first_name = (ctx["name"] or "there").split(" ")[0]

    # At-risk subjects (below threshold) from attendance
    by_subject = (ctx["attendance"] or {}).get("by_subject", {}) if ctx["attendance"] else {}
    at_risk = {sub: pct for sub, pct in by_subject.items() if pct < threshold}
    today_subjects = {c["subject"] for c in ctx["today_classes"]}

    # Classes today (flag at-risk ones)
    classes = [
        DigestClass(
            subject=c["subject"], start=c["start"], end=c["end"],
            room=c.get("room"), at_risk=c["subject"] in at_risk,
        )
        for c in ctx["today_classes"]
    ]

    # Assignments due within 7 days (prioritise soonest)
    assignments: list[DigestItem] = []
    for a in ctx["assignments"]:
        days = _days_until(a["due"])
        assignments.append(DigestItem(
            title=a["title"],
            subtitle=a["subject"],
            when=_when_label(days),
            urgent=days is not None and days <= 2,
        ))

    # Deadlines: exams + placement registration
    deadlines: list[DigestItem] = []
    for e in ctx["exams"]:
        days = _days_until(e["date"])
        deadlines.append(DigestItem(
            title=f"{e['subject']} exam",
            subtitle=f"{e['time']} · {e['room'] or 'TBD'}",
            when=_when_label(days),
            urgent=days is not None and days <= 3,
        ))
    for p in ctx["placements"]:
        if p["deadline"]:
            days = _days_until(p["deadline"])
            deadlines.append(DigestItem(
                title=f"{p['company']} applications close",
                subtitle=p["role"],
                when=_when_label(days),
                urgent=days is not None and days <= 3,
            ))
    deadlines.sort(key=lambda d: (not d.urgent, d.when or ""))

    notices = [DigestItem(title=n["title"], subtitle=n["body"][:80], urgent=n["pinned"]) for n in ctx["notices"][:4]]
    events = [DigestItem(title=e["title"], when=e["date"]) for e in ctx["events"][:4]]
    attendance_alerts = [
        DigestItem(
            title=sub,
            subtitle=f"{pct}% — below the {threshold}% requirement",
            when="class today" if sub in today_subjects else None,
            urgent=sub in today_subjects,
        )
        for sub, pct in sorted(at_risk.items(), key=lambda x: x[1])
    ]

    # ── Smart insight (connect the dots) ──────────────────────────────────
    insight = f"Good morning, {first_name}! "
    risk_today = [s for s in at_risk if s in today_subjects]
    due_soon = [a for a in ctx["assignments"] if (_days_until(a["due"]) or 9) <= 1]
    exam_soon = [e for e in ctx["exams"] if (_days_until(e["date"]) or 9) <= 2]
    pl_soon = [p for p in ctx["placements"] if p["deadline"] and (_days_until(p["deadline"]) or 9) <= 2]

    if risk_today:
        sub = risk_today[0]
        insight += (f"Your {sub} attendance is {by_subject[sub]}% — below the {threshold}% line, "
                    f"and you have {sub} today. This is the class to attend.")
    elif due_soon:
        a = due_soon[0]
        insight += f"{a['title']} ({a['subject']}) is due {_when_label(_days_until(a['due']))} — make it your first task."
    elif exam_soon:
        e = exam_soon[0]
        insight += f"Your {e['subject']} exam is {_when_label(_days_until(e['date']))} — start revising today."
    elif pl_soon:
        p = pl_soon[0]
        insight += f"{p['company']} applications close {_when_label(_days_until(p['deadline']))} — apply before it's too late."
    elif classes:
        insight += f"You have {len(classes)} class(es) today, starting with {classes[0].subject} at {classes[0].start}."
    else:
        insight += "No classes scheduled today — a great time to catch up on assignments or revision."

    # ── Quick-action pills (route into the assistant) ─────────────────────
    quick_actions: list[str] = []
    if classes:
        quick_actions.append("What's my schedule today?")
    if risk_today or at_risk:
        quick_actions.append("Can I miss my next class?")
    if ctx["mess"]:
        quick_actions.append("What's for lunch today?")
    if pl_soon or ctx["placements"]:
        quick_actions.append("Any placement deadlines?")
    if not quick_actions:
        quick_actions = ["What's my schedule today?", "What's the mess menu?"]

    return DigestResponse(
        greeting=f"Good morning, {first_name}",
        date=date.today().strftime("%A, %d %B %Y"),
        insight=insight,
        classes=classes,
        assignments=assignments,
        deadlines=deadlines,
        notices=notices,
        events=events,
        attendance_alerts=attendance_alerts,
        quick_actions=quick_actions,
    )
