"""
Admin router — SUPER_ADMIN only.

Provides user management and role assignment endpoints.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import AcademicWrite, SuperAdmin, get_user_role_names
from app.models.academic import Department
from app.models.club import Club
from app.models.hostel import Hostel
from app.models.rbac import Role, RoleName, UserRole
from app.models.user import UserProfile
from app.schemas.campus import (
    AssignRoleRequest,
    ClubCreate,
    ClubOut,
    DepartmentCreate,
    DepartmentOut,
    HostelCreate,
    HostelOut,
    RoleOut,
    UserProfileOut,
    UserProfileUpdate,
    UserRoleOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])

DB = Annotated[AsyncSession, Depends(get_db)]


# ── User Management (Academic Admins) ────────────────────────────────────── #

@router.get(
    "/manage/users",
    response_model=list[UserProfileOut],
    summary="List users for management (academic admins)",
)
async def manage_list_users(
    _admin: AcademicWrite,
    db: DB,
    role: str | None = None,
    department_id: uuid.UUID | None = None,
) -> list[UserProfileOut]:
    """List users (optionally filtered by role/department) so admins can assign
    department and year of study."""
    query = select(UserProfile).order_by(UserProfile.full_name)
    if role:
        query = query.where(UserProfile.role == role)
    if department_id:
        query = query.where(UserProfile.department_id == department_id)
    result = await db.execute(query)
    return [UserProfileOut.model_validate(u) for u in result.scalars().all()]


@router.patch(
    "/manage/users/{user_id}",
    response_model=UserProfileOut,
    summary="Update a user's department / year / role (academic admins)",
)
async def manage_update_user(
    user_id: uuid.UUID,
    body: UserProfileUpdate,
    _admin: AcademicWrite,
    db: DB,
) -> UserProfileOut:
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = body.model_dump(exclude_unset=True)
    if "department_id" in data:
        user.department_id = data["department_id"]
    if "year_of_study" in data:
        user.year_of_study = data["year_of_study"]
    if "role" in data and data["role"]:
        user.role = data["role"]

    await db.commit()
    await db.refresh(user)
    return UserProfileOut.model_validate(user)


@router.post(
    "/manage/departments",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department (academic admins)",
)
async def manage_create_department(
    body: DepartmentCreate,
    _admin: AcademicWrite,
    db: DB,
) -> DepartmentOut:
    dept = Department(name=body.name, code=body.code.upper())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return DepartmentOut.model_validate(dept)


# ── User Management (Super Admin) ────────────────────────────────────────── #

@router.get("/users", response_model=list[UserProfileOut], summary="List all users")
async def list_users(
    _admin: SuperAdmin,
    db: DB,
) -> list[UserProfileOut]:
    result = await db.execute(
        select(UserProfile)
        .options(selectinload(UserProfile.user_roles).selectinload(UserRole.role))
        .order_by(UserProfile.created_at.desc())
    )
    users = result.scalars().all()
    out = []
    for u in users:
        profile = UserProfileOut.model_validate(u)
        profile.roles = [ur.role.name for ur in u.user_roles if ur.role]
        if not profile.roles:
            profile.roles = [u.role]
        out.append(profile)
    return out


@router.post(
    "/users/{user_id}/roles",
    response_model=UserRoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a role to a user",
)
async def assign_role(
    user_id: uuid.UUID,
    body: AssignRoleRequest,
    admin: SuperAdmin,
    db: DB,
) -> UserRoleOut:
    # Validate role exists
    role_result = await db.execute(select(Role).where(Role.name == body.role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{body.role_name}' not found")

    # Validate user exists
    user_result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create user role assignment
    user_role = UserRole(
        user_id=user_id,
        role_id=role.id,
        scope_id=body.scope_id,
        granted_by=admin.id,
    )
    db.add(user_role)

    # Also update the legacy role field if it's a primary role
    if body.role_name != RoleName.STUDENT:
        user.role = body.role_name

    await db.commit()
    await db.refresh(user_role)
    await db.refresh(user_role, ["role"])

    return UserRoleOut(
        id=user_role.id,
        user_id=user_role.user_id,
        role_id=user_role.role_id,
        role_name=role.name,
        scope_id=user_role.scope_id,
        granted_at=user_role.granted_at,
    )


@router.delete(
    "/users/{user_id}/roles/{role_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a role from a user",
)
async def revoke_role(
    user_id: uuid.UUID,
    role_name: str,
    _admin: SuperAdmin,
    db: DB,
) -> None:
    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")

    ur_result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
        )
    )
    user_role = ur_result.scalar_one_or_none()
    if not user_role:
        raise HTTPException(status_code=404, detail="Role assignment not found")

    await db.delete(user_role)
    await db.commit()


# ── Department Management ─────────────────────────────────────────────────── #

@router.get("/departments", response_model=list[DepartmentOut], summary="List departments")
async def list_departments(
    _admin: SuperAdmin,
    db: DB,
) -> list[DepartmentOut]:
    result = await db.execute(select(Department).order_by(Department.code))
    return [DepartmentOut.model_validate(d) for d in result.scalars().all()]


@router.post(
    "/departments",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department",
)
async def create_department(
    body: DepartmentCreate,
    _admin: SuperAdmin,
    db: DB,
) -> DepartmentOut:
    dept = Department(name=body.name, code=body.code.upper())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return DepartmentOut.model_validate(dept)


# ── Hostel Management ─────────────────────────────────────────────────────── #

@router.post(
    "/hostels",
    response_model=HostelOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new hostel",
)
async def create_hostel(
    body: HostelCreate,
    _admin: SuperAdmin,
    db: DB,
) -> HostelOut:
    hostel = Hostel(name=body.name)
    db.add(hostel)
    await db.commit()
    await db.refresh(hostel)
    return HostelOut.model_validate(hostel)


# ── Club Management ───────────────────────────────────────────────────────── #

@router.post(
    "/clubs",
    response_model=ClubOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new club",
)
async def create_club(
    body: ClubCreate,
    _admin: SuperAdmin,
    db: DB,
) -> ClubOut:
    club = Club(name=body.name, club_type=body.club_type, description=body.description)
    db.add(club)
    await db.commit()
    await db.refresh(club)
    return ClubOut.model_validate(club)


# ── Roles Reference ───────────────────────────────────────────────────────── #

@router.get("/roles", response_model=list[RoleOut], summary="List all system roles")
async def list_roles(
    _admin: SuperAdmin,
    db: DB,
) -> list[RoleOut]:
    result = await db.execute(select(Role).order_by(Role.id))
    return [RoleOut.model_validate(r) for r in result.scalars().all()]
