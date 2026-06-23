# Manual Database Setup for Neon (If Script Fails)

If `setup_neon_db.py` fails with SSL errors, follow these steps:

## Step 1: Go to Neon Dashboard

1. Open https://console.neon.tech/
2. Log in to your account
3. Select your project
4. Click "SQL Editor" in the left sidebar

## Step 2: Run SQL Script

1. Open the file `neon_setup.sql` in a text editor
2. **Copy ALL the SQL code** (Ctrl+A, Ctrl+C)
3. **Paste it into the Neon SQL Editor**
4. Click **"Run"** button

You should see:
```
Database setup complete!
department_count: 5
role_count: 11
```

## Step 3: Verify Tables Were Created

Run this query in Neon SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

You should see these tables:
- assignments
- clubs
- departments
- events
- exam_schedules
- holidays
- hostel_rooms
- hostels
- mess_menus
- mess_notices
- notices
- placement_drives
- placement_notices
- roles
- timetables
- user_profiles
- user_roles

## Step 4: Create Admin User

Back in your terminal:

```powershell
cd backend
python -m scripts.create_admin_simple
```

This should work now and create:
- admin@college.edu (ACADEMIC_ADMIN)
- student@college.edu (STUDENT)

## Step 5: Start Backend

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 6: Test Login

Open http://localhost:8000/docs and try:

```json
{
  "email": "admin@college.edu",
  "password": "test"
}
```

Should work! ✅
