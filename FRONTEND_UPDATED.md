# Frontend Updated for New Authentication

## ✅ Changes Made

I've updated your frontend to use the new simple authentication system (no more Supabase Auth).

### Files Updated:

1. **`src/lib/auth-api.ts`** - New login/register API calls
2. **`src/lib/api.ts`** - Simplified to use JWT token from store
3. **`src/store/auth.ts`** - Now stores token + user (persisted to localStorage)
4. **`src/components/auth/LoginForm.tsx`** - Calls backend `/auth/login` directly
5. **`src/components/auth/AuthProvider.tsx`** - Validates token on mount
6. **`src/components/auth/AuthGuard.tsx`** - Checks auth store instead of Supabase

---

## 🚀 How to Test

### 1. Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend will run on **http://localhost:3000**

### 2. Login

1. Open http://localhost:3000
2. You should see the login form
3. Login with:
   - **Email**: `admin@college.edu`
   - **Password**: `anything` (any password works in dev)
4. Click "Sign In"
5. You'll be redirected to `/dashboard`

### 3. Test Protected Routes

Once logged in:
- Go to **`/dashboard/timetable`** - Should show timetable page
- Upload a timetable image
- AI will extract the schedule

---

## 🔑 How Authentication Works Now

### Login Flow:

```
User enters email + password
     ↓
POST /api/v1/auth/login
     ↓
Backend validates (any password works in dev)
     ↓
Backend returns { access_token, user }
     ↓
Frontend stores token in localStorage
     ↓
All API requests include: Authorization: Bearer <token>
```

### API Requests:

```typescript
// Automatically adds Authorization header
const response = await apiClient.get('/academic/timetable');
// Headers: { Authorization: "Bearer eyJhbGc..." }
```

### Logout:

```typescript
const { clearAuth } = useAuthStore();
clearAuth(); // Clears token and user from localStorage
router.push('/'); // Redirect to home
```

---

## 📝 Available Test Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@college.edu | anything | ACADEMIC_ADMIN |
| student@college.edu | anything | STUDENT |

**Note:** Password literally doesn't matter - type "test", "123", or "asdf" - all work!

---

## 🎯 Next Steps

1. ✅ Start frontend: `npm run dev`
2. ✅ Login at http://localhost:3000
3. ✅ Go to `/dashboard/timetable`
4. ✅ Upload a timetable image
5. ✅ Watch AI extract the schedule!

---

## 🔧 Troubleshooting

### "Failed to fetch" error

- **Backend not running** - Start with: `python -m uvicorn app.main:app --reload`
- **Wrong API URL** - Check `frontend/.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`

### Login fails with 401

- Backend database tables not created - Run `neon_setup.sql` in Neon SQL Editor
- Admin user not created - Run `python -m scripts.create_admin_simple`

### Token expires

- Token expires after 7 days (configurable in `backend/app/core/security.py`)
- Just login again to get a new token

### Can't access protected routes

- Clear browser localStorage and login again
- Check console for errors

---

## 🎉 You're Ready!

Your frontend now:
- ✅ Uses backend authentication (no Supabase)
- ✅ Stores token in localStorage
- ✅ Auto-attaches token to all API requests
- ✅ Redirects to login if token invalid
- ✅ Works with role-based access control

**Test it now!** Open http://localhost:3000 and login! 🚀
