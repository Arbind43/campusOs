"""RBAC full schema — all domain tables + user_profiles extensions

Revision ID: 002
Revises: 001
Create Date: 2026-06-13

Adds:
  - roles
  - user_roles
  - departments
  - timetables
  - exam_schedules
  - holidays
  - hostels
  - hostel_rooms
  - mess_menus
  - mess_notices
  - placement_drives
  - drive_registrations
  - placement_notices
  - clubs
  - club_memberships
  - notices
  - events
  - event_registrations
  - assignments

Alters:
  - user_profiles: adds department_id, hostel_room_id, year_of_study; widens role to 50 chars
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Departments (no FKs other than self — create first)             #
    # ------------------------------------------------------------------ #
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # ------------------------------------------------------------------ #
    # 2. Hostels                                                          #
    # ------------------------------------------------------------------ #
    op.create_table(
        "hostels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("warden_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # warden_id FK added after user_profiles alter (circular ref avoided)
    )

    # ------------------------------------------------------------------ #
    # 3. Hostel Rooms (FK → hostels)                                      #
    # ------------------------------------------------------------------ #
    op.create_table(
        "hostel_rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_number", sa.String(20), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_hostel_rooms_hostel_id", "hostel_rooms", ["hostel_id"])

    # ------------------------------------------------------------------ #
    # 4. Alter user_profiles                                              #
    # ------------------------------------------------------------------ #
    # Widen role column
    op.alter_column("user_profiles", "role",
                     existing_type=sa.String(20),
                     type_=sa.String(50),
                     existing_nullable=False)
    # Update default to STUDENT
    op.execute("UPDATE user_profiles SET role = 'STUDENT' WHERE role = 'student'")
    op.execute("UPDATE user_profiles SET role = 'FACULTY' WHERE role = 'professor'")

    op.add_column("user_profiles",
                  sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("user_profiles",
                  sa.Column("year_of_study", sa.Integer(), nullable=True))
    op.add_column("user_profiles",
                  sa.Column("hostel_room_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key(
        "fk_user_profiles_department_id", "user_profiles",
        "departments", ["department_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_user_profiles_hostel_room_id", "user_profiles",
        "hostel_rooms", ["hostel_room_id"], ["id"], ondelete="SET NULL"
    )

    # Now add warden_id FK on hostels → user_profiles
    op.create_foreign_key(
        "fk_hostels_warden_id", "hostels",
        "user_profiles", ["warden_id"], ["id"], ondelete="SET NULL"
    )

    # ------------------------------------------------------------------ #
    # 5. Roles table                                                      #
    # ------------------------------------------------------------------ #
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    # Seed role rows
    op.execute("""
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
    """)

    # ------------------------------------------------------------------ #
    # 6. UserRole join table                                              #
    # ------------------------------------------------------------------ #
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", "role_id", "scope_id", name="uq_user_role_scope"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])

    # ------------------------------------------------------------------ #
    # 7. Timetables                                                       #
    # ------------------------------------------------------------------ #
    op.create_table(
        "timetables",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.String(10), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("room", sa.String(50), nullable=True),
        sa.Column("faculty_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_timetables_dept_id", "timetables", ["department_id"])

    # ------------------------------------------------------------------ #
    # 8. Exam Schedules                                                   #
    # ------------------------------------------------------------------ #
    op.create_table(
        "exam_schedules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("room", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_exam_schedules_dept_id", "exam_schedules", ["department_id"])

    # ------------------------------------------------------------------ #
    # 9. Holidays                                                         #
    # ------------------------------------------------------------------ #
    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("holiday_date", sa.Date(), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------ #
    # 10. Mess Menus                                                      #
    # ------------------------------------------------------------------ #
    op.create_table(
        "mess_menus",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("day_of_week", sa.String(10), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=False),
        sa.Column("items", sa.Text(), nullable=False),
        sa.Column("is_special", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mess_menus_hostel_id", "mess_menus", ["hostel_id"])

    # ------------------------------------------------------------------ #
    # 11. Mess Notices                                                    #
    # ------------------------------------------------------------------ #
    op.create_table(
        "mess_notices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["user_profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_mess_notices_hostel_id", "mess_notices", ["hostel_id"])

    # ------------------------------------------------------------------ #
    # 12. Placement Drives                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "placement_drives",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(150), nullable=False),
        sa.Column("job_role", sa.String(150), nullable=False),
        sa.Column("package_lpa", sa.Numeric(6, 2), nullable=True),
        sa.Column("drive_date", sa.Date(), nullable=True),
        sa.Column("registration_deadline", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["user_profiles.id"], ondelete="SET NULL"),
    )

    # ------------------------------------------------------------------ #
    # 13. Drive Registrations                                             #
    # ------------------------------------------------------------------ #
    op.create_table(
        "drive_registrations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("drive_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["drive_id"], ["placement_drives.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["user_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_drive_registrations_drive_id", "drive_registrations", ["drive_id"])

    # ------------------------------------------------------------------ #
    # 14. Placement Notices                                               #
    # ------------------------------------------------------------------ #
    op.create_table(
        "placement_notices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("drive_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["drive_id"], ["placement_drives.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["user_profiles.id"], ondelete="SET NULL"),
    )

    # ------------------------------------------------------------------ #
    # 15. Clubs                                                           #
    # ------------------------------------------------------------------ #
    op.create_table(
        "clubs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("club_type", sa.String(30), nullable=False, server_default="technical"),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------ #
    # 16. Club Memberships                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "club_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("club_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_coordinator", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "club_id", name="uq_club_membership"),
    )
    op.create_index("ix_club_memberships_user_id", "club_memberships", ["user_id"])
    op.create_index("ix_club_memberships_club_id", "club_memberships", ["club_id"])

    # ------------------------------------------------------------------ #
    # 17. Notices                                                         #
    # ------------------------------------------------------------------ #
    op.create_table(
        "notices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(30), nullable=False),
        sa.Column("target_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["target_department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["user_profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_notices_domain", "notices", ["domain"])

    # ------------------------------------------------------------------ #
    # 18. Events                                                          #
    # ------------------------------------------------------------------ #
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("domain", sa.String(30), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("venue", sa.String(150), nullable=True),
        sa.Column("requires_registration", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("registration_deadline", sa.Date(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["user_profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_events_domain", "events", ["domain"])

    # ------------------------------------------------------------------ #
    # 19. Event Registrations                                             #
    # ------------------------------------------------------------------ #
    op.create_table(
        "event_registrations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("event_id", "student_id", name="uq_event_registration"),
    )
    op.create_index("ix_event_registrations_event_id", "event_registrations", ["event_id"])

    # ------------------------------------------------------------------ #
    # 20. Assignments                                                     #
    # ------------------------------------------------------------------ #
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["faculty_id"], ["user_profiles.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_assignments_department_id", "assignments", ["department_id"])


def downgrade() -> None:
    # Drop in reverse order of creation
    op.drop_table("assignments")
    op.drop_table("event_registrations")
    op.drop_table("events")
    op.drop_table("notices")
    op.drop_table("club_memberships")
    op.drop_table("clubs")
    op.drop_table("placement_notices")
    op.drop_table("drive_registrations")
    op.drop_table("placement_drives")
    op.drop_table("mess_notices")
    op.drop_table("mess_menus")
    op.drop_table("holidays")
    op.drop_table("exam_schedules")
    op.drop_table("timetables")
    op.drop_table("user_roles")
    op.drop_table("roles")

    # Revert user_profiles
    op.drop_constraint("fk_user_profiles_department_id", "user_profiles", type_="foreignkey")
    op.drop_constraint("fk_user_profiles_hostel_room_id", "user_profiles", type_="foreignkey")
    op.drop_column("user_profiles", "hostel_room_id")
    op.drop_column("user_profiles", "year_of_study")
    op.drop_column("user_profiles", "department_id")
    op.alter_column("user_profiles", "role",
                     existing_type=sa.String(50),
                     type_=sa.String(20),
                     existing_nullable=False)

    op.drop_constraint("fk_hostels_warden_id", "hostels", type_="foreignkey")
    op.drop_table("hostel_rooms")
    op.drop_table("hostels")
    op.drop_table("departments")
