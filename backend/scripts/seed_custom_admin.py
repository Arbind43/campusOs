"""
Create a custom academic admin account and seed starter academic data.

Run from backend:
    python -m scripts.seed_custom_admin
"""
import asyncio
import uuid
from datetime import time

import httpx
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.academic import Department, Timetable
from app.models.rbac import Role, RoleName, UserRole
from app.models.user import UserProfile


ADMIN_EMAIL = "admin@campusos.app"
ADMIN_PASSWORD = "Uday@123"
ADMIN_NAME = "admin"


async def ensure_supabase_auth_user() -> uuid.UUID:
    service_key = settings.SUPABASE_JWT_SECRET
    base_url = settings.SUPABASE_URL.rstrip("/")
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{base_url}/auth/v1/admin/users",
            headers=headers,
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": ADMIN_NAME,
                    "app_role": "admin",
                },
            },
        )

        if response.status_code in {200, 201}:
            return uuid.UUID(response.json()["id"])

        if response.status_code not in {400, 422}:
            raise RuntimeError(
                f"Supabase admin user creation failed: {response.status_code} {response.text}"
            )

        users_response = await client.get(
            f"{base_url}/auth/v1/admin/users",
            headers=headers,
            params={"page": 1, "per_page": 1000},
        )
        users_response.raise_for_status()

        users = users_response.json().get("users", [])
        for user in users:
            if user.get("email") == ADMIN_EMAIL:
                return uuid.UUID(user["id"])

    raise RuntimeError(f"Could not create or find Supabase auth user {ADMIN_EMAIL}")


async def ensure_role(db, role_name: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=role_name, description=role_name.replace("_", " ").title())
        db.add(role)
        await db.flush()
    return role


async def ensure_department(db) -> Department:
    result = await db.execute(select(Department).where(Department.code == "CSE"))
    department = result.scalar_one_or_none()
    if department is None:
        department = Department(name="Computer Science & Engineering", code="CSE")
        db.add(department)
        await db.flush()
    return department


async def seed_database(auth_user_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        department = await ensure_department(db)

        for role_name in RoleName.ALL:
            await ensure_role(db, role_name)

        admin_role = await ensure_role(db, RoleName.ACADEMIC_ADMIN)

        result = await db.execute(select(UserProfile).where(UserProfile.id == auth_user_id))
        profile = result.scalar_one_or_none()

        if profile is None:
            profile = UserProfile(
                id=auth_user_id,
                email=ADMIN_EMAIL,
                full_name=ADMIN_NAME,
                role=RoleName.ACADEMIC_ADMIN,
                is_demo=False,
                department_id=department.id,
            )
            db.add(profile)
            await db.flush()
        else:
            profile.email = ADMIN_EMAIL
            profile.full_name = ADMIN_NAME
            profile.role = RoleName.ACADEMIC_ADMIN
            profile.department_id = department.id

        role_result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == auth_user_id,
                UserRole.role_id == admin_role.id,
                UserRole.scope_id.is_(None),
            )
        )
        if role_result.scalar_one_or_none() is None:
            db.add(UserRole(user_id=auth_user_id, role_id=admin_role.id))

        timetable_result = await db.execute(
            select(Timetable).where(Timetable.department_id == department.id)
        )
        if timetable_result.first() is None:
            db.add_all(
                [
                    Timetable(
                        department_id=department.id,
                        semester=1,
                        day_of_week="Monday",
                        start_time=time(9, 0),
                        end_time=time(10, 0),
                        subject="Data Structures",
                        room="CSE-101",
                        faculty_name="Prof. Rao",
                    ),
                    Timetable(
                        department_id=department.id,
                        semester=1,
                        day_of_week="Tuesday",
                        start_time=time(10, 0),
                        end_time=time(11, 0),
                        subject="Database Systems",
                        room="CSE-102",
                        faculty_name="Prof. Mehta",
                    ),
                    Timetable(
                        department_id=department.id,
                        semester=1,
                        day_of_week="Wednesday",
                        start_time=time(11, 0),
                        end_time=time(12, 0),
                        subject="Operating Systems",
                        room="Lab-1",
                        faculty_name="Prof. Iyer",
                    ),
                ]
            )

        await db.commit()


async def main() -> None:
    auth_user_id = await ensure_supabase_auth_user()
    await seed_database(auth_user_id)
    print("Custom admin seeded successfully.")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
