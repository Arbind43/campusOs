"""
Seed the demo student profile.

The demo Supabase Auth user must already exist (create it in the Supabase
Dashboard → Authentication → Users → Invite / Add user).

Then run this script to create the matching user_profiles row:

    python -m scripts.seed_demo <supabase-user-uuid>

Example:
    python -m scripts.seed_demo 11111111-2222-3333-4444-555555555555
"""
import asyncio
import sys
import uuid

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import UserProfile


async def seed(user_id: str) -> None:
    uid = uuid.UUID(user_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UserProfile).where(UserProfile.id == uid))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Demo profile already exists for {user_id}")
            return

        profile = UserProfile(
            id=uid,
            email="demo@campusos.app",
            full_name="Demo Student",
            role="student",
            is_demo=True,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        print(f"Created demo profile: id={profile.id}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.seed_demo <supabase-user-uuid>")
        sys.exit(1)
    asyncio.run(seed(sys.argv[1]))
