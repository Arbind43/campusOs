# 🔐 Login Credentials

## Test Users (Dev Mode - Any Password Works!)

### Admin User
- **Email**: `admin@college.edu`
- **Password**: `any-password` (or literally type anything)
- **Role**: ACADEMIC_ADMIN
- **Department**: CSE (Computer Science & Engineering)
- **Permissions**: Can upload/create timetables, manage content

### Student User
- **Email**: `student@college.edu`
- **Password**: `any-password` (or literally type anything)
- **Role**: STUDENT
- **Department**: CSE (Computer Science & Engineering)
- **Year**: 2nd year
- **Permissions**: Can view timetables, events, notices (read-only)

---

## How to Test Timetable Feature

### Step 1: Login as Admin
1. Go to `http://localhost:3000`
2. Login with `admin@college.edu` (password doesn't matter)
3. You'll see the **Admin Dashboard**

### Step 2: Create Timetable
1. Click on **"Timetable"** in the sidebar
2. Choose one of:
   - **Upload Image** - Drag/drop a timetable image for OCR
   - **Create Manually** - Click "Create Timetable Manually (Skip OCR)"

### Step 3: Add Entries
If using manual creation:
1. Fill in the form:
   - Subject (e.g., "Data Structures")
   - Day of week (e.g., "Monday")
   - Start time (e.g., "09:00")
   - End time (e.g., "10:30")
   - Room (optional, e.g., "A101")
   - Faculty (optional, e.g., "Dr. Smith")
2. Click **"Add Entry"**
3. Repeat to add more classes
4. Click **"Confirm & Save Timetable"**

### Step 4: Login as Student
1. **Logout** from admin account
2. Login with `student@college.edu` (password doesn't matter)
3. You'll see the **Student Dashboard**
4. Click **"Timetable"** in the sidebar
5. ✅ You should see all the timetable entries created by admin!

---

## Department Assignment

Both admin and student users are assigned to the **CSE (Computer Science & Engineering)** department, so:
- Admin creates timetable → saves with `department_id = CSE`
- Student views timetable → filters by `department_id = CSE`
- **Result**: Student sees admin's timetable! 🎉

---

## Creating More Users

To create additional users (different departments, roles, etc.):

```python
# Create a new script or modify create_admin_simple.py
python -m scripts.create_admin_simple
```

Or use SQL directly in Neon:
```sql
INSERT INTO user_profiles (id, email, full_name, role, department_id, year_of_study, is_demo)
VALUES (
  gen_random_uuid(),
  'student2@college.edu',
  'John Doe',
  'STUDENT',
  (SELECT id FROM departments WHERE code = 'CSE'),
  3,
  false
);
```

---

## Database Connection

- **Provider**: Neon PostgreSQL
- **Connection**: Already configured in `.env`
- **Tables**: All created via `neon_setup.sql`
- **Admin User ID**: `6cec280a-4258-46ec-901b-f6382976a69f`
- **Student User ID**: `49f1b1c4-c09d-4338-974b-aee7b2cec64b`
- **CSE Department ID**: Check with `SELECT id FROM departments WHERE code = 'CSE'`

---

## Troubleshooting

### Student can't see timetable
- Check student has `department_id` assigned
- Check admin created timetable for same department
- Check timetable entries exist: `SELECT * FROM timetables WHERE department_id = (SELECT id FROM departments WHERE code = 'CSE')`

### Login not working
- Backend must be running: `cd backend && python -m uvicorn app.main:app --reload`
- Frontend must be running: `cd frontend && npm run dev`
- Check browser console for errors

### Timetable not saving
- Check admin has `department_id` assigned
- Check browser console/network tab for errors
- Check backend logs for error messages
