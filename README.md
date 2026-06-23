# CampusOS — AI-Powered Campus Operating System

CampusOS is a full-stack campus platform that unifies timetables, attendance, notices,
mess, placements, wellbeing, and scheduling behind a single **AI assistant**. It was built
for the HackOn (Amazon) hackathon and uses an Amazon-inspired dark/orange theme.

The system is **role-aware** (Student, Faculty, Academic Admin, Super Admin) and ships an
agentic chatbot that both **answers questions** (for students) and **performs actions**
(for admins) from natural language.

---

## Table of contents

1. [Tech stack](#tech-stack)
2. [High-level architecture](#high-level-architecture)
3. [Project structure](#project-structure)
4. [Authentication & RBAC](#authentication--rbac)
5. [Data model](#data-model)
6. [Features](#features) — how each one works, its architecture, and endpoints
7. [Full API reference](#full-api-reference)
8. [Local setup & running](#local-setup--running)
9. [Database & migrations](#database--migrations)
10. [Environment variables](#environment-variables)

---

## Tech stack

| Layer        | Technology |
|--------------|-----------|
| Frontend     | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Zustand, lucide-react, Axios |
| Backend      | FastAPI, SQLAlchemy 2 (async), Pydantic v2, Alembic |
| Database     | PostgreSQL (Supabase / Neon), `asyncpg` driver |
| Auth         | Supabase Auth (browser) + app-issued JWT validated by the backend |
| AI / LLM     | Google Gemini (`gemini-1.5-flash`) with a built-in **offline rule-based fallback**; Groq vision (`llama-3.2-90b-vision`) for OCR |
| OCR          | Groq vision API (timetable + mess menu image parsing) with mock fallback |

> **Key design principle:** every AI feature degrades gracefully. If no `GEMINI_API_KEY`
> or `GROQ_API_KEY` is configured, the app still works using deterministic offline logic,
> so the demo runs with zero external keys.

---

## High-level architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Browser (Next.js)                            │
│  App Router pages (/, /dashboard/*)  ·  Zustand auth store            │
│  Axios apiClient (injects JWT)        ·  Supabase browser client      │
└───────────────┬───────────────────────────────────────┬──────────────┘
                │ REST (/api/v1/*, Bearer JWT)           │ Supabase Auth
                ▼                                        ▼
┌──────────────────────────────────────────────┐   ┌───────────────────┐
│                FastAPI backend                 │   │   Supabase Auth   │
│  Routers ── Dependencies (RBAC) ── Services    │   │  (email/password) │
│  ┌─────────┐  ┌──────────────┐  ┌───────────┐  │   └───────────────────┘
│  │ routers │→ │ require_role │→ │ services  │  │
│  └─────────┘  └──────────────┘  │ ocr,      │  │
│       │                          │ conflicts │  │
│       ▼                          └─────┬─────┘  │
│  SQLAlchemy async models               │        │
└───────────────┬────────────────────────┼────────┘
                │ asyncpg                 │ httpx
                ▼                         ▼
        ┌───────────────┐        ┌──────────────────┐
        │  PostgreSQL    │        │  Groq / Gemini   │
        │ (Supabase/Neon)│        │   LLM + Vision   │
        └───────────────┘        └──────────────────┘
```

**Request lifecycle**
1. Frontend page calls a typed function in `src/lib/*-api.ts`.
2. Axios `apiClient` attaches the JWT (`Authorization: Bearer …`) from the Zustand store.
3. FastAPI router resolves the user via `get_current_user`, enforces role with `require_role(...)`.
4. The handler queries async SQLAlchemy models and/or calls a service (OCR, conflict scan, LLM).
5. A Pydantic schema serializes the response back to the typed frontend client.

---

## Project structure

```
hackon/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app + router registration + CORS
│   │   ├── config.py              # Pydantic settings (env)
│   │   ├── database.py            # async engine + session
│   │   ├── dependencies.py        # auth + require_role RBAC dependencies
│   │   ├── core/                  # security (JWT), logging
│   │   ├── models/                # SQLAlchemy models (one file per domain)
│   │   ├── schemas/campus.py      # all Pydantic request/response schemas
│   │   ├── routers/               # one router per feature domain
│   │   └── services/
│   │       ├── ocr.py             # timetable + mess image parsing (Groq vision)
│   │       └── conflicts.py       # schedule conflict detection engine
│   ├── alembic/versions/          # migrations 001–007
│   └── scripts/                   # seed scripts (attendance, demo, admins)
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx           # landing + login/register/demo
        │   └── dashboard/         # one folder per feature page
        ├── components/
        │   ├── auth/              # AuthGuard, AuthProvider, Login/Register forms
        │   ├── dashboard/         # DashboardHeader, DailyDigest
        │   ├── notifications/     # NotificationBell (notice popups)
        │   ├── landing/           # Globe3D, Starfield, AuthShell
        │   └── timetable/         # TimetableUploader, TimetableDisplay
        ├── lib/                   # typed API clients (one per feature)
        └── store/auth.ts          # Zustand auth store (persisted)
```

---

## Authentication & RBAC

- **Login/Register** go through Supabase Auth on the browser; the backend issues/validates a
  simple JWT (`app/core/security.py`). The token + user profile are persisted in the Zustand
  store (`localStorage` key `auth-storage`).
- **`AuthGuard`** wraps all `/dashboard/*` routes and redirects unauthenticated users to `/`.
- **Role enforcement** is centralized in `app/dependencies.py`:
  - `get_current_user` → resolves the `UserProfile` from the JWT.
  - `require_role(*roles)` → dependency factory used by every protected write endpoint.
  - Pre-built dependencies: `CurrentUser`, `SuperAdmin`, `AcademicWrite`, `PlacementWrite`,
    `HostelWrite`, `MessWrite`, `FacultyWrite`.
- **Roles:** `STUDENT`, `FACULTY`, `ACADEMIC_ADMIN`, `SUPER_ADMIN` (plus optional
  `PLACEMENT_*`, `HOSTEL_*`, `COUNSELLOR`). The legacy single-role field on `user_profiles`
  is the working source of truth; a full `roles`/`user_roles` RBAC table also exists.

---

## Data model

Core tables (PostgreSQL):

| Table | Purpose |
|-------|---------|
| `user_profiles` | App profile keyed by Supabase user id; `role`, `department_id`, `year_of_study`, `hostel_room_id` |
| `departments` | Department catalogue (`name`, `code`) |
| `timetables` | Weekly class entries (`day_of_week`, `start/end_time`, `subject`, `room`, `faculty_name`, `semester`) |
| `exam_schedules` | Exam entries (`exam_date`, `start_time`, `room`, `subject`, `semester`) |
| `holidays` | Holiday calendar |
| `attendance_marks` | Per-day, per-subject attendance (`status` present/absent/late) — **predictor source** |
| `notices` | Notice board (`domain`, `target_department_id`, `target_year`, `is_pinned`) |
| `mess_schedule` | Campus mess menu with meal timings |
| `mess_ratings` | 1-tap anonymous meal ratings (sentiment loop) |
| `wellbeing_checkins` | Anonymous weekly mood check-ins |
| `chat_messages` | Persisted AI assistant conversation history per user |
| `placement_drives`, `drive_registrations`, `placement_notices` | Placement domain |
| `events`, `event_registrations`, `assignments`, `clubs`, `club_memberships`, `hostels`, `hostel_rooms`, `mess_menus`, `mess_notices` | Supporting domains |

> Anonymous tables (`wellbeing_checkins`, `mess_ratings`) store **no user id** — only a
> one-way SHA-256 `submitter_hash` (user id + period + server secret) to prevent duplicate
> submissions without being reversible.

---

## Features

Every feature below lists: **what it does**, **how it works / architecture**, the **backend
endpoints**, and the **frontend route**. All endpoints are prefixed with `/api/v1`.

---

### 1. AI Campus Assistant (chatbot)

**What:** A conversational assistant. For **students** it answers from their live data
(timetable, attendance, mess, notices, placements, exams, assignments). For **admins** it is
**agentic** — it executes CRUD commands from natural language.

**How it works / architecture**
- `_gather_context()` builds a single structured context dict by querying all of the
  student's data sources (filtered by department + year).
- `_build_prompt()` renders that context + the last 10 messages of history into an LLM prompt.
- `_call_llm()` calls Gemini; if no key/failure, `_offline_answer()` does **intent routing**
  (keyword matching for schedule / mess / attendance / notices / placement / "can I miss class").
- **Memory:** every turn is saved to `chat_messages`; recent turns are replayed for context,
  and short follow-ups ("what about tomorrow?") inherit the previous topic.
- **Admin actions:** `_try_admin_action()` runs first for admins. Regex parsers detect:
  - *Add class* — "put Bengali class on Monday 7 pm" → creates a `timetables` row.
  - *Cancel class* — "cancel Bengali class on Monday" → deletes matching rows.
  - *Post notice* — "post a notice that tomorrow is a holiday" → creates a `notices` row
    (auto-pinned for holidays).
- "Can I miss class?" computes the projected attendance % after one more absence vs the
  threshold and advises accordingly.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| POST | `/ai/query` | Any | Ask a question / issue an admin command |
| GET | `/ai/history` | Any | Load saved conversation |
| DELETE | `/ai/history` | Any | Clear conversation |

**Frontend:** `/dashboard/assistant` (chat UI, role-aware suggestion chips, auto-send via `?q=`).

---

### 2. Smart Daily Digest

**What:** A personalised morning summary — today's classes, urgent assignments, upcoming
deadlines, attendance-at-risk subjects, notices and events — with a single **insight sentence**
that connects the dots, plus **quick-action pills** that route into the assistant.

**How it works / architecture**
- Reuses the assistant's `_gather_context()` so it shares one data pipeline.
- **Prioritisation cascade** for the insight: at-risk subject with a class today → assignment
  due tonight/tomorrow → exam in ≤2 days → placement deadline in ≤2 days → schedule summary.
- Flags classes whose subject is below the attendance threshold; sorts deadlines urgent-first;
  filters out anything not actionable now.
- Quick-action pills are generated from what's present and deep-link to
  `/dashboard/assistant?q=<question>` (the assistant auto-sends on open).

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/ai/digest` | Student | Build the prioritised, personalised digest |

**Frontend:** rendered at the top of the **student** `/dashboard` via `DailyDigest`.

---

### 3. Timetable management (OCR upload)

**What:** Admins upload a **photo** of a timetable; AI extracts the schedule for review, then
saves it. Students view their schedule.

**How it works / architecture**
- `services/ocr.py::parse_timetable_image()` sends the image to Groq vision with a strict JSON
  prompt; falls back to a mock schedule when no key.
- Upload returns parsed entries **without writing** (review step). Confirm does an **atomic
  replace** of the department's timetable (delete-all + insert) with per-row validation.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/academic/timetable` | Any | Get timetable (by dept/semester) |
| POST | `/academic/timetable` | Admin | Create a single entry |
| DELETE | `/academic/timetable/{id}` | Admin | Delete an entry |
| POST | `/academic/timetable/upload` | Admin | OCR-parse an image (no write) |
| POST | `/academic/timetable/confirm` | Admin | Atomically save reviewed entries |
| GET | `/academic/departments` | Any | List departments |

**Frontend:** `/dashboard/timetable`.

---

### 4. Attendance Management + Predictor AI

**What:** Admins/faculty bulk-mark attendance per department/year/subject/date. Students get a
per-subject **risk predictor** that warns before they fall below the minimum threshold and tells
them exactly how many classes they can still miss, or must attend to recover.

**How it works / architecture**
- Marking upserts rows into `attendance_marks` (unique on student+date+subject).
- The predictor (`/attendance/predict`) groups marks by subject and uses **exact integer math**:
  - `can_miss = floor(100·present / T) − total`
  - `must_attend = ceil((T·total − 100·present) / (100 − T))`
  - Status: `safe` / `warning` (on the edge) / `critical` (below threshold T = `ATTENDANCE_THRESHOLD`, default 80%).
- The chatbot's attendance answer and the daily digest both reuse this signal.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/attendance/students` | Admin/Faculty | Roster for marking (by dept + year) |
| POST | `/attendance/mark` | Admin/Faculty | Bulk upsert attendance |
| GET | `/attendance/records` | Admin/Faculty | Records for a date + subject |
| GET | `/attendance/me` | Student | Own attendance summary |
| GET | `/attendance/predict` | Student | Per-subject risk + recovery plan |

**Frontend:** `/dashboard/attendance` (role-aware: marking grid vs predictor view).
**Seed:** `python -m scripts.seed_attendance`.

---

### 5. Notices with department + year targeting

**What:** Admins publish notices targeted by **department and year**. Matching students get a
real-time **notification bell + popup**.

**How it works / architecture**
- `notices` rows carry `target_department_id` and `target_year` (NULL = "all").
- `GET /notices` filters server-side so a student only ever receives notices meant for them.
- `NotificationBell` polls `/notices` every 60s, tracks seen IDs in `localStorage`, shows an
  unread badge + dropdown, and pops a toast for the newest unseen notice.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/notices` | Any | Notices visible to the current user |
| POST | `/notices` | Domain admin | Create a notice |
| DELETE | `/notices/{id}` | Admin | Delete a notice |

**Frontend:** `/dashboard/notices`; bell in the dashboard navbar.

---

### 6. Mess menu + Sentiment loop

**What:** Admins upload the mess menu (image OCR or manual). Students rate each meal in **one
tap**. Wardens see a **real-time sentiment dashboard**; persistent low ratings trigger an
**automatic "review the menu" nudge**.

**How it works / architecture**
- `mess_schedule` holds the campus menu with meal timings; uploaded via `parse_mess_image()`.
- `mess_ratings` stores anonymous 1-tap ratings (👍/😐/👎 → 5/3/1), deduped per student/meal/day.
- `/mess/sentiment` aggregates today's per-meal averages + a 7-day trend and computes nudges:
  a **3-day persistent low** (avg < 2.5 with ≥5 ratings) and a **same-day strong negative**
  (≥60% negative). The dashboard polls every 20s for a near-real-time feel.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/mess` | Any | Get the mess schedule |
| POST | `/mess/upload` | Admin | OCR-parse a menu image |
| POST | `/mess/confirm` | Admin | Replace the saved schedule |
| POST | `/mess/rate` | Student | One-tap rate today's meal |
| GET | `/mess/rate/today` | Student | My ratings for today |
| GET | `/mess/sentiment` | Warden/Admin | Real-time sentiment + nudges |

**Frontend:** `/dashboard/mess` (role-aware: rating widget vs sentiment dashboard).

---

### 7. Placement management

**What:** Admins / placement coordinators post drives and prep resources. Students view drives,
register, and read resources. The chatbot can answer placement questions.

**How it works / architecture**
- `placement_drives` (company, role, package, dates, description) + `placement_notices`
  (prep resources) + `drive_registrations`.
- Write access broadened to include `ACADEMIC_ADMIN` so the demo admin can manage placements.
- The assistant's context includes active drives and placement notices.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/placement/drives` | Any | List drives (`active_only` flag) |
| POST | `/placement/drives` | Admin/Coordinator | Create a drive |
| DELETE | `/placement/drives/{id}` | Admin/Coordinator | Delete a drive |
| POST | `/placement/drives/{id}/register` | Student | Register for a drive |
| GET | `/placement/notices` | Any | List prep resources/notices |
| POST | `/placement/notices` | Admin/Coordinator | Post a resource/notice |
| DELETE | `/placement/notices/{id}` | Admin/Coordinator | Delete a notice |

**Frontend:** `/dashboard/placement`.

---

### 8. Wellbeing check-in (anonymous)

**What:** A weekly anonymous 3-question mood check-in (mood/stress/sleep). Counsellors see
aggregate insights with **pattern detection** (e.g. a stress spike that lines up with upcoming
exams) and recommendations.

**How it works / architecture**
- `wellbeing_checkins` stores **no user id** — only a one-way hash to enforce one submission
  per student per week. Department/year are coarse cohort tags.
- `/wellbeing/insights` compares the current week vs last week, computes high-stress %, builds
  a 4-week trend, cross-references `exam_schedules` for the "before exams" correlation, and
  surfaces department hotspots (only cohorts ≥ 3 responses, for privacy).

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/wellbeing/status` | Student | Has the student checked in this week? |
| POST | `/wellbeing/checkin` | Student | Submit anonymous check-in |
| GET | `/wellbeing/insights` | Counsellor/Admin | Aggregated insights + alerts |

**Frontend:** `/dashboard/wellbeing` (role-aware: check-in form vs insights dashboard).

---

### 9. Conflict-free scheduling

**What:** Two things in one admin tool: (a) a **conflict scanner** that flags room
double-bookings, faculty clashes, student exam overlaps and event venue clashes; (b) a
**conflict-aware class scheduler** — pick department + semester + slot, see clashes and **all
free rooms with their free time windows**, then schedule.

**How it works / architecture**
- `services/conflicts.py::scan_conflicts()` does pairwise overlap detection across exams,
  timetable and events (exams assume a 180-min window since they store only a start time).
- `/academic/timetable/check` validates a proposed slot against existing classes for room,
  faculty and cohort clashes.
- `/academic/free-slots` computes, per room, the **gaps** between bookings within working hours
  (8 AM–6 PM) for a given day — the UI shows clickable free windows that auto-fill the form.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/academic/conflicts` | Admin | Full conflict scan |
| POST | `/academic/timetable/check` | Admin | Check a proposed slot |
| GET | `/academic/free-slots` | Admin | Free time windows per room for a day |

**Frontend:** `/dashboard/conflicts`.

---

### 10. User management

**What:** Admins assign students to a **department and year** (prerequisite for attendance
rosters and targeted notices) and can quick-add departments / change roles.

**Endpoints**
| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| GET | `/admin/manage/users` | Admin | List users (filter by role/dept) |
| PATCH | `/admin/manage/users/{id}` | Admin | Set department / year / role |
| POST | `/admin/manage/departments` | Admin | Quick-add a department |
| GET | `/admin/users` | Super Admin | List all users (with roles) |
| POST | `/admin/users/{id}/roles` | Super Admin | Assign an RBAC role |
| DELETE | `/admin/users/{id}/roles/{role}` | Super Admin | Revoke a role |
| GET | `/admin/roles` | Super Admin | List system roles |

**Frontend:** `/dashboard/users`.

---

### Supporting domains

Exams & holidays (`/academic/exams`, `/academic/holidays`), events
(`/events`, `/events/{id}/register`), assignments (`/assignments`), clubs
(`/clubs`, `/clubs/{id}/join`, `/clubs/{id}/leave`), hostel
(`/hostel`, `/hostel/rooms`, `/hostel/menu`, `/hostel/notices`).

---

## Full API reference

Base URL: `http://localhost:8000/api/v1` · Auth: `Authorization: Bearer <jwt>` · `GET /health` is public.

| Domain | Endpoints |
|--------|-----------|
| **Auth** | `POST /auth/login`, `POST /auth/register`, `GET /auth/me` |
| **AI** | `POST /ai/query`, `GET /ai/history`, `DELETE /ai/history`, `GET /ai/digest` |
| **Academic** | `GET/POST/DELETE /academic/timetable`, `POST /academic/timetable/upload`, `POST /academic/timetable/confirm`, `POST /academic/timetable/check`, `GET /academic/free-slots`, `GET /academic/conflicts`, `GET /academic/departments`, `GET/POST /academic/exams`, `GET/POST /academic/holidays`, `GET /academic/debug/me` |
| **Attendance** | `GET /attendance/students`, `POST /attendance/mark`, `GET /attendance/records`, `GET /attendance/me`, `GET /attendance/predict` |
| **Notices** | `GET/POST /notices`, `DELETE /notices/{id}` |
| **Mess** | `GET /mess`, `POST /mess/upload`, `POST /mess/confirm`, `POST /mess/rate`, `GET /mess/rate/today`, `GET /mess/sentiment` |
| **Placement** | `GET/POST /placement/drives`, `DELETE /placement/drives/{id}`, `POST /placement/drives/{id}/register`, `GET/POST /placement/notices`, `DELETE /placement/notices/{id}` |
| **Wellbeing** | `GET /wellbeing/status`, `POST /wellbeing/checkin`, `GET /wellbeing/insights` |
| **Admin** | `GET /admin/manage/users`, `PATCH /admin/manage/users/{id}`, `POST /admin/manage/departments`, `GET /admin/users`, `POST /admin/users/{id}/roles`, `DELETE /admin/users/{id}/roles/{role}`, `GET/POST /admin/departments`, `POST /admin/hostels`, `POST /admin/clubs`, `GET /admin/roles` |
| **Events** | `GET/POST /events`, `POST /events/{id}/register` |
| **Assignments** | `GET/POST /assignments`, `DELETE /assignments/{id}` |
| **Clubs** | `GET /clubs`, `GET /clubs/{id}`, `POST /clubs/{id}/join`, `DELETE /clubs/{id}/leave` |
| **Hostel** | `GET /hostel`, `GET/POST /hostel/rooms`, `GET/POST /hostel/menu`, `GET/POST /hostel/notices` |

Interactive docs (Swagger): `http://localhost:8000/docs`.

---

## Local setup & running

### Prerequisites
- Python 3.11+ and Node.js 18+
- A PostgreSQL database (Supabase or Neon connection string)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate           # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env          # then fill in DATABASE_URL, SUPABASE_* (see below)
uvicorn app.main:app --reload   # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
copy .env.local.example .env.local   # set NEXT_PUBLIC_SUPABASE_* and NEXT_PUBLIC_API_URL
npm run dev                            # http://localhost:3000
```

### Demo / seed data
```bash
cd backend
python -m scripts.seed_demo            # demo accounts & base data
python -m scripts.seed_attendance      # attendance (drives the predictor)
```
Demo accounts (from the landing page "Try Demo"): `demo.student@…`, `demo.admin@…`,
`demo.professor@…` (password `demo1234`).

---

## Database & migrations

Migrations live in `backend/alembic/versions/` (001–007):

| Rev | Adds |
|-----|------|
| 001 | `user_profiles` |
| 002 | Full RBAC + domain schema (departments, timetables, exams, hostels, placement, clubs, notices, events, assignments) |
| 003 | `attendance_marks` + `notices.target_year` |
| 004 | `mess_schedule` |
| 005 | `chat_messages` |
| 006 | `wellbeing_checkins` |
| 007 | `mess_ratings` |

Apply with:
```bash
cd backend
alembic upgrade head
```

> **Note:** during development this database was stamped at an out-of-sync Alembic revision, so
> the newer tables (003–007) were also applied directly via idempotent `CREATE TABLE IF NOT
> EXISTS` DDL. The migration files remain the source of truth for a clean database.

---

## Environment variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://…`) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_JWT_SECRET` | JWT secret (also used to salt anonymous hashes) |
| `GROQ_API_KEY` | (optional) Groq vision key for OCR — falls back to mock |
| `GEMINI_API_KEY` | (optional) Gemini key for the assistant — falls back to offline logic |
| `ATTENDANCE_THRESHOLD` | Minimum attendance % (default 80) |
| `CRITICAL_ATTENDANCE_FLOOR` | Critical floor for warnings (default 75) |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Supabase publishable/anon key |
| `NEXT_PUBLIC_API_URL` | Backend base URL (default `http://localhost:8000/api/v1`) |

---

## Design notes & conventions

- **Typed end-to-end:** each backend domain has a matching `src/lib/*-api.ts` client with
  interfaces mirroring the Pydantic schemas.
- **Graceful AI degradation:** no LLM/OCR key required — offline logic keeps every feature
  functional for demos.
- **Privacy by design:** wellbeing and mess ratings are anonymous (no user id stored).
- **Consistent UI:** shared `DashboardHeader`, Amazon dark-navy + orange theme, role-aware pages.
```
