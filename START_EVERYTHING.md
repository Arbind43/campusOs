# 🚀 Start Everything - Complete Guide

## Quick Start (2 Terminals)

### Terminal 1: Backend

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend: http://localhost:8000  
✅ API Docs: http://localhost:8000/docs

### Terminal 2: Frontend

```powershell
cd frontend
npm run dev
```

✅ Frontend: http://localhost:3000

---

## 🎯 Test the Complete System

### 1. Login

1. Open **http://localhost:3000**
2. Login with:
   - Email: `admin@college.edu`
   - Password: `anything`
3. Click "Sign In"
4. Redirected to dashboard ✅

### 2. View Timetable

1. Go to **http://localhost:3000/dashboard/timetable**
2. Should see empty timetable (no entries yet)

### 3. Upload Timetable Image

1. Click "Upload Timetable" button
2. Select a timetable image (JPEG/PNG)
3. **AI will extract the schedule automatically!** 🤖
4. Review parsed entries
5. Click "Confirm" to save

---

## 🔥 What Works Now

✅ **Backend (Python FastAPI)**
- Simple email/password authentication
- JWT token generation
- Neon PostgreSQL database
- Timetable CRUD operations
- **OCR + AI parsing with Groq Vision**
- Role-based access control

✅ **Frontend (Next.js + TypeScript)**
- Login/logout
- Protected routes
- Timetable display
- File upload
- API integration
- Role-based UI

✅ **Features**
- Admin can upload timetable images
- AI extracts schedule (day, time, subject, room, faculty)
- Students can view timetable
- Department-based filtering
- Semester filtering

---

## 📝 Test Accounts

| Email | Password | Role | Can Upload? |
|-------|----------|------|-------------|
| admin@college.edu | anything | ACADEMIC_ADMIN | ✅ Yes |
| student@college.edu | anything | STUDENT | ❌ No (view only) |

---

## 🎯 Test the AI Feature

1. Login as admin
2. Go to timetable page
3. Upload any timetable image
4. AI will:
   - Extract text using OCR
   - Parse schedule entries
   - Find day, time, subject, room, faculty
   - Return structured data
5. Review and save!

---

## 📊 Architecture

```
Frontend (Next.js)
     ↓ HTTP
Backend (FastAPI)
     ↓ SQL
Neon (PostgreSQL)
     ↓
Groq API (OCR + AI)
```

---

## 🔧 Environment Variables

### Backend (`.env`)
```env
DATABASE_URL=postgresql+asyncpg://neondb_owner:...@ep-divine-bird-ahsyqwtc-pooler.c-3.us-east-1.aws.neon.tech/neondb?ssl=require
GROQ_API_KEY=your_groq_api_key_here
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📁 Key Files

### Backend
- `app/routers/auth.py` - Login/register endpoints
- `app/routers/academic.py` - Timetable CRUD + upload
- `app/services/ocr.py` - Groq Vision OCR
- `app/core/security.py` - JWT token handling
- `app/models/academic.py` - Database models

### Frontend
- `src/lib/auth-api.ts` - Auth API calls
- `src/lib/timetable-api.ts` - Timetable API calls
- `src/components/auth/LoginForm.tsx` - Login UI
- `src/app/dashboard/timetable/page.tsx` - Timetable page
- `src/store/auth.ts` - Auth state (token + user)

---

## 🎉 Everything is Working!

You now have a complete system:
- ✅ Authentication working
- ✅ Database connected (Neon)
- ✅ Frontend + Backend integrated
- ✅ AI-powered timetable parsing
- ✅ Role-based access control
- ✅ File upload working
- ✅ Production-ready architecture

**Go test it! Upload a timetable image and watch the AI work!** 🚀

---

## 📞 Need Help?

**Backend not starting?**
- Check DATABASE_URL in `.env`
- Make sure tables exist in Neon
- Run: `python -m scripts.create_admin_simple`

**Frontend not loading?**
- Check NEXT_PUBLIC_API_URL in `.env.local`
- Make sure backend is running on port 8000
- Clear browser cache and localStorage

**Can't login?**
- Backend must be running
- Check backend terminal for errors
- Try Swagger UI first: http://localhost:8000/docs

**Upload fails?**
- Check GROQ_API_KEY in backend `.env`
- Image must be JPEG or PNG
- Max size: 10MB
- Must login as admin

---

## 🎯 Next: Build More Features!

Now that auth + timetable is working, you can add:
- Exam schedules
- Holidays
- Hostel management
- Placement tracking
- Clubs
- Notices
- Events
- AI assistant (using campus data)

All the groundwork is done! 🎉
