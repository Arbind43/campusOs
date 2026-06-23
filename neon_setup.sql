-- ============================================================================
-- CampusOS Database Schema for Neon PostgreSQL
-- Run this in Neon SQL Editor to create all tables
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- DEPARTMENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- USER PROFILES
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'STUDENT',
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    year_of_study INTEGER CHECK (year_of_study >= 1 AND year_of_study <= 8),
    hostel_room_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_department ON user_profiles(department_id);

-- ============================================================================
-- RBAC - ROLES
-- ============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- ============================================================================
-- RBAC - USER ROLES (many-to-many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    scope_id UUID,
    granted_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_role_scope UNIQUE (user_id, role_id, scope_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- ============================================================================
-- TIMETABLES
-- ============================================================================
CREATE TABLE IF NOT EXISTS timetables (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    day_of_week VARCHAR(10) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    subject VARCHAR(100) NOT NULL,
    room VARCHAR(50),
    faculty_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_timetables_department ON timetables(department_id);
CREATE INDEX IF NOT EXISTS idx_timetables_day ON timetables(day_of_week);

-- ============================================================================
-- EXAM SCHEDULES
-- ============================================================================
CREATE TABLE IF NOT EXISTS exam_schedules (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    subject VARCHAR(100) NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    room VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exam_schedules_department ON exam_schedules(department_id);
CREATE INDEX IF NOT EXISTS idx_exam_schedules_date ON exam_schedules(exam_date);

-- ============================================================================
-- HOLIDAYS
-- ============================================================================
CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE UNIQUE NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(holiday_date);

-- ============================================================================
-- HOSTELS
-- ============================================================================
CREATE TABLE IF NOT EXISTS hostels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    warden_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hostel_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hostel_id UUID NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
    room_number VARCHAR(20) NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 2 CHECK (capacity >= 1 AND capacity <= 10),
    CONSTRAINT uq_hostel_room UNIQUE (hostel_id, room_number)
);

-- ============================================================================
-- MESS MENU
-- ============================================================================
CREATE TABLE IF NOT EXISTS mess_menus (
    id SERIAL PRIMARY KEY,
    hostel_id UUID NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    items TEXT NOT NULL,
    is_special BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mess_notices (
    id SERIAL PRIMARY KEY,
    hostel_id UUID NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- PLACEMENT
-- ============================================================================
CREATE TABLE IF NOT EXISTS placement_drives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(150) NOT NULL,
    job_role VARCHAR(150) NOT NULL,
    package_lpa NUMERIC(10, 2) CHECK (package_lpa >= 0),
    drive_date DATE,
    registration_deadline DATE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS placement_notices (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    drive_id UUID REFERENCES placement_drives(id) ON DELETE SET NULL,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- CLUBS
-- ============================================================================
CREATE TABLE IF NOT EXISTS clubs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    club_type VARCHAR(20) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- NOTICES (General)
-- ============================================================================
CREATE TABLE IF NOT EXISTS notices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    domain VARCHAR(20) NOT NULL,
    target_department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notices_domain ON notices(domain);
CREATE INDEX IF NOT EXISTS idx_notices_pinned ON notices(is_pinned);

-- ============================================================================
-- EVENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    domain VARCHAR(20) NOT NULL,
    event_date DATE NOT NULL,
    venue VARCHAR(255),
    requires_registration BOOLEAN NOT NULL DEFAULT FALSE,
    registration_deadline DATE,
    created_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_domain ON events(domain);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);

-- ============================================================================
-- ASSIGNMENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(100) NOT NULL,
    due_date DATE NOT NULL,
    file_url TEXT,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester INTEGER CHECK (semester >= 1 AND semester <= 8),
    faculty_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assignments_department ON assignments(department_id);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date);

-- ============================================================================
-- SEED DATA - Roles
-- ============================================================================
INSERT INTO roles (name, description) VALUES
    ('SUPER_ADMIN', 'Full system access'),
    ('ACADEMIC_ADMIN', 'Manages academic data'),
    ('HOSTEL_ADMIN', 'Manages hostels and mess'),
    ('PLACEMENT_ADMIN', 'Manages placement drives'),
    ('MESS_ADMIN', 'Manages mess menus'),
    ('CLUB_ADMIN', 'Manages clubs'),
    ('FACULTY', 'Faculty member'),
    ('PLACEMENT_COORDINATOR', 'Placement team member'),
    ('HOSTEL_COORDINATOR', 'Hostel team member'),
    ('CLUB_COORDINATOR', 'Club team member'),
    ('STUDENT', 'Student')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- SEED DATA - Department
-- ============================================================================
INSERT INTO departments (name, code) VALUES
    ('Computer Science & Engineering', 'CSE'),
    ('Information Technology', 'IT'),
    ('Electronics & Communication', 'ECE'),
    ('Mechanical Engineering', 'MECH'),
    ('Civil Engineering', 'CIVIL')
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- Done!
-- ============================================================================
SELECT 'Database setup complete!' AS status;
SELECT COUNT(*) AS department_count FROM departments;
SELECT COUNT(*) AS role_count FROM roles;
