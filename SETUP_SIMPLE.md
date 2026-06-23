# Simple Setup Guide - MVP Auth Fixed

## What Changed
- **Removed all Supabase JWT complexity**
- **Simple email/password login** (password doesn't matter in dev - any password works)
- **Auto-creates users** on first login
- **Email-based role assignment**: admin@* = ACADEMIC_ADMIN, others = STUDENT

## Setup Steps

### 1. Install Backend Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

### 2. Create Admin User in Database
```powershell
python -m scripts.create_admin_simple
```

This creates:
- `admin@college.edu` with role ACADEMIC_ADMIN
- `student@college.edu` with role STUDENT
- Password: **any password works** (dev mode)

### 3. Start Backend
```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test Backend (Optional)
```powershell
# In a new terminal
python test_auth_simple.py
```

## API Endpoints

### Login
```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@college.edu",
  "password": "anything"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "admin@college.edu",
    "full_name": "Admin User",
    "role": "ACADEMIC_ADMIN",
    "roles": ["ACADEMIC_ADMIN"]
  }
}
```

### Register
```bash
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "email": "newuser@college.edu",
  "password": "anything",
  "full_name": "New User",
  "role": "student"
}
```

### Get Current User
```bash
GET http://localhost:8000/api/v1/auth/me
Authorization: Bearer <token>
```

### Get Timetable
```bash
GET http://localhost:8000/api/v1/academic/timetable
Authorization: Bearer <token>
```

### Upload Timetable (Admin Only)
```bash
POST http://localhost:8000/api/v1/academic/timetable/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image file>
```

## Frontend Changes Needed

Update the login function to use the new endpoint:

```typescript
// src/lib/auth-api.ts
export async function login(email: string, password: string) {
  const response = await api.post('/auth/login', { email, password });
  const { access_token, user } = response.data;
  localStorage.setItem('token', access_token);
  return user;
}
```

## Test Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@college.edu | anything | ACADEMIC_ADMIN |
| student@college.edu | anything | STUDENT |

## Troubleshooting

### Backend won't start
- Check `.env` file has correct `DATABASE_URL`
- Make sure PostgreSQL is running
- Run migrations: `alembic upgrade head`

### 401 Unauthorized
- Make sure you're sending the token in Authorization header
- Token format: `Bearer <token>`

### 403 Forbidden
- User doesn't have required role
- Check user role in database: `SELECT email, role FROM user_profiles;`

### 500 Internal Server Error
- Check backend terminal for Python traceback
- Most likely database connection issue
- Verify tables exist in database

## Next Steps

1. ✅ Fix authentication (DONE)
2. Test timetable upload with image
3. Test OCR + AI parsing
4. Build frontend timetable upload component
5. Test end-to-end flow
