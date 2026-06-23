"""
Assignments router — faculty uploads, students view (dept-scoped).
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, FacultyWrite
from app.models.content import Assignment
from app.schemas.campus import AssignmentCreate, AssignmentOut

router = APIRouter(prefix="/assignments", tags=["assignments"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[AssignmentOut])
async def list_assignments(
    current_user: CurrentUser,
    db: DB,
    department_id: uuid.UUID | None = None,
    semester: int | None = None,
) -> list[AssignmentOut]:
    query = select(Assignment)
    # Default to user's own department
    dept_id = department_id or current_user.department_id
    if dept_id:
        query = query.where(Assignment.department_id == dept_id)
    if semester:
        query = query.where(Assignment.semester == semester)
    # Also filter by student's year_of_study → semester (rough mapping)
    if current_user.year_of_study and not semester:
        sem = current_user.year_of_study * 2  # rough: year 2 → sem 3/4
        query = query.where(
            (Assignment.semester == sem) |
            (Assignment.semester == sem - 1) |
            (Assignment.semester.is_(None))
        )
    query = query.order_by(Assignment.due_date.asc())
    result = await db.execute(query)
    return [AssignmentOut.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    body: AssignmentCreate,
    faculty: FacultyWrite,
    db: DB,
) -> AssignmentOut:
    assignment = Assignment(**body.model_dump(), faculty_id=faculty.id)
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return AssignmentOut.model_validate(assignment)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: uuid.UUID,
    faculty: FacultyWrite,
    db: DB,
) -> None:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.faculty_id != faculty.id and faculty.role not in ("SUPER_ADMIN", "ACADEMIC_ADMIN"):
        raise HTTPException(status_code=403, detail="Can only delete your own assignments")
    await db.delete(assignment)
    await db.commit()
