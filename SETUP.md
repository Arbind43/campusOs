# CampusOS — Local Setup
//bikram

## Prerequisites

Install these first:

1. **Node.js 20+** → https://nodejs.org/en/download  
2. **Python 3.11+** → https://www.python.org/downloads/ (check "Add Python to PATH")

---

## 1. Supabase Setup (already have the project)

You already have the Supabase project: `https://atqehxgcedarbuirqzli.supabase.co`

You need two more things from the Supabase Dashboard:

### A. Database connection string (for FastAPI)
1. Dashboard → Project Settings → Database → Connection string → **URI**
2. Use the **Transaction pooler** string (port 6543) — looks like:
   ```
   postgresql://postgres.atqehxgcedarbuirqzli:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
3. Change `postgresql://` → `postgresql+asyncpg://`
4. Paste into `backend/.env` as `DATABASE_URL`

### B. JWT Secret (for FastAPI to verify tokens)
1. Dashboard → Project Settings → API → **JWT Secret**
2. Paste into `backend/.env` as `SUPABASE_JWT_SECRET`

### C. Demo account
1. Dashboard → Authentication → Users → **Add user**
2. Email: `demo@campusos.app`, Password: `demo1234`
3. Copy the UUID of the created user, then run:
   ```bash
   python -m scripts.seed_demo <uuid-from-step-2>
   ```

### D. Disable email confirmation (for hackathon)
1. Dashboard → Authentication → Providers → Email
2. Toggle **"Confirm email"** → OFF  
   (So users can register and login instantly without checking email)

---

## 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env
copy .env.example .env
# Then fill in DATABASE_URL and SUPABASE_JWT_SECRET

# Run database migration
alembic upgrade head

# Seed demo account (after creating it in Supabase Dashboard)
python -m scripts.seed_demo <supabase-demo-user-uuid>

# Start the server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# .env.local is already created with your Supabase keys
# Just update NEXT_PUBLIC_API_URL if your backend runs on a different port

# Start dev server
npm run dev
```

Frontend: http://localhost:3000

---

## How Auth Works

```
User fills Register form
    ↓
supabase.auth.signUp()     ← Supabase creates the account
    ↓
authApi.syncProfile()      ← Our FastAPI stores the role in user_profiles table
    ↓
Dashboard loads

User fills Login form
    ↓
supabase.auth.signInWithPassword()   ← Supabase issues a JWT
    ↓
JWT is attached to every FastAPI request as: Authorization: Bearer <token>
    ↓
FastAPI verifies JWT using SUPABASE_JWT_SECRET → loads user_profiles row
```

---

## Project Structure

```
hackon/
├── backend/
│   ├── app/
│   │   ├── core/security.py      # Supabase JWT verification
│   │   ├── models/user.py        # UserProfile (role, name, keyed by Supabase UUID)
│   │   ├── routers/auth.py       # POST /auth/sync-profile, GET /auth/me
│   │   ├── schemas/auth.py       # Pydantic schemas
│   │   ├── config.py             # Settings from .env
│   │   ├── database.py           # Async SQLAlchemy → Supabase Postgres
│   │   ├── dependencies.py       # JWT auth dependency (verifies Supabase token)
│   │   └── main.py               # FastAPI app
│   ├── alembic/                  # DB migrations
│   ├── scripts/seed_demo.py      # Demo profile seeder
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx           # Landing page (Login / Register / Try Demo)
        │   └── dashboard/         # Protected — requires Supabase session
        ├── components/
        │   ├── auth/
        │   │   ├── AuthProvider.tsx   # Listens to Supabase session changes
        │   │   ├── AuthGuard.tsx      # Route protection
        │   │   ├── LoginForm.tsx      # Uses supabase.auth.signInWithPassword
        │   │   └── RegisterForm.tsx   # Uses supabase.auth.signUp + syncProfile
        │   └── ui/                   # Button, Input, Label, Card
        ├── lib/
        │   ├── supabase.ts        # Browser Supabase client
        │   ├── api.ts             # Axios client (attaches Supabase JWT)
        │   └── auth-api.ts        # syncProfile + me endpoints
        └── store/auth.ts          # Zustand (session + profile)
```
