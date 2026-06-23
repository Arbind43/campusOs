-- ============================================================
-- COMPLETE DATABASE SETUP FOR CAMPUS OS
-- Run this entire script in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- 1. USER PROFILES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'STUDENT',
    is_demo BOOLEAN NOT NULL DEFAULT false,
    department_id UUID,
    year_of_study INTEGER,
    hostel_room_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_profiles_email ON user_profiles(email);

-- ============================================================
-- 2. DEPARTMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(code)
);

-- ============================================================
-- 3. HOSTELS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS hostels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    warden_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 4. HOSTEL ROOMS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS hostel_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hostel_id UUID NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
    room_number VARCHAR(20) NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 2,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_hostel_rooms_hostel_id ON hostel_rooms(hostel_id);

-- ============================================================
-- 5. ADD FOREIGN KEYS TO USER_PROFILES
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_user_profiles_department_id') THEN
        ALTER TABLE user_profiles 
        ADD CONSTRAINT fk_user_profiles_department_id 
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_user_profiles_hostel_room_id') THEN
        ALTER TABLE user_profiles 
        ADD CONSTRAINT fk_user_profiles_hostel_room_id 
        FOREIGN KEY (hostel_room_id) REFERENCES hostel_rooms(id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_hostels_warden_id') THEN
        ALTER TABLE hostels 
        ADD CONSTRAINT fk_hostels_warden_id 
        FOREIGN KEY (warden_id) REFERENCES user_profiles(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================
-- 6. ROLES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL DEFAULT ''
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_roles_name ON roles(name);

-- Seed roles
INSERT INTO roles (name, description) VALUES
    ('SUPER_ADMIN',            'Institute-level super administrator'),
    ('ACADEMIC_ADMIN',         'Academic office administrator'),
    ('HOSTEL_ADMIN',           'Hostel warden / administrator'),
    ('PLACEMENT_ADMIN',        'Placement cell administrator'),
    ('MESS_ADMIN',             'Mess manager'),
    ('CLUB_ADMIN',             'Club administrator'),
    ('FACULTY',                'Teaching faculty member'),
    ('PLACEMENT_COORDINATOR',  'Student placement coordinator (delegated)'),
    ('HOSTEL_COORDINATOR',     'Student hostel secretary (delegated)'),
    ('CLUB_COORDINATOR',       'Club lead / sports captain (delegated)'),
    ('STUDENT',                'Regular student')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- 7. USER_ROLES JOIN TABLE (RBAC)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    scope_id UUID,
    granted_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, role_id, scope_id)
);

CREATE INDEX IF NOT EXISTS ix_user_roles_user_id ON user_roles(user_id);

