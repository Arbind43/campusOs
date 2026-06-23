"""
Academic router — timetable, exam schedules, holidays.
Read: all authenticated users.
Write: SUPER_ADMIN, ACADEMIC_ADMIN.
"""
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import StructuredLogger
from app.database import get_db
from app.dependencies import AcademicWrite, CurrentUser
from app.models.academic import Department, ExamSchedule, Holiday, Timetable
from app.schemas.campus import (
    DepartmentOut,
    ExamScheduleCreate,
    ExamScheduleOut,
    HolidayCreate,
    HolidayOut,
    TimetableConfirmRequest,
    TimetableCreate,
    TimetableOut,
    TimetableUploadResponse,
)
from app.services.ocr import parse_timetable_image, parse_time
from app.services.conflicts import scan_conflicts, _overlaps, _fmt
from app.schemas.campus import (
    ClassSlotCheck,
    ConflictScanResult,
    FreeSlotsResult,
    FreeWindow,
    RoomFreeSlots,
    SlotCheckResult,
    SlotConflict,
)
from datetime import time as _time

router = APIRouter(prefix="/academic", tags=["academic"])
DB = Annotated[AsyncSession, Depends(get_db)]
structured_logger = StructuredLogger(__name__)


@router.get("/conflicts", response_model=ConflictScanResult, summary="Scan schedules for conflicts")
async def get_conflicts(_admin: AcademicWrite, db: DB) -> ConflictScanResult:
    """Auto-flag room double-bookings, faculty clashes, and student exam overlaps."""
    return await scan_conflicts(db)


@router.post(
    "/timetable/check",
    response_model=SlotCheckResult,
    summary="Check a proposed class slot for conflicts before scheduling",
)
async def check_slot(body: ClassSlotCheck, _admin: AcademicWrite, db: DB) -> SlotCheckResult:
    """Return room / faculty / cohort clashes for a proposed class slot (no write)."""
    result = await db.execute(
        select(Timetable).where(Timetable.day_of_week == body.day_of_week)
    )
    same_day = list(result.scalars().all())

    conflicts: list[SlotConflict] = []
    for c in same_day:
        if not _overlaps(body.start_time, body.end_time, c.start_time, c.end_time):
            continue
        window = f"{_fmt(c.start_time)}–{_fmt(c.end_time)}"
        # Room clash
        if body.room and c.room and body.room.strip().lower() == c.room.strip().lower():
            conflicts.append(SlotConflict(
                kind="room",
                detail=f"Room {c.room} is already used by {c.subject} ({window}) on {body.day_of_week}.",
            ))
        # Faculty clash
        if (
            body.faculty_name and c.faculty_name
            and body.faculty_name.strip().lower() == c.faculty_name.strip().lower()
        ):
            conflicts.append(SlotConflict(
                kind="faculty",
                detail=f"{c.faculty_name} already teaches {c.subject} ({window}) on {body.day_of_week}.",
            ))
        # Cohort clash (same dept + semester already has a class then)
        if c.department_id == body.department_id and c.semester == body.semester:
            conflicts.append(SlotConflict(
                kind="cohort",
                detail=f"This batch already has {c.subject} ({window}) on {body.day_of_week}.",
            ))

    return SlotCheckResult(has_conflict=len(conflicts) > 0, conflicts=conflicts)


WORKING_START = _time(8, 0)
WORKING_END = _time(18, 0)


