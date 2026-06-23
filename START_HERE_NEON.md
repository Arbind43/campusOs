# ⚡ START HERE - Complete Setup for Neon Database

## 🎯 What You Have

- ✅ Neon PostgreSQL database (not Supabase)
- ✅ Simple authentication system (no complex JWT)
- ✅ Timetable OCR + AI parsing ready

---

## 🚀 Complete Setup (4 Steps)

### Step 1: Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
pip install asyncpg python-dotenv
```

### Step 2: Setup Database Tables

**Option A: Run Python script (Recommended)**
```powershell
python setup_neon_db.py
```

**Option B: Manual - Copy SQL to Neon Console**
1. Go to your Neon project dashboard
2. Click "SQL Editor"
3. Copy all contents from `neon_setup.sql`
4. Paste and run
5. Should see "Database setup complete!"

### Step 3: Create Admin User

```powershell
python -m scripts.create_admin_simple
```

This creates:
- ✅ `admin@college.edu` with ACADEMIC_ADMIN role
- ✅ `student@college.edu` with STUDENT role
- ✅ CSE department

### Step 4: Start Backend

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Backend is now running at http://localhost:8000**

---

## 🧪 Test It Works

### Option 1: Interactive API Docs

1. Open http://localhost:8000/docs
2. Try `POST /auth/login`:
   ```json
   {
     "email": "admin@college.edu",
     "password": "anything"
   }
   ```
3. Copy the `access_token` from response
4. Click "Authorize" button (🔓 icon at top right)
5. Paste token and click "Authorize"
6. Try `GET /auth/me` - should see your profile!

### Option 2: Test Script

```powershell
python test_auth_simple.py
```

Should show:
```
✅ Login successful!
✅ /auth/me successful!
✅ /academic/timetable successful!
```

---

## 📝 Login Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@college.edu | **anything** | ACADEMIC_ADMIN |
| student@college.edu | **anything** | STUDENT |

**Password doesn't matter** - type "password", "123", "test", or anything - all work!

---

## 🎯 Your Database Connection

**Neon Connection String:**
```
postgresql://neondb_owner:npg_QTAf5hMHJLB8@ep-divine-bird-ahsyqwtc-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
```

**Already configured in `.env` as:**
```
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_QTAf5hMHJLB8@ep-divine-bird-ahsyqwtc-pooler.us-east-1.aws.neon.tech/neondb?ssl=require
```

---

## 📸 Test Timetable Upload

Once backend is running:

1. Go to http://localhost:8000/docs
2. Login as admin (get token)
3. Click "Authorize" and paste token
4. Find `POST /academic/timetable/upload`
5. Click "Try it out"
6. Upload a timetable image (JPEG/PNG)
7. AI will extract schedule entries
8. Review entries in response
9. Use `POST /academic/timetable/confirm` to save

---

## 🔧 Troubleshooting

### "Can't connect to database"

```powershell
# Test connection with Python
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://neondb_owner:npg_QTAf5hMHJLB8@ep-divine-bird-ahsyqwtc-pooler.us-east-1.aws.neon.tech/neondb'))"
```

If fails:
- Check Neon dashboard - is database active?
- Password might have changed
- Network/firewall blocking connection

### "Table doesn't exist"

```powershell
# Re-run setup
python setup_neon_db.py
```

Or manually run `neon_setup.sql` in Neon SQL Editor.

### "No module named asyncpg"

```powershell
pip install asyncpg
```

### Backend starts but 500 errors

Check backend terminal - it shows the actual Python error. Most common:
- Database connection failed → check DATABASE_URL
- Table missing → run setup_neon_db.py
- Syntax error → restart backend

---

## 📚 What's Available

### Auth Endpoints
- `POST /auth/login` - Login with email/password
- `POST /auth/register` - Register new user
- `GET /auth/me` - Get current user profile

### Timetable Endpoints (Admin only)
- `GET /academic/timetable` - Get timetable entries
- `POST /academic/timetable` - Create single entry
- `POST /academic/timetable/upload` - Upload image for OCR parsing
- `POST /academic/timetable/confirm` - Save reviewed entries
- `DELETE /academic/timetable/{id}` - Delete entry

### Other Endpoints
- `GET /academic/departments` - List departments
- `GET /academic/exams` - Get exam schedules
- `GET /academic/holidays` - Get holiday list
- Plus hostel, placement, clubs, notices, events, assignments, AI

Full API docs: http://localhost:8000/docs

---

## ✅ Quick Start Commands (Copy-Paste)

```powershell
# Everything in one go:
cd backend
pip install -r requirements.txt
pip install asyncpg python-dotenv
python setup_neon_db.py
python -m scripts.create_admin_simple
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs and login! 🚀

---

## 🎉 You're Ready!

The backend is fully functional with:
- ✅ Neon PostgreSQL database
- ✅ All tables created
- ✅ Admin and student users
- ✅ Simple authentication
- ✅ Timetable OCR + AI parsing
- ✅ Role-based access control

**Next:** Upload a timetable image to test the AI parsing! 📸
