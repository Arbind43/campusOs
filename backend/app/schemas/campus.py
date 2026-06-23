"""
Pydantic schemas for all RBAC domain models.
"""
import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth / User ──────────────────────────────────────────────────────────── #

class SyncProfileRequest(BaseModel):
    """
    Sent by the frontend after Supabase sign-up.
    Stores the selected role in the application profile.
    """
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: Literal["student", "professor", "admin"] = "student"
    department_id: uuid.UUID | None = None
    year_of_study: int | None = Field(default=None, ge=1, le=8)


class UserProfileOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_demo: bool
    department_id: uuid.UUID | None = None
    year_of_study: int | None = None
    hostel_room_id: uuid.UUID | None = None
    roles: list[str] = []

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Admin edit of a user's academic placement / role."""
    department_id: uuid.UUID | None = None
    year_of_study: int | None = Field(default=None, ge=1, le=8)
    role: str | None = None


# ── Role assignment ───────────────────────────────────────────────────────── #

class AssignRoleRequest(BaseModel):
    role_name: str
    scope_id: uuid.UUID | None = None


class RoleOut(BaseModel):
    id: int
    name: str
    description: str

    model_config = {"from_attributes": True}


class UserRoleOut(BaseModel):
    id: int
    user_id: uuid.UUID
    role_id: int
    role_name: str
    scope_id: uuid.UUID | None = None
    granted_at: datetime

    model_config = {"from_attributes": True}


# ── Department ───────────────────────────────────────────────────────────── #

class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=20)


class DepartmentOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Timetable ─────────────────────────────────────────────────────────────── #

class TimetableCreate(BaseModel):
    department_id: uuid.UUID
    semester: int = Field(ge=1, le=8)
    day_of_week: Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    start_time: time
    end_time: time
    subject: str = Field(min_length=1, max_length=100)
    room: str | None = Field(default=None, max_length=50)
    faculty_name: str | None = Field(default=None, max_length=100)

    @field_validator('end_time')
    @classmethod
    def validate_time_order(cls, v, info):
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class TimetableOut(BaseModel):
    id: int
    department_id: uuid.UUID
    semester: int
    day_of_week: str
    start_time: time
    end_time: time
    subject: str
    room: str | None = None
    faculty_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TimetableUploadResponse(BaseModel):
    """Response from timetable OCR upload endpoint"""
    success: bool
    message: str
    extracted_text: str = ""
    entries_created: int = 0
    entries: list[TimetableOut] = []
    errors: list[str] = []


class TimetableConfirmRequest(BaseModel):
    """Request body for confirming and saving timetable entries"""
    entries: list[dict] = Field(min_length=1)

    @field_validator('entries')
    @classmethod
    def validate_entries(cls, v):
        """Validate each entry has required fields"""
        if not v:
            raise ValueError("At least one timetable entry is required")
        
        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        
        for idx, entry in enumerate(v):
            # Validate required fields
            if 'day_of_week' not in entry:
                raise ValueError(f"Entry {idx}: day_of_week is required")
            if 'start_time' not in entry:
                raise ValueError(f"Entry {idx}: start_time is required")
            if 'end_time' not in entry:
                raise ValueError(f"Entry {idx}: end_time is required")
            if 'subject' not in entry:
                raise ValueError(f"Entry {idx}: subject is required")
            
            # Validate day_of_week
            if entry['day_of_week'] not in valid_days:
                raise ValueError(f"Entry {idx}: day_of_week must be one of {valid_days}")
            
            # Validate subject length
            if not entry['subject'] or len(entry['subject']) > 100:
                raise ValueError(f"Entry {idx}: subject must be between 1 and 100 characters")
            
            # Validate optional field lengths
            if 'room' in entry and entry['room'] and len(entry['room']) > 50:
                raise ValueError(f"Entry {idx}: room must not exceed 50 characters")
            
            if 'faculty_name' in entry and entry['faculty_name'] and len(entry['faculty_name']) > 100:
                raise ValueError(f"Entry {idx}: faculty_name must not exceed 100 characters")
            
            # Validate semester if provided
            if 'semester' in entry:
                semester = entry['semester']
                if not isinstance(semester, int) or semester < 1 or semester > 8:
                    raise ValueError(f"Entry {idx}: semester must be between 1 and 8")
        
        return v


