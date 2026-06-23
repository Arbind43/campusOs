"""
Create a simple admin user in the database.
Run with: python -m scripts.create_admin_simple
"""
import asyncio
import uuid

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.academic import Department
from app.models.user import UserProfile


async def main():
    async with AsyncSessionLocal() as db:
        # Create CSE department if it doesn't exist
        result = await db.execute(select(Department).where(Department.code == "CSE"))
        dept = result.scalar_one_or_none()
        
        if dept is None:
            dept = Department(
                name="Computer Science & Engineering",
                code="CSE",
            )
            db.add(dept)
            await db.flush()
            print(f"✅ Created department: {dept.name}")
        else:
            print(f"✅ Department already exists: {dept.name}")
        
        # Create admin user
        admin_email = "admin@college.edu"
        result = await db.execute(select(UserProfile).where(UserProfile.email == admin_email))
        admin = result.scalar_one_or_none()
        
        if admin is None:
            admin = UserProfile(
                id=uuid.uuid4(),
                email=admin_email,
                full_name="Admin User",
                role="ACADEMIC_ADMIN",
                is_demo=False,
                department_id=dept.id,
            )
            db.add(admin)
            await db.commit()
            print(f"✅ Created admin user: {admin_email}")
            print(f"   User ID: {admin.id}")
            print(f"   Role: {admin.role}")
            print(f"   Department: {dept.code}")
        else:
            print(f"✅ Admin user already exists: {admin_email}")
            print(f"   User ID: {admin.id}")
            print(f"   Role: {admin.role}")
        
        # Create a student user
        student_email = "student@college.edu"
        result = await db.execute(select(UserProfile).where(UserProfile.email == student_email))
        student = result.scalar_one_or_none()
        
        if student is None:
            student = UserProfile(
                id=uuid.uuid4(),
                email=student_email,
                full_name="Student User",
                role="STUDENT",
                is_demo=False,
                department_id=dept.id,
                year_of_study=2,
            )
            db.add(student)
            await db.commit()
            print(f"✅ Created student user: {student_email}")
            print(f"   User ID: {student.id}")
            print(f"   Role: {student.role}")
        else:
            print(f"✅ Student user already exists: {student_email}")
        
        print("\n" + "="*60)
        print("SIMPLE LOGIN CREDENTIALS (password doesn't matter in dev):")
        print("="*60)
        print(f"Admin:   {admin_email} / any-password")
        print(f"Student: {student_email} / any-password")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
