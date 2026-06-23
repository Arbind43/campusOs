"""
Comprehensive Database Connection & Health Check
Run: python check_db.py
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load .env from same directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "")

# These match the actual SQLAlchemy __tablename__ values in app/models/
EXPECTED_TABLES = [
    "user_profiles",       # app/models/user.py       -> UserProfile
    "roles",               # app/models/rbac.py       -> Role
    "user_roles",          # app/models/rbac.py       -> UserRole
    "departments",         # app/models/academic.py   -> Department
    "timetables",          # app/models/academic.py   -> Timetable
    "exam_schedules",      # app/models/academic.py   -> ExamSchedule
    "holidays",            # app/models/academic.py   -> Holiday
    "attendance_marks",    # app/models/attendance.py -> AttendanceRecord
    "mess_schedule",       # app/models/mess.py       -> MessSchedule
    "mess_ratings",        # app/models/mess.py       -> MessRating
    "chat_messages",       # app/models/chat.py       -> ChatMessage
    "hostels",             # app/models/hostel.py     -> Hostel
    "hostel_rooms",        # app/models/hostel.py     -> HostelRoom
    "mess_menus",          # app/models/hostel.py     -> MessMenu
    "mess_notices",        # app/models/hostel.py     -> MessNotice
    "placement_drives",    # app/models/placement.py  -> PlacementDrive
    "drive_registrations", # app/models/placement.py  -> DriveRegistration
    "placement_notices",   # app/models/placement.py  -> PlacementNotice
    "clubs",               # app/models/club.py       -> Club
    "club_memberships",    # app/models/club.py       -> ClubMembership
    "notices",             # app/models/content.py    -> Notice
    "events",              # app/models/content.py    -> Event
    "event_registrations", # app/models/content.py    -> EventRegistration
    "assignments",         # app/models/content.py    -> Assignment
    "wellbeing_checkins",  # app/models/wellbeing.py  -> WellbeingCheckin
]

SEP = "=" * 65


async def check_database():
    try:
        import asyncpg
    except ImportError:
        print("ERROR: asyncpg not installed. Run: pip install asyncpg")
        return

    print(SEP)
    print("  DATABASE CONNECTION & HEALTH CHECK")
    print(SEP)

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in .env!")
        return

    # Mask password for display
    masked = DATABASE_URL
    try:
        parts = DATABASE_URL.split("@")
        creds = parts[0].split("//")[1]
        user = creds.split(":")[0]
        host_part = parts[1]
        masked = f"postgresql://{user}:***@{host_part}"
    except Exception:
        pass

    print(f"\nConnecting to:\n   {masked}\n")

    # Convert SQLAlchemy URL to raw asyncpg URL
    conn_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    try:
        conn = await asyncpg.connect(conn_url, timeout=10)
        print("[OK] CONNECTION SUCCESS - Database is reachable!\n")
    except Exception as e:
        print(f"[FAIL] CONNECTION FAILED: {e}\n")
        print("Possible causes:")
        print("  - Wrong DATABASE_URL in .env")
        print("  - Neon project is paused / deleted")
        print("  - Network / firewall blocking connection")
        return

    try:
        # Server Info
        version = await conn.fetchval("SELECT version()")
        print(f"[INFO] Server : {version[:70]}")

        db_name = await conn.fetchval("SELECT current_database()")
        print(f"[INFO] Database: {db_name}\n")

        # List all public tables
        rows = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        existing_tables = {r["table_name"] for r in rows}

        print(f"{'─'*65}")
        print(f"  TABLES IN DATABASE  ({len(existing_tables)} found)")
        print(f"{'─'*65}")
        for t in sorted(existing_tables):
            print(f"   [OK]  {t}")

        # Check expected tables
        print(f"\n{'─'*65}")
        print("  EXPECTED TABLES CHECK")
        print(f"{'─'*65}")

        missing = []
        for expected in EXPECTED_TABLES:
            if expected in existing_tables:
                print(f"   [OK]      {expected}")
            else:
                print(f"   [MISSING] {expected}")
                missing.append(expected)

        # Row counts
        print(f"\n{'─'*65}")
        print("  ROW COUNTS (existing tables only)")
        print(f"{'─'*65}")
        for t in sorted(existing_tables):
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM "{t}"')
                status = "[OK]    " if count > 0 else "[EMPTY] "
                print(f"   {status}  {t:<35} {count:>6} rows")
            except Exception as ex:
                print(f"   [ERROR]  {t:<35} ERROR: {ex}")

        # Summary
        print(f"\n{SEP}")
        print("  SUMMARY")
        print(SEP)
        print(f"  Connection  : OK")
        print(f"  Tables found: {len(existing_tables)}")
        print(f"  Missing     : {len(missing)}")
        if missing:
            print(f"\n  WARNING - Missing tables. Run to create them:")
            print(f"      python setup_neon_db.py")
            for m in missing:
                print(f"      - {m}")
        else:
            print(f"\n  SUCCESS - All expected tables exist!")
            print(f"            Database is fully set up and connected.")
        print(SEP)

    except Exception as e:
        print(f"ERROR during checks: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_database())
