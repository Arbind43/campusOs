"""
Seed three demo accounts with different roles.

Run this after database is configured:
    python -m scripts.seed_demo_roles
"""
import asyncio
import uuid

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import UserProfile
from app.models.academic import Department

# Demo account UUIDs from Supabase
DEMO_ACCOUNTS = [
    {
        "id": uuid.UUID("e906678c-21c2-44c1-bcf5-a172c69d17f7"),
        "email": "demo.student@campusos.app",
        "name": "Demo Student",
        "role": "STUDENT",
    },
    {
        "id": uuid.UUID("cb253015-0448-49ec-aee6-70faef5e9113"),
        "email": "demo.admin@campusos.app",
        "name": "Demo Admin",
        "role": "ACADEMIC_ADMIN",
    },
    {
        "id": uuid.UUID("f0103df7-cd9b-4988-bb6f-e92458e90502"),
        "email": "demo.professor@campusos.app",
        "name": "Demo Professor",
        "role": "FACULTY",
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        # Ensure a default department exists for the admin
        result = await db.execute(select(Department).where(Department.code == "CSE"))
        dept = result.scalar_one_or_none()
        if not dept:
            dept = Department(name="Computer Science & Engineering", code="CSE")
            db.add(dept)
            await db.flush()
            print(f"✓ Created default department: CSE (id={dept.id})")

        for account in DEMO_ACCOUNTS:
            # Check if profile exists
            result = await db.execute(
                select(UserProfile).where(UserProfile.id == account["id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update department_id for admin accounts if not set
                if account["role"] in ("ACADEMIC_ADMIN", "SUPER_ADMIN") and not existing.department_id:
                    existing.department_id = dept.id
                    print(f"✓ Updated {account['name']} with department CSE")
                else:
                    print(f"✓ {account['name']} profile already exists")
                continue

            # Create profile - assign department for admin and faculty
            department_id = dept.id if account["role"] in ("ACADEMIC_ADMIN", "SUPER_ADMIN", "FACULTY") else None
            
            profile = UserProfile(
                id=account["id"],
                email=account["email"],
                full_name=account["name"],
                role=account["role"],
                is_demo=True,
                department_id=department_id,
            )
            db.add(profile)
            await db.flush()
            print(f"✓ Created {account['name']} profile (dept={'CSE' if department_id else 'None'})")

        # Commit all profiles
        await db.commit()
        print("\n✅ All demo accounts seeded successfully!")
        print("\nDemo Credentials:")
        print("=" * 50)
        for account in DEMO_ACCOUNTS:
            print(
                f"\n{account['name']} ({account['role']}):"
            )
            print(f"  Email:    {account['email']}")
            print(f"  Password: demo1234")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