@router.get(
    "/free-slots",
    response_model=FreeSlotsResult,
    summary="List free time windows per room for a given day",
)
async def free_slots(_admin: AcademicWrite, db: DB, day_of_week: str) -> FreeSlotsResult:
    """For each known room, return the unoccupied time windows on the given day."""
    result = await db.execute(select(Timetable))
    all_entries = list(result.scalars().all())

    # Room inventory = every distinct room that appears anywhere in the timetable.
    rooms = sorted({e.room.strip() for e in all_entries if e.room and e.room.strip()})

    day_entries = [e for e in all_entries if e.day_of_week == day_of_week]

    rooms_out: list[RoomFreeSlots] = []
    for room in rooms:
        # Occupied intervals for this room on this day, clipped to working hours.
        occ = []
        for e in day_entries:
            if e.room and e.room.strip().lower() == room.lower():
                s = max(e.start_time, WORKING_START)
                en = min(e.end_time, WORKING_END)
                if s < en:
                    occ.append((s, en))
        occ.sort()

        # Compute gaps between occupied intervals within working hours.
        windows: list[FreeWindow] = []
        cursor = WORKING_START
        for s, en in occ:
            if s > cursor:
                windows.append(FreeWindow(start=cursor, end=s))
            if en > cursor:
                cursor = en
        if cursor < WORKING_END:
            windows.append(FreeWindow(start=cursor, end=WORKING_END))

        rooms_out.append(RoomFreeSlots(room=room, free_windows=windows))

    return FreeSlotsResult(
        day_of_week=day_of_week,
        working_start=WORKING_START,
        working_end=WORKING_END,
        rooms=rooms_out,
    )


# ── Debug endpoint ────────────────────────────────────────────────────────── #

@router.get("/debug/me")
async def debug_me(user: CurrentUser):
    """Debug endpoint to check auth status."""
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "department_id": str(user.department_id) if user.department_id else None,
    }


# ── Departments (public read) ─────────────────────────────────────────────── #

@router.get("/departments", response_model=list[DepartmentOut])
async def list_departments(_user: CurrentUser, db: DB) -> list[DepartmentOut]:
    result = await db.execute(select(Department).order_by(Department.code))
    return [DepartmentOut.model_validate(d) for d in result.scalars().all()]


# ── Timetable ─────────────────────────────────────────────────────────────── #

@router.get("/timetable", response_model=list[TimetableOut])
async def get_timetable(
    current_user: CurrentUser,
    db: DB,
    department_id: uuid.UUID | None = None,
    semester: int | None = None,
) -> list[TimetableOut]:
    query = select(Timetable)
    dept_id = department_id or current_user.department_id
    if dept_id:
        query = query.where(Timetable.department_id == dept_id)
    if semester:
        query = query.where(Timetable.semester == semester)
    query = query.order_by(Timetable.day_of_week, Timetable.start_time)
    result = await db.execute(query)
    return [TimetableOut.model_validate(t) for t in result.scalars().all()]