# ── Exam Schedule ─────────────────────────────────────────────────────────── #

class ExamScheduleCreate(BaseModel):
    department_id: uuid.UUID
    semester: int = Field(ge=1, le=8)
    subject: str = Field(min_length=1, max_length=100)
    exam_date: date
    start_time: time
    room: str | None = None


class ExamScheduleOut(BaseModel):
    id: int
    department_id: uuid.UUID
    semester: int
    subject: str
    exam_date: date
    start_time: time
    room: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Holiday ───────────────────────────────────────────────────────────────── #

class HolidayCreate(BaseModel):
    holiday_date: date
    description: str = Field(min_length=1, max_length=255)


class HolidayOut(BaseModel):
    id: int
    holiday_date: date
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Hostel ────────────────────────────────────────────────────────────────── #

class HostelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class HostelOut(BaseModel):
    id: uuid.UUID
    name: str
    warden_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HostelRoomCreate(BaseModel):
    hostel_id: uuid.UUID
    room_number: str = Field(min_length=1, max_length=20)
    capacity: int = Field(default=2, ge=1, le=10)


class HostelRoomOut(BaseModel):
    id: uuid.UUID
    hostel_id: uuid.UUID
    room_number: str
    capacity: int

    model_config = {"from_attributes": True}


# ── Mess Menu ─────────────────────────────────────────────────────────────── #

class MessMenuCreate(BaseModel):
    hostel_id: uuid.UUID
    week_start: date
    day_of_week: str
    meal_type: Literal["breakfast", "lunch", "snacks", "dinner"]
    items: str = Field(min_length=1)
    is_special: bool = False


class MessMenuOut(BaseModel):
    id: int
    hostel_id: uuid.UUID
    week_start: date
    day_of_week: str
    meal_type: str
    items: str
    is_special: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MessNoticeCreate(BaseModel):
    hostel_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class MessNoticeOut(BaseModel):
    id: int
    hostel_id: uuid.UUID
    title: str
    body: str
    created_by: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Placement ─────────────────────────────────────────────────────────────── #

class PlacementDriveCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=150)
    job_role: str = Field(min_length=1, max_length=150)
    package_lpa: float | None = Field(default=None, ge=0)
    drive_date: date | None = None
    registration_deadline: date | None = None
    description: str = ""


class PlacementDriveOut(BaseModel):
    id: uuid.UUID
    company_name: str
    job_role: str
    package_lpa: float | None = None
    drive_date: date | None = None
    registration_deadline: date | None = None
    description: str
    is_active: bool
    created_by: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlacementNoticeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    drive_id: uuid.UUID | None = None


class PlacementNoticeOut(BaseModel):
    id: int
    title: str
    body: str
    drive_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Clubs ─────────────────────────────────────────────────────────────────── #

class ClubCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    club_type: Literal["technical", "cultural", "sports", "other"] = "technical"
    description: str = ""


class ClubOut(BaseModel):
    id: uuid.UUID
    name: str
    club_type: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Notices ───────────────────────────────────────────────────────────────── #

class NoticeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    domain: Literal["academic", "hostel", "placement", "clubs", "general"]
    target_department_id: uuid.UUID | None = None
    target_year: int | None = Field(default=None, ge=1, le=8)
    is_pinned: bool = False