-- ============================================================
-- 8. TIMETABLES TABLE (MAIN TABLE FOR THIS FEATURE)
-- ============================================================
CREATE TABLE IF NOT EXISTS timetables (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester INTEGER NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    subject VARCHAR(100) NOT NULL,
    room VARCHAR(50),
    faculty_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_timetables_dept_id ON timetables(department_id);

-- ============================================================
-- 9. EXAM SCHEDULES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS exam_schedules (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester INTEGER NOT NULL,
    subject VARCHAR(100) NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    room VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_exam_schedules_dept_id ON exam_schedules(department_id);

-- ============================================================
-- 10. HOLIDAYS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 11. CLUBS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS clubs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    club_type VARCHAR(30) NOT NULL DEFAULT 'technical',
    description VARCHAR(500) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 12. CLUB MEMBERSHIPS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS club_memberships (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    club_id UUID NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    is_coordinator BOOLEAN NOT NULL DEFAULT false,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, club_id)
);

CREATE INDEX IF NOT EXISTS ix_club_memberships_user_id ON club_memberships(user_id);
CREATE INDEX IF NOT EXISTS ix_club_memberships_club_id ON club_memberships(club_id);

-- ============================================================
-- 13. NOTICES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS notices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    domain VARCHAR(30) NOT NULL,
    target_department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_notices_domain ON notices(domain);

-- ============================================================
-- 14. EVENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    domain VARCHAR(30) NOT NULL,
    event_date DATE NOT NULL,
    venue VARCHAR(150),
    requires_registration BOOLEAN NOT NULL DEFAULT false,
    registration_deadline DATE,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_events_domain ON events(domain);

-- ============================================================
-- 15. EVENT REGISTRATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS event_registrations (
    id SERIAL PRIMARY KEY,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(event_id, student_id)
);

CREATE INDEX IF NOT EXISTS ix_event_registrations_event_id ON event_registrations(event_id);

-- ============================================================
-- 16. PLACEMENT DRIVES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS placement_drives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(150) NOT NULL,
    job_role VARCHAR(150) NOT NULL,
    package_lpa NUMERIC(6,2),
    drive_date DATE,
    registration_deadline DATE,
    description TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 17. DRIVE REGISTRATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS drive_registrations (
    id SERIAL PRIMARY KEY,
    drive_id UUID NOT NULL REFERENCES placement_drives(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_drive_registrations_drive_id ON drive_registrations(drive_id);

-- ============================================================
-- 18. PLACEMENT NOTICES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS placement_notices (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    drive_id UUID REFERENCES placement_drives(id) ON DELETE SET NULL,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 19. MESS MENUS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS mess_menus (
    id SERIAL PRIMARY KEY,
    hostel_id UUID NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    items TEXT NOT NULL,
    is_special BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_mess_menus_hostel_id ON mess_menus(hostel_id);

-- ============================================================
-- 20. MESS NOTICES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS mess_notices (
    id SERIAL PRIMARY KEY,
    hostel_id UUID NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_mess_notices_hostel_id ON mess_notices(hostel_id);

-- ============================================================
-- 21. ASSIGNMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    subject VARCHAR(100) NOT NULL,
    due_date DATE NOT NULL,
    file_url VARCHAR(500),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester INTEGER,
    faculty_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_assignments_department_id ON assignments(department_id);

-- ============================================================
-- 22. SEED DATA - DEFAULT DEPARTMENT
-- ============================================================
INSERT INTO departments (id, name, code) VALUES
    (gen_random_uuid(), 'Computer Science & Engineering', 'CSE'),
    (gen_random_uuid(), 'Electronics & Communication', 'ECE'),
    (gen_random_uuid(), 'Mechanical Engineering', 'ME'),
    (gen_random_uuid(), 'Information Technology', 'IT')
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- 23. SEED DEMO USERS (Update these IDs to match your Supabase Auth users)
-- ============================================================
-- IMPORTANT: Replace these UUIDs with your actual Supabase Auth user IDs!
-- Go to Supabase Dashboard → Authentication → Users to find them.

-- Demo Student
INSERT INTO user_profiles (id, email, full_name, role, is_demo, department_id) VALUES
    ('e906678c-21c2-44c1-bcf5-a172c69d17f7', 'demo.student@campusos.app', 'Demo Student', 'STUDENT', true, 
     (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1))
ON CONFLICT (id) DO UPDATE SET 
    role = 'STUDENT',
    department_id = (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1);

-- Demo Admin (ACADEMIC_ADMIN)
INSERT INTO user_profiles (id, email, full_name, role, is_demo, department_id) VALUES
    ('cb253015-0448-49ec-aee6-70faef5e9113', 'demo.admin@campusos.app', 'Demo Admin', 'ACADEMIC_ADMIN', true, 
     (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1))
ON CONFLICT (id) DO UPDATE SET 
    role = 'ACADEMIC_ADMIN',
    department_id = (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1);

-- Demo Professor
INSERT INTO user_profiles (id, email, full_name, role, is_demo, department_id) VALUES
    ('f0103df7-cd9b-4988-bb6f-e92458e90502', 'demo.professor@campusos.app', 'Demo Professor', 'FACULTY', true,
     (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1))
ON CONFLICT (id) DO UPDATE SET 
    role = 'FACULTY',
    department_id = (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1);

-- ============================================================
-- 24. ASSIGN RBAC ROLES TO DEMO USERS
-- ============================================================
-- Give admin the ACADEMIC_ADMIN role in the RBAC table
INSERT INTO user_roles (user_id, role_id) VALUES
    ('cb253015-0448-49ec-aee6-70faef5e9113', (SELECT id FROM roles WHERE name = 'ACADEMIC_ADMIN')),
    ('e906678c-21c2-44c1-bcf5-a172c69d17f7', (SELECT id FROM roles WHERE name = 'STUDENT')),
    ('f0103df7-cd9b-4988-bb6f-e92458e90502', (SELECT id FROM roles WHERE name = 'FACULTY'))
ON CONFLICT (user_id, role_id, scope_id) DO NOTHING;

-- ============================================================
-- DONE! Your database is now fully set up.
-- 
-- Demo Credentials:
--   Student:  demo.student@campusos.app / demo1234
--   Admin:    demo.admin@campusos.app / demo1234
--   Professor: demo.professor@campusos.app / demo1234
--
-- The admin can now upload timetables!
-- ============================================================