@router.post("/timetable", response_model=TimetableOut, status_code=status.HTTP_201_CREATED)
async def create_timetable_entry(
    body: TimetableCreate,
    _admin: AcademicWrite,
    db: DB,
) -> TimetableOut:
    entry = Timetable(**body.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return TimetableOut.model_validate(entry)


@router.delete("/timetable/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable_entry(
    entry_id: int,
    _admin: AcademicWrite,
    db: DB,
) -> None:
    result = await db.execute(select(Timetable).where(Timetable.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    await db.delete(entry)
    await db.commit()


@router.post("/timetable/upload", response_model=TimetableUploadResponse)
async def upload_timetable_image(
    admin: AcademicWrite,
    db: DB,
    file: UploadFile = File(...),
) -> TimetableUploadResponse:
    """
    Upload a timetable image (JPEG/PNG) for OCR parsing.
    Uses Groq Vision API to extract schedule information.
    Returns parsed entries for frontend review WITHOUT database write.
    
    **Only Academic Admins can upload timetables.**
    """
    # Log file upload metadata
    structured_logger.info(
        "Timetable image upload received",
        user_id=str(admin.id),
        department_id=str(admin.department_id) if admin.department_id else None,
        content_type=file.content_type,
        filename=file.filename,
    )
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        structured_logger.warning(
            "File upload rejected - unsupported format",
            user_id=str(admin.id),
            content_type=file.content_type,
            filename=file.filename,
        )
        return TimetableUploadResponse(
            success=False,
            message="Unsupported file format. Only JPEG and PNG images are allowed.",
            errors=["Unsupported file format. Only JPEG and PNG images are allowed."],
        )

    # Validate file size (10 MB limit)
    file_content = await file.read()
    file_size = len(file_content)
    
    structured_logger.info(
        "File content read",
        user_id=str(admin.id),
        file_size_bytes=file_size,
        file_size_mb=round(file_size / (1024 * 1024), 2),
    )
    
    if file_size > 10 * 1024 * 1024:
        structured_logger.warning(
            "File upload rejected - exceeds size limit",
            user_id=str(admin.id),
            file_size_bytes=file_size,
            file_size_mb=round(file_size / (1024 * 1024), 2),
            max_size_mb=10,
        )
        return TimetableUploadResponse(
            success=False,
            message="File size exceeds the maximum limit of 10 MB",
            errors=["File size exceeds the maximum limit of 10 MB"],
        )

    # Check if file is empty
    if file_size == 0:
        structured_logger.warning(
            "File upload rejected - empty file",
            user_id=str(admin.id),
            filename=file.filename,
        )
        return TimetableUploadResponse(
            success=False,
            message="Uploaded file is empty",
            errors=["Uploaded file is empty"],
        )

    # Ensure admin has department assigned
    if not admin.department_id:
        structured_logger.error(
            "File upload rejected - no department assignment",
            user_id=str(admin.id),
        )
        return TimetableUploadResponse(
            success=False,
            message="Department assignment is required for timetable upload",
            errors=["Department assignment is required for timetable upload"],
        )

    try:
        # Parse timetable from image using OCR
        ocr_result = await parse_timetable_image(file_content)

        if not ocr_result["success"]:
            structured_logger.error(
                "OCR parsing failed",
                user_id=str(admin.id),
                department_id=str(admin.department_id),
                extracted_text=ocr_result.get("extracted_text", "")[:200],  # First 200 chars
                errors=ocr_result.get("errors", []),
            )
            return TimetableUploadResponse(
                success=False,
                message="Failed to parse timetable image.",
                extracted_text=ocr_result.get("extracted_text", ""),
                errors=ocr_result.get("errors", ["OCR parsing failed"]),
            )

        entries = ocr_result.get("entries", [])
        if not entries:
            structured_logger.warning(
                "OCR completed but no entries extracted",
                user_id=str(admin.id),
                department_id=str(admin.department_id),
                extracted_text_length=len(ocr_result.get("extracted_text", "")),
            )
            return TimetableUploadResponse(
                success=True,
                message="Image processed but no timetable entries were extracted. Please try a clearer image.",
                extracted_text=ocr_result.get("extracted_text", ""),
                errors=["No entries extracted from image"],
            )

        # Validate and convert parsed entries to TimetableOut format
        # WITHOUT database write - just return for frontend review
        parsed_entries = []
        skipped_count = 0
        
        for entry_data in entries:
            try:
                # Validate required fields
                if not all(k in entry_data for k in ["day_of_week", "start_time", "end_time", "subject"]):
                    skipped_count += 1
                    continue

                # Parse time values
                start_time = parse_time(entry_data["start_time"])
                end_time = parse_time(entry_data["end_time"])

                # Get semester value (default to 1 if not provided)
                # Safely coerce to int — the vision model may return it as a string
                try:
                    semester = int(entry_data.get("semester", 1))
                except (TypeError, ValueError):
                    semester = 1
                
                # Validate semester is between 1 and 8 inclusive
                if semester < 1 or semester > 8:
                    semester = 1  # Clamp to valid range

                # Create entry object for response (without database ID or created_at)
                # Using a mock TimetableOut structure
                parsed_entry = TimetableOut(
                    id=0,  # Temporary ID since not saved yet
                    department_id=admin.department_id,
                    semester=semester,
                    day_of_week=entry_data["day_of_week"],
                    start_time=start_time,
                    end_time=end_time,
                    subject=entry_data["subject"],
                    room=entry_data.get("room"),
                    faculty_name=entry_data.get("faculty_name"),
                    created_at=datetime.now(),  # Temporary timestamp
                )
                parsed_entries.append(parsed_entry)
            except (ValueError, KeyError) as e:
                skipped_count += 1
                structured_logger.warning(
                    "Entry parsing failed - skipping entry",
                    user_id=str(admin.id),
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                    entry_data=entry_data,
                )
                continue

        structured_logger.info(
            "Timetable upload parsing completed",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
            entries_parsed=len(parsed_entries),
            entries_skipped=skipped_count,
            extracted_text_length=len(ocr_result.get("extracted_text", "")),
        )

        return TimetableUploadResponse(
            success=True,
            message=f"Successfully parsed {len(parsed_entries)} timetable entries. Review and confirm to save.",
            extracted_text=ocr_result.get("extracted_text", ""),
            entries_created=0,  # No entries created yet - awaiting confirmation
            entries=parsed_entries,
            errors=ocr_result.get("errors", []),
        )

    except Exception as e:
        structured_logger.error(
            "Timetable upload processing error",
            user_id=str(admin.id),
            department_id=str(admin.department_id) if admin.department_id else None,
            exception_type=type(e).__name__,
            exception_message=str(e),
        )
        return TimetableUploadResponse(
            success=False,
            message=f"Error processing timetable upload: {str(e)}",
            errors=[str(e)],
        )


@router.post("/timetable/confirm", response_model=TimetableUploadResponse)
async def confirm_timetable(
    body: TimetableConfirmRequest,
    admin: AcademicWrite,
    db: DB,
) -> TimetableUploadResponse:
    """
    Confirm and save reviewed timetable entries with atomic replacement.
    Deletes all existing timetable entries for the admin's department and inserts new ones.
    
    **Only Academic Admins can confirm timetables.**
    """
    structured_logger.info(
        "Timetable confirmation started",
        user_id=str(admin.id),
        department_id=str(admin.department_id) if admin.department_id else None,
        entries_to_save=len(body.entries),
    )
    
    # Validate user has department_id assigned
    if not admin.department_id:
        structured_logger.error(
            "Timetable confirmation rejected - no department assignment",
            user_id=str(admin.id),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user must be assigned to a department before saving timetables.",
        )

    # Validate entries array is not empty (schema validator handles this, but double-check)
    if not body.entries:
        structured_logger.warning(
            "Timetable confirmation rejected - no entries provided",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one timetable entry is required",
        )

    try:
        # Begin atomic transaction with timeout
        structured_logger.info(
            "Database transaction started",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
            transaction_type="atomic_timetable_replacement",
        )
        
        # Step 1: Delete existing timetable entries for this department
        structured_logger.info(
            "Deleting existing timetable entries",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
        )
        
        delete_stmt = delete(Timetable).where(
            Timetable.department_id == admin.department_id
        )
        delete_result = await db.execute(delete_stmt)
        deleted_count = delete_result.rowcount
        
        structured_logger.info(
            "Existing timetable entries deleted",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
            deleted_count=deleted_count,
        )

        # Step 2: Validate and insert new timetable entries
        new_entries = []
        skipped_count = 0
        
        # Valid days for validation (Requirement 4.1)
        VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        
        for entry_data in body.entries:
            try:
                # Requirement 4.1: Validate day_of_week is one of the valid days
                day_of_week = entry_data.get("day_of_week")
                if not day_of_week or day_of_week not in VALID_DAYS:
                    skipped_count += 1
                    continue
                
                # Requirement 4.4: Validate subject is non-empty string
                subject = entry_data.get("subject", "").strip() if isinstance(entry_data.get("subject"), str) else ""
                if not subject:
                    skipped_count += 1
                    continue
                
                # Requirement 4.5: Validate subject max 100 chars
                if len(subject) > 100:
                    skipped_count += 1
                    continue
                
                # Requirements 4.2, 4.3: Validate start_time and end_time are non-null and parseable
                start_time_str = entry_data.get("start_time")
                end_time_str = entry_data.get("end_time")
                
                if not start_time_str or not end_time_str:
                    skipped_count += 1
                    continue
                
                # Requirement 4.7: Parse time strings in HH:MM format to Python time objects
                start_time = parse_time(start_time_str)
                end_time = parse_time(end_time_str)

                # Requirement 4.6: Validate start_time < end_time
                if start_time >= end_time:
                    skipped_count += 1
                    continue

                # Get semester value (default to 1 if not provided)
                # Safely coerce to int — the vision model may return it as a string
                try:
                    semester = int(entry_data.get("semester", 1))
                except (TypeError, ValueError):
                    semester = 1
                
                # Validate semester is between 1 and 8 inclusive
                if semester < 1 or semester > 8:
                    skipped_count += 1
                    continue

                # Create new timetable entry
                timetable_entry = Timetable(
                    department_id=admin.department_id,
                    semester=semester,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    subject=subject,
                    room=entry_data.get("room"),
                    faculty_name=entry_data.get("faculty_name"),
                )
                db.add(timetable_entry)
                new_entries.append(timetable_entry)

            except (ValueError, KeyError, TypeError) as e:
                # Requirement 4.8: Skip invalid entries
                # Requirement 4.9: Increment skipped entry count
                skipped_count += 1
                structured_logger.warning(
                    "Entry validation failed - skipping entry",
                    user_id=str(admin.id),
                    department_id=str(admin.department_id),
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                )
                continue

        # Flush to get IDs but don't commit yet
        structured_logger.info(
            "Inserting new timetable entries",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
            entries_to_insert=len(new_entries),
            entries_skipped=skipped_count,
        )
        
        await db.flush()

        # Commit the transaction
        structured_logger.info(
            "Committing database transaction",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
            transaction_type="atomic_timetable_replacement",
        )
        
        await db.commit()
        
        structured_logger.info(
            "Database transaction committed successfully",
            user_id=str(admin.id),
            department_id=str(admin.department_id),
            entries_created=len(new_entries),
            entries_skipped=skipped_count,
            deleted_count=deleted_count,
        )

        # Refresh entries to get all fields including created_at
        for entry in new_entries:
            await db.refresh(entry)

        # Convert to response format
        response_entries = [TimetableOut.model_validate(entry) for entry in new_entries]

        # Build success message with skipped entry count if applicable
        message = f"Successfully saved {len(new_entries)} timetable entries."
        if skipped_count > 0:
            message += f" {skipped_count} entries were skipped due to validation failures."

        return TimetableUploadResponse(
            success=True,
            message=message,
            entries_created=len(new_entries),
            entries=response_entries,
            errors=[],
        )

    except Exception as e:
        # Rollback happens automatically
        structured_logger.error(
            "Database transaction failed - rolling back",
            user_id=str(admin.id),
            department_id=str(admin.department_id) if admin.department_id else None,
            exception_type=type(e).__name__,
            exception_message=str(e),
            transaction_type="atomic_timetable_replacement",
        )
        
        await db.rollback()
        
        structured_logger.info(
            "Database transaction rolled back",
            user_id=str(admin.id),
            department_id=str(admin.department_id) if admin.department_id else None,
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction failed. No changes were saved.",
        )


# ── Exam Schedule ─────────────────────────────────────────────────────────── #

@router.get("/exams", response_model=list[ExamScheduleOut])
async def get_exam_schedule(
    current_user: CurrentUser,
    db: DB,
    department_id: uuid.UUID | None = None,
    semester: int | None = None,
) -> list[ExamScheduleOut]:
    query = select(ExamSchedule)
    dept_id = department_id or current_user.department_id
    if dept_id:
        query = query.where(ExamSchedule.department_id == dept_id)
    if semester:
        query = query.where(ExamSchedule.semester == semester)
    query = query.order_by(ExamSchedule.exam_date, ExamSchedule.start_time)
    result = await db.execute(query)
    return [ExamScheduleOut.model_validate(e) for e in result.scalars().all()]


@router.post("/exams", response_model=ExamScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_exam(
    body: ExamScheduleCreate,
    _admin: AcademicWrite,
    db: DB,
) -> ExamScheduleOut:
    exam = ExamSchedule(**body.model_dump())
    db.add(exam)
    await db.commit()
    await db.refresh(exam)
    return ExamScheduleOut.model_validate(exam)


# ── Holidays ──────────────────────────────────────────────────────────────── #

@router.get("/holidays", response_model=list[HolidayOut])
async def get_holidays(_user: CurrentUser, db: DB) -> list[HolidayOut]:
    result = await db.execute(select(Holiday).order_by(Holiday.holiday_date))
    return [HolidayOut.model_validate(h) for h in result.scalars().all()]


@router.post("/holidays", response_model=HolidayOut, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    body: HolidayCreate,
    _admin: AcademicWrite,
    db: DB,
) -> HolidayOut:
    holiday = Holiday(**body.model_dump())
    db.add(holiday)
    await db.commit()
    await db.refresh(holiday)
    return HolidayOut.model_validate(holiday)