class NoticeOut(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    domain: str
    target_department_id: uuid.UUID | None = None
    target_year: int | None = None
    created_by: uuid.UUID | None = None
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Events ────────────────────────────────────────────────────────────────── #

class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    domain: Literal["academic", "hostel", "placement", "clubs", "general"]
    event_date: date
    venue: str | None = None
    requires_registration: bool = False
    registration_deadline: date | None = None


class EventOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    domain: str
    event_date: date
    venue: str | None = None
    requires_registration: bool
    registration_deadline: date | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Assignments ───────────────────────────────────────────────────────────── #

class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    subject: str = Field(min_length=1, max_length=100)
    due_date: date
    file_url: str | None = None
    department_id: uuid.UUID
    semester: int | None = Field(default=None, ge=1, le=8)


class AssignmentOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    subject: str
    due_date: date
    file_url: str | None = None
    department_id: uuid.UUID
    semester: int | None = None
    faculty_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AI ────────────────────────────────────────────────────────────────────── #

class AIQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class AIQueryResponse(BaseModel):
    reply: str
    context_used: list[str] = []


# ── AI Admin Assistant ────────────────────────────────────────────────────── #

class ConversationContext(BaseModel):
    """Stateless conversation context passed from frontend"""
    department_id: uuid.UUID | None = None
    semester: int | None = Field(default=None, ge=1, le=8)
    pending_operation: dict | None = None  # For multi-turn operations


class ChatRequest(BaseModel):
    """Request to AI assistant chat endpoint"""
    message: str = Field(min_length=1, max_length=500)
    context: ConversationContext = Field(default_factory=ConversationContext)


class OperationResult(BaseModel):
    """Result of a timetable operation"""
    operation_type: Literal["add", "update", "delete", "replace", "query"]
    success: bool
    affected_entries_count: int = 0
    entries: list[TimetableOut] = []
    error_message: str | None = None


class ChatResponse(BaseModel):
    """Response from AI assistant chat endpoint"""
    reply: str  # Natural language response
    context: ConversationContext  # Updated context
    action_taken: OperationResult | None = None  # If operation was executed
    requires_confirmation: bool = False  # If destructive action needs confirmation


class ParsedIntent(BaseModel):
    """Internal model for LLM output"""
    intent: Literal["add", "update", "delete", "replace", "query", "help", "unclear"]
    parameters: dict
    missing_fields: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


# ── Attendance ────────────────────────────────────────────────────────────── #

class StudentBrief(BaseModel):
    """Minimal student info for the attendance roster."""
    id: uuid.UUID
    full_name: str
    email: str
    year_of_study: int | None = None

    model_config = {"from_attributes": True}


class AttendanceMarkItem(BaseModel):
    student_id: uuid.UUID
    status: Literal["present", "absent", "late"] = "present"


class AttendanceMarkRequest(BaseModel):
    """Bulk-mark attendance for a date + subject."""
    department_id: uuid.UUID
    year_of_study: int | None = Field(default=None, ge=1, le=8)
    subject: str = Field(default="General", min_length=1, max_length=100)
    attend_date: date
    records: list[AttendanceMarkItem] = Field(min_length=1)


class AttendanceRecordOut(BaseModel):
    id: int
    student_id: uuid.UUID
    department_id: uuid.UUID | None = None
    year_of_study: int | None = None
    subject: str
    attend_date: date
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceMarkResponse(BaseModel):
    success: bool
    message: str
    saved: int = 0


class AttendanceSummaryOut(BaseModel):
    """Per-student attendance summary (used by student view)."""
    total: int
    present: int
    absent: int
    late: int
    percentage: float
    records: list[AttendanceRecordOut] = []


# ── Attendance Predictor ──────────────────────────────────────────────────── #

class SubjectPrediction(BaseModel):
    subject: str
    present: int
    total: int
    percentage: float
    status: Literal["safe", "warning", "critical"]
    can_miss: int          # how many more classes can be missed and stay >= threshold
    must_attend: int       # consecutive classes to attend to recover (0 if already safe)
    recoverable: bool      # whether recovery to threshold is realistically possible
    message: str


class AttendancePrediction(BaseModel):
    threshold: int
    overall_percentage: float
    overall_status: Literal["safe", "warning", "critical"]
    at_risk_count: int
    subjects: list[SubjectPrediction] = []
    summary: str


# ── Mess Schedule (campus-wide, OCR upload) ───────────────────────────────── #

class MessScheduleOut(BaseModel):
    id: int
    day_of_week: str
    meal_type: str
    start_time: time | None = None
    end_time: time | None = None
    items: str
    is_special: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MessUploadResponse(BaseModel):
    success: bool
    message: str
    extracted_text: str = ""
    entries: list[dict] = []
    errors: list[str] = []


class MessConfirmRequest(BaseModel):
    entries: list[dict] = Field(min_length=1)


# ── Chat history ──────────────────────────────────────────────────────────── #

class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Wellbeing check-in (anonymous) ────────────────────────────────────────── #

class WellbeingCheckinCreate(BaseModel):
    mood: int = Field(ge=1, le=5)    # 1 very low .. 5 great
    stress: int = Field(ge=1, le=5)  # 1 none .. 5 overwhelmed
    sleep: int = Field(ge=1, le=5)   # 1 poor .. 5 excellent
    note: str | None = Field(default=None, max_length=500)


class WellbeingStatus(BaseModel):
    submitted: bool
    week_start: date


class WellbeingDeptStat(BaseModel):
    department: str
    responses: int
    avg_stress: float
    high_stress_pct: float


class WellbeingWeekPoint(BaseModel):
    week_start: date
    responses: int
    avg_mood: float
    avg_stress: float
    avg_sleep: float
    high_stress_pct: float


class WellbeingInsights(BaseModel):
    week_start: date
    responses: int
    avg_mood: float
    avg_stress: float
    avg_sleep: float
    high_stress_pct: float
    low_mood_pct: float
    status: Literal["calm", "watch", "elevated"]
    insight: str
    recommendations: list[str] = []
    departments: list[WellbeingDeptStat] = []
    trend: list[WellbeingWeekPoint] = []
    min_cohort: int = 3


# ── Mess sentiment (1-tap ratings) ────────────────────────────────────────── #

class MessRateRequest(BaseModel):
    meal_type: Literal["breakfast", "lunch", "snacks", "dinner"]
    rating: int = Field(ge=1, le=5)


class MessTodayRatings(BaseModel):
    rating_date: date
    ratings: dict[str, int] = {}  # meal_type -> rating already given today


class MealSentiment(BaseModel):
    meal_type: str
    count: int
    avg: float
    positive_pct: float
    negative_pct: float


class SentimentTrendPoint(BaseModel):
    day: date
    count: int
    avg: float


class MessSentiment(BaseModel):
    day: date
    total: int
    overall_avg: float
    meals: list[MealSentiment] = []
    trend: list[SentimentTrendPoint] = []
    alerts: list[str] = []


# ── Schedule conflict detection ───────────────────────────────────────────── #

class ScheduleConflict(BaseModel):
    type: Literal[
        "exam_room", "exam_student_overlap", "class_room", "class_faculty", "event_venue"
    ]
    severity: Literal["high", "medium", "low"]
    title: str
    detail: str
    when: str
    items: list[str] = []


class ConflictScanResult(BaseModel):
    scanned_at: datetime
    total: int
    counts: dict[str, int] = {}
    conflicts: list[ScheduleConflict] = []


class ClassSlotCheck(BaseModel):
    """A proposed class slot to check for conflicts before scheduling."""
    department_id: uuid.UUID
    semester: int = Field(ge=1, le=8)
    day_of_week: Literal[
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    start_time: time
    end_time: time
    subject: str = Field(min_length=1, max_length=100)
    room: str | None = Field(default=None, max_length=50)
    faculty_name: str | None = Field(default=None, max_length=100)


class SlotConflict(BaseModel):
    kind: Literal["room", "faculty", "cohort"]
    detail: str


class SlotCheckResult(BaseModel):
    has_conflict: bool
    conflicts: list[SlotConflict] = []


class FreeWindow(BaseModel):
    start: time
    end: time


class RoomFreeSlots(BaseModel):
    room: str
    free_windows: list[FreeWindow] = []


class FreeSlotsResult(BaseModel):
    day_of_week: str
    working_start: time
    working_end: time
    rooms: list[RoomFreeSlots] = []


# ── Smart Daily Digest ────────────────────────────────────────────────────── #

class DigestClass(BaseModel):
    subject: str
    start: str
    end: str
    room: str | None = None
    at_risk: bool = False


class DigestItem(BaseModel):
    title: str
    subtitle: str | None = None
    when: str | None = None
    urgent: bool = False


class DigestResponse(BaseModel):
    greeting: str
    date: str
    insight: str
    classes: list[DigestClass] = []
    assignments: list[DigestItem] = []
    deadlines: list[DigestItem] = []
    notices: list[DigestItem] = []
    events: list[DigestItem] = []
    attendance_alerts: list[DigestItem] = []
    quick_actions: list[str] = []
