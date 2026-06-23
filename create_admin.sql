-- ============================================================
-- CREATE ADMIN USER IN DATABASE
-- ============================================================
-- STEP 1: First create the user in Supabase Auth:
--   Go to Supabase Dashboard → Authentication → Users → Add User
--   Email: admin@campusos.app
--   Password: Uday@123
--   Then copy the UUID from the user list
--
-- STEP 2: Replace the UUID below with the one you copied
-- ============================================================

-- Make sure department exists
INSERT INTO departments (id, name, code) VALUES
    (gen_random_uuid(), 'Computer Science & Engineering', 'CSE')
ON CONFLICT (code) DO NOTHING;

-- Insert admin user profile
-- ⚠️ REPLACE THIS UUID with the one from Supabase Auth Dashboard!
INSERT INTO user_profiles (id, email, full_name, role, is_demo, department_id) VALUES
    (
        '00000000-0000-0000-0000-000000000000',  -- ← REPLACE WITH YOUR ACTUAL UUID FROM SUPABASE AUTH
        'admin@campusos.app',
        'Admin',
        'ACADEMIC_ADMIN',
        false,
        (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1)
    )
ON CONFLICT (id) DO UPDATE SET
    role = 'ACADEMIC_ADMIN',
    full_name = 'Admin',
    department_id = (SELECT id FROM departments WHERE code = 'CSE' LIMIT 1);

-- Also assign RBAC role
INSERT INTO user_roles (user_id, role_id) VALUES
    (
        '00000000-0000-0000-0000-000000000000',  -- ← SAME UUID HERE
        (SELECT id FROM roles WHERE name = 'ACADEMIC_ADMIN')
    )
ON CONFLICT (user_id, role_id, scope_id) DO NOTHING;

-- Verify it worked
SELECT id, email, full_name, role, department_id FROM user_profiles WHERE email = 'admin@campusos.app';
