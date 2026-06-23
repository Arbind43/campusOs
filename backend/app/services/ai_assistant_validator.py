"""Parameter validator for AI Assistant timetable operations.

This module provides validation for parameters extracted from natural language
by the LLM service. It enforces business rules and required fields for each
operation type (add, update, delete, replace, query).

Requirements: 4.1, 4.2, 4.3, 5.1, 6.1, 7.1
"""
import logging
import re
import uuid
from datetime import time
from typing import Any

from app.core.logging_config import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)


# ─── Constants ────────────────────────────────────────────────────────────────

VALID_DAYS = {
    "Monday", "Tuesday", "Wednesday", "Thursday", 
    "Friday", "Saturday", "Sunday"
}

MIN_SEMESTER = 1
MAX_SEMESTER = 8

MAX_SUBJECT_LENGTH = 100
MAX_ROOM_LENGTH = 50
MAX_FACULTY_NAME_LENGTH = 100


# ─── Validation Error Class ──────────────────────────────────────────────────

class ValidationError(Exception):
    """Raised when parameter validation fails."""
    
    def __init__(self, message: str, field: str | None = None):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: Name of the field that failed validation (optional)
        """
        super().__init__(message)
        self.message = message
        self.field = field


# ─── Parameter Validator Class ───────────────────────────────────────────────

class ParameterValidator:
    """
    Validates parameters extracted by LLM service for timetable operations.
    
    Provides validation methods for each operation type (add, update, delete,
    replace, query) and enforces business rules like time ordering, semester
    range, field length limits, etc.
    
    Requirements: 4.1, 4.2, 4.3, 5.1, 6.1, 7.1
    """
    
    def __init__(self):
        """Initialize parameter validator."""
        structured_logger.info("Parameter validator initialized")
    
    # ─── Add Operation Validation ─────────────────────────────────────────────
    
    def validate_add_parameters(
        self,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[bool, list[str], str | None]:
        """
        Validate parameters for add timetable entry operation.
        
        Required fields:
        - day_of_week: Valid day name (Monday-Sunday)
        - start_time: Time in HH:MM format
        - subject: Non-empty subject name (1-100 chars)
        - semester: Integer 1-8
        - department_id: Valid UUID
        
        Optional fields:
        - end_time: Time in HH:MM format (defaults to start_time + 1 hour)
        - room: Room identifier (max 50 chars)
        - faculty_name: Faculty name (max 100 chars)
        
        Business rules:
        - start_time must be before end_time
        - All time values must be valid HH:MM format
        - semester must be in range 1-8
        
        Args:
            parameters: Extracted parameters from LLM
            context: Conversation context with defaults
            
        Returns:
            Tuple of (is_valid, missing_fields, error_message)
            - is_valid: True if all required fields valid
            - missing_fields: List of missing required field names
            - error_message: Human-readable error or None if valid
            
        Requirements: 4.1, 4.2, 4.3
        """
        structured_logger.info(
            "Validating add parameters",
            parameters_count=len(parameters),
            has_context=bool(context),
        )
        
        # Merge context into parameters (context provides defaults)
        merged = {**context, **parameters}
        
        missing_fields = []
        error_message = None
        
        # ─── Check Required Fields ────────────────────────────────────────────
        
        # Check day_of_week
        if not merged.get("day_of_week"):
            missing_fields.append("day_of_week")
        
        # Check start_time
        if not merged.get("start_time"):
            missing_fields.append("start_time")
        
        # Check subject
        if not merged.get("subject"):
            missing_fields.append("subject")
        
        # Check semester
        if not merged.get("semester"):
            missing_fields.append("semester")
        
        # Check department_id
        if not merged.get("department_id"):
            missing_fields.append("department_id")
        
        # If any required fields are missing, return early
        if missing_fields:
            structured_logger.info(
                "Add validation failed: missing required fields",
                missing_fields=missing_fields,
            )
            return (False, missing_fields, None)
        
        # ─── Validate Field Values ────────────────────────────────────────────
        
        try:
            # Validate day_of_week
            day = merged["day_of_week"]
            if day not in VALID_DAYS:
                error_message = (
                    f"Invalid day name: {day}. "
                    "Please use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday."
                )
                raise ValidationError(error_message, "day_of_week")
            
            # Validate semester range
            semester = merged["semester"]
            if not isinstance(semester, int) or semester < MIN_SEMESTER or semester > MAX_SEMESTER:
                error_message = f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
                raise ValidationError(error_message, "semester")
            
            # Validate subject length
            subject = merged["subject"]
            if not isinstance(subject, str) or len(subject.strip()) == 0:
                error_message = "Subject name cannot be empty."
                raise ValidationError(error_message, "subject")
            if len(subject) > MAX_SUBJECT_LENGTH:
                error_message = f"Subject name is too long. Please keep it under {MAX_SUBJECT_LENGTH} characters."
                raise ValidationError(error_message, "subject")
            
            # Validate start_time format
            start_time = merged["start_time"]
            if not self._is_valid_time_format(start_time):
                error_message = (
                    f"Invalid start time format: {start_time}. "
                    "Please use HH:MM format (e.g., '09:00', '14:30')."
                )
                raise ValidationError(error_message, "start_time")
            
            # Validate end_time if provided
            end_time = merged.get("end_time")
            if end_time and not self._is_valid_time_format(end_time):
                error_message = (
                    f"Invalid end time format: {end_time}. "
                    "Please use HH:MM format (e.g., '10:00', '15:30')."
                )
                raise ValidationError(error_message, "end_time")
            
            # Validate start_time < end_time
            if end_time:
                if not self._is_time_before(start_time, end_time):
                    error_message = "Start time must be before end time."
                    raise ValidationError(error_message, "start_time")
            
            # Validate optional fields if provided
            room = merged.get("room")
            if room and len(room) > MAX_ROOM_LENGTH:
                error_message = f"Room identifier is too long. Please keep it under {MAX_ROOM_LENGTH} characters."
                raise ValidationError(error_message, "room")
            
            faculty_name = merged.get("faculty_name")
            if faculty_name and len(faculty_name) > MAX_FACULTY_NAME_LENGTH:
                error_message = f"Faculty name is too long. Please keep it under {MAX_FACULTY_NAME_LENGTH} characters."
                raise ValidationError(error_message, "faculty_name")
            
            # Validate department_id is valid UUID
            department_id = merged.get("department_id")
            if department_id:
                try:
                    if isinstance(department_id, str):
                        uuid.UUID(department_id)
                except (ValueError, AttributeError):
                    error_message = f"Invalid department identifier: {department_id}."
                    raise ValidationError(error_message, "department_id")
            
            structured_logger.info(
                "Add parameters validated successfully",
                subject=subject,
                day=day,
                semester=semester,
            )
            
            return (True, [], None)
        
        except ValidationError as e:
            structured_logger.warning(
                "Add validation failed: business rule violation",
                field=e.field,
                error=e.message,
            )
            return (False, [], e.message)
    
    # ─── Update Operation Validation ──────────────────────────────────────────
    
    def validate_update_parameters(
        self,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[bool, list[str], str | None]:
        """
        Validate parameters for update timetable entry operation.
        
        Required fields (identifier):
        - day_of_week: To identify which entry to update
        - start_time: To identify which entry to update
        - subject: To identify which entry to update
        - semester: To identify which entry to update
        
        At least one field to change must be provided.
        
        Business rules:
        - If changing start_time or end_time, start_time must be < end_time
        - Changed fields follow same validation as add operation
        
        Args:
            parameters: Extracted parameters from LLM
            context: Conversation context with defaults
            
        Returns:
            Tuple of (is_valid, missing_fields, error_message)
            
        Requirements: 5.1, 5.2, 5.3
        """
        structured_logger.info(
            "Validating update parameters",
            parameters_count=len(parameters),
            has_context=bool(context),
        )
        
        # Merge context into parameters
        merged = {**context, **parameters}
        
        missing_fields = []
        error_message = None
        
        # ─── Check Required Identifier Fields ────────────────────────────────
        
        if not merged.get("day_of_week"):
            missing_fields.append("day_of_week")
        
        if not merged.get("start_time"):
            missing_fields.append("start_time")
        
        if not merged.get("subject"):
            missing_fields.append("subject")
        
        if not merged.get("semester"):
            missing_fields.append("semester")
        
        # If identifier fields are missing, return early
        if missing_fields:
            structured_logger.info(
                "Update validation failed: missing identifier fields",
                missing_fields=missing_fields,
            )
            return (False, missing_fields, None)
        
        # ─── Validate Identifier Field Values ────────────────────────────────
        
        try:
            # Validate day_of_week
            day = merged["day_of_week"]
            if day not in VALID_DAYS:
                error_message = (
                    f"Invalid day name: {day}. "
                    "Please use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday."
                )
                raise ValidationError(error_message, "day_of_week")
            
            # Validate semester range
            semester = merged["semester"]
            if not isinstance(semester, int) or semester < MIN_SEMESTER or semester > MAX_SEMESTER:
                error_message = f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
                raise ValidationError(error_message, "semester")
            
            # Validate start_time format
            start_time = merged["start_time"]
            if not self._is_valid_time_format(start_time):
                error_message = (
                    f"Invalid start time format: {start_time}. "
                    "Please use HH:MM format."
                )
                raise ValidationError(error_message, "start_time")
            
            # Validate subject
            subject = merged["subject"]
            if not isinstance(subject, str) or len(subject.strip()) == 0:
                error_message = "Subject name cannot be empty."
                raise ValidationError(error_message, "subject")
            
            # ─── Validate Changed Fields (if any) ────────────────────────────
            
            # Check if end_time is being updated
            if parameters.get("end_time"):
                end_time = parameters["end_time"]
                if not self._is_valid_time_format(end_time):
                    error_message = (
                        f"Invalid end time format: {end_time}. "
                        "Please use HH:MM format."
                    )
                    raise ValidationError(error_message, "end_time")
                
                # If updating end_time, validate against start_time
                if not self._is_time_before(start_time, end_time):
                    error_message = "Start time must be before end time."
                    raise ValidationError(error_message, "end_time")
            
            # Validate room if being updated
            if parameters.get("room"):
                room = parameters["room"]
                if len(room) > MAX_ROOM_LENGTH:
                    error_message = f"Room identifier is too long. Please keep it under {MAX_ROOM_LENGTH} characters."
                    raise ValidationError(error_message, "room")
            
            # Validate faculty_name if being updated
            if parameters.get("faculty_name"):
                faculty_name = parameters["faculty_name"]
                if len(faculty_name) > MAX_FACULTY_NAME_LENGTH:
                    error_message = f"Faculty name is too long. Please keep it under {MAX_FACULTY_NAME_LENGTH} characters."
                    raise ValidationError(error_message, "faculty_name")
            
            structured_logger.info(
                "Update parameters validated successfully",
                identifier=f"{day} {start_time} {subject}",
                semester=semester,
            )
            
            return (True, [], None)
        
        except ValidationError as e:
            structured_logger.warning(
                "Update validation failed: business rule violation",
                field=e.field,
                error=e.message,
            )
            return (False, [], e.message)
    
    # ─── Delete Operation Validation ──────────────────────────────────────────
    
    def validate_delete_parameters(
        self,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[bool, list[str], str | None]:
        """
        Validate parameters for delete timetable entry operation.
        
        Required fields (identifier):
        - day_of_week: To identify which entry to delete
        - subject: To identify which entry to delete
        - semester: To identify which entry to delete
        
        Optional but helpful:
        - start_time: For more precise identification
        
        Business rules:
        - Must provide enough information to uniquely identify entry
        
        Args:
            parameters: Extracted parameters from LLM
            context: Conversation context with defaults
            
        Returns:
            Tuple of (is_valid, missing_fields, error_message)
            
        Requirements: 6.1, 6.2, 6.3
        """
        structured_logger.info(
            "Validating delete parameters",
            parameters_count=len(parameters),
            has_context=bool(context),
        )
        
        # Merge context into parameters
        merged = {**context, **parameters}
        
        missing_fields = []
        error_message = None
        
        # ─── Check Required Identifier Fields ────────────────────────────────
        
        if not merged.get("day_of_week"):
            missing_fields.append("day_of_week")
        
        if not merged.get("subject"):
            missing_fields.append("subject")
        
        if not merged.get("semester"):
            missing_fields.append("semester")
        
        # If identifier fields are missing, return early
        if missing_fields:
            structured_logger.info(
                "Delete validation failed: missing identifier fields",
                missing_fields=missing_fields,
            )
            return (False, missing_fields, None)
        
        # ─── Validate Identifier Field Values ────────────────────────────────
        
        try:
            # Validate day_of_week
            day = merged["day_of_week"]
            if day not in VALID_DAYS:
                error_message = (
                    f"Invalid day name: {day}. "
                    "Please use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday."
                )
                raise ValidationError(error_message, "day_of_week")
            
            # Validate semester range
            semester = merged["semester"]
            if not isinstance(semester, int) or semester < MIN_SEMESTER or semester > MAX_SEMESTER:
                error_message = f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
                raise ValidationError(error_message, "semester")
            
            # Validate subject
            subject = merged["subject"]
            if not isinstance(subject, str) or len(subject.strip()) == 0:
                error_message = "Subject name cannot be empty."
                raise ValidationError(error_message, "subject")
            
            # Validate start_time if provided (optional but helpful)
            start_time = merged.get("start_time")
            if start_time and not self._is_valid_time_format(start_time):
                error_message = (
                    f"Invalid start time format: {start_time}. "
                    "Please use HH:MM format."
                )
                raise ValidationError(error_message, "start_time")
            
            structured_logger.info(
                "Delete parameters validated successfully",
                identifier=f"{day} {subject}",
                semester=semester,
                has_time=bool(start_time),
            )
            
            return (True, [], None)
        
        except ValidationError as e:
            structured_logger.warning(
                "Delete validation failed: business rule violation",
                field=e.field,
                error=e.message,
            )
            return (False, [], e.message)
    
    # ─── Replace Operation Validation ─────────────────────────────────────────
    
    def validate_replace_parameters(
        self,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[bool, list[str], str | None]:
        """
        Validate parameters for replace entire timetable operation.
        
        Required fields:
        - semester: Which semester's timetable to replace
        - department_id: Which department's timetable to replace
        
        Optional:
        - entries: List of new timetable entries (validated individually)
        
        Business rules:
        - Each entry in the list must pass add validation
        - At least one entry should be provided (though can be validated later)
        
        Args:
            parameters: Extracted parameters from LLM
            context: Conversation context with defaults
            
        Returns:
            Tuple of (is_valid, missing_fields, error_message)
            
        Requirements: 7.1, 7.2, 7.3
        """
        structured_logger.info(
            "Validating replace parameters",
            parameters_count=len(parameters),
            has_context=bool(context),
        )
        
        # Merge context into parameters
        merged = {**context, **parameters}
        
        missing_fields = []
        error_message = None
        
        # ─── Check Required Fields ────────────────────────────────────────────
        
        # Check semester exists (allow 0 for now, will validate range later)
        if merged.get("semester") is None:
            missing_fields.append("semester")
        
        if not merged.get("department_id"):
            missing_fields.append("department_id")
        
        # If required fields are missing, return early
        if missing_fields:
            structured_logger.info(
                "Replace validation failed: missing required fields",
                missing_fields=missing_fields,
            )
            return (False, missing_fields, None)
        
        # ─── Validate Field Values ────────────────────────────────────────────
        
        try:
            # Validate semester range
            semester = merged["semester"]
            if not isinstance(semester, int) or semester < MIN_SEMESTER or semester > MAX_SEMESTER:
                error_message = f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
                raise ValidationError(error_message, "semester")
            
            # Validate department_id is valid UUID
            department_id = merged.get("department_id")
            if department_id:
                try:
                    if isinstance(department_id, str):
                        uuid.UUID(department_id)
                except (ValueError, AttributeError):
                    error_message = f"Invalid department identifier: {department_id}."
                    raise ValidationError(error_message, "department_id")
            
            # Validate entries list if provided
            entries = merged.get("entries", [])
            if entries:
                if not isinstance(entries, list):
                    error_message = "Entries must be a list of timetable entries."
                    raise ValidationError(error_message, "entries")
                
                # Validate each entry individually
                for i, entry in enumerate(entries):
                    # Each entry should have the required fields for add operation
                    entry_context = {
                        "semester": semester,
                        "department_id": department_id,
                    }
                    is_valid, missing, err_msg = self.validate_add_parameters(entry, entry_context)
                    
                    if not is_valid:
                        if missing:
                            error_message = f"Entry {i+1} is missing required fields: {', '.join(missing)}."
                        else:
                            error_message = f"Entry {i+1} validation failed: {err_msg}"
                        raise ValidationError(error_message, "entries")
            
            structured_logger.info(
                "Replace parameters validated successfully",
                semester=semester,
                entries_count=len(entries),
            )
            
            return (True, [], None)
        
        except ValidationError as e:
            structured_logger.warning(
                "Replace validation failed: business rule violation",
                field=e.field,
                error=e.message,
            )
            return (False, [], e.message)
    
    # ─── Query Operation Validation ───────────────────────────────────────────
    
    def validate_query_parameters(
        self,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[bool, list[str], str | None]:
        """
        Validate parameters for query timetable operation.
        
        Required fields:
        - None (query is flexible)
        
        Optional filters:
        - semester: Integer 1-8
        - day_of_week: Valid day name
        - subject: Subject name
        
        Business rules:
        - All provided filters must be valid
        - Query can work without any filters (returns all)
        
        Args:
            parameters: Extracted parameters from LLM
            context: Conversation context with defaults
            
        Returns:
            Tuple of (is_valid, missing_fields, error_message)
            
        Requirements: 7.1
        """
        structured_logger.info(
            "Validating query parameters",
            parameters_count=len(parameters),
            has_context=bool(context),
        )
        
        # Merge context into parameters
        merged = {**context, **parameters}
        
        error_message = None
        
        # ─── Validate Optional Filter Values ──────────────────────────────────
        
        try:
            # Validate day_of_week if provided
            day = merged.get("day_of_week")
            if day and day not in VALID_DAYS:
                error_message = (
                    f"Invalid day name: {day}. "
                    "Please use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday."
                )
                raise ValidationError(error_message, "day_of_week")
            
            # Validate semester if provided
            semester = merged.get("semester")
            if semester:
                if not isinstance(semester, int) or semester < MIN_SEMESTER or semester > MAX_SEMESTER:
                    error_message = f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
                    raise ValidationError(error_message, "semester")
            
            # Validate subject if provided
            subject = merged.get("subject")
            if subject:
                if not isinstance(subject, str) or len(subject.strip()) == 0:
                    error_message = "Subject name cannot be empty."
                    raise ValidationError(error_message, "subject")
            
            structured_logger.info(
                "Query parameters validated successfully",
                has_day_filter=bool(day),
                has_semester_filter=bool(semester),
                has_subject_filter=bool(subject),
            )
            
            return (True, [], None)
        
        except ValidationError as e:
            structured_logger.warning(
                "Query validation failed: invalid filter",
                field=e.field,
                error=e.message,
            )
            return (False, [], e.message)
    
    # ─── Helper Methods ───────────────────────────────────────────────────────
    
    def _is_valid_time_format(self, time_str: str | None) -> bool:
        """
        Check if time string is in valid HH:MM format.
        
        Args:
            time_str: Time string to validate
            
        Returns:
            True if valid HH:MM format, False otherwise
        """
        if not time_str or not isinstance(time_str, str):
            return False
        
        # Pattern: HH:MM where HH is 00-23 and MM is 00-59
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        match = re.match(pattern, time_str)
        
        return match is not None
    
    def _is_time_before(self, start_time: str, end_time: str) -> bool:
        """
        Check if start_time is before end_time.
        
        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            
        Returns:
            True if start_time < end_time, False otherwise
        """
        try:
            # Parse time strings
            start_parts = start_time.split(":")
            end_parts = end_time.split(":")
            
            start_hour = int(start_parts[0])
            start_minute = int(start_parts[1])
            
            end_hour = int(end_parts[0])
            end_minute = int(end_parts[1])
            
            # Compare times
            start_total_minutes = start_hour * 60 + start_minute
            end_total_minutes = end_hour * 60 + end_minute
            
            return start_total_minutes < end_total_minutes
        
        except (IndexError, ValueError):
            return False


# ─── Clarification Question Logic ────────────────────────────────────────────

def identify_missing_fields(
    intent: str,
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> list[str]:
    """
    Identify missing required fields for a given operation intent.
    
    This function determines which required fields are missing based on
    the operation type and the current parameters and context.
    
    Args:
        intent: Operation intent (add, update, delete, replace, query)
        parameters: Extracted parameters from LLM
        context: Conversation context with defaults
        
    Returns:
        List of missing required field names
        
    Requirements: 3.2, 3.3, 3.5
    
    Examples:
        >>> identify_missing_fields("add", {"day_of_week": "Monday"}, {})
        ['department_id', 'semester', 'start_time', 'subject']
        
        >>> identify_missing_fields("add", {}, {"department_id": "...", "semester": 5})
        ['day_of_week', 'start_time', 'subject']
    """
    # Merge context into parameters
    merged = {**context, **parameters}
    
    missing_fields = []
    
    if intent == "add":
        # Required fields for add operation
        if not merged.get("department_id"):
            missing_fields.append("department_id")
        if not merged.get("semester"):
            missing_fields.append("semester")
        if not merged.get("day_of_week"):
            missing_fields.append("day_of_week")
        if not merged.get("start_time"):
            missing_fields.append("start_time")
        if not merged.get("subject"):
            missing_fields.append("subject")
    
    elif intent == "update":
        # Required identifier fields for update operation
        if not merged.get("semester"):
            missing_fields.append("semester")
        if not merged.get("day_of_week"):
            missing_fields.append("day_of_week")
        if not merged.get("start_time"):
            missing_fields.append("start_time")
        if not merged.get("subject"):
            missing_fields.append("subject")
    
    elif intent == "delete":
        # Required identifier fields for delete operation
        if not merged.get("semester"):
            missing_fields.append("semester")
        if not merged.get("day_of_week"):
            missing_fields.append("day_of_week")
        if not merged.get("subject"):
            missing_fields.append("subject")
    
    elif intent == "replace":
        # Required fields for replace operation
        if not merged.get("department_id"):
            missing_fields.append("department_id")
        if not merged.get("semester"):
            missing_fields.append("semester")
    
    # Query and other intents don't have required fields
    
    structured_logger.info(
        "Identified missing fields",
        intent=intent,
        missing_count=len(missing_fields),
        missing_fields=missing_fields,
    )
    
    return missing_fields


def prioritize_clarifications(
    missing_fields: list[str],
    intent: str,
) -> str:
    """
    Select the next field to ask for clarification, following priority order.
    
    Priority order: department_id → semester → day_of_week → start_time → subject → end_time → room → faculty_name
    
    This ensures we ask for foundational context (department, semester) before
    specific details (time, subject).
    
    Args:
        missing_fields: List of missing field names
        intent: Operation intent (for context in question generation)
        
    Returns:
        The highest-priority missing field name, or empty string if none missing
        
    Requirements: 3.5
    
    Examples:
        >>> prioritize_clarifications(["subject", "semester", "day_of_week"], "add")
        'semester'
        
        >>> prioritize_clarifications(["start_time", "subject"], "add")
        'start_time'
    """
    if not missing_fields:
        return ""
    
    # Define priority order
    priority_order = [
        "department_id",
        "semester",
        "day_of_week",
        "start_time",
        "end_time",
        "subject",
        "room",
        "faculty_name",
    ]
    
    # Find the first field in priority order that is missing
    for field in priority_order:
        if field in missing_fields:
            structured_logger.info(
                "Prioritized clarification field",
                field=field,
                intent=intent,
                total_missing=len(missing_fields),
            )
            return field
    
    # If no priority field found, return first missing field
    # (this shouldn't happen with the current priority order)
    return missing_fields[0]


def generate_clarification_question(
    field: str,
    intent: str,
    context: dict[str, Any],
) -> str:
    """
    Generate a natural language clarification question for a missing field.
    
    Creates context-aware, conversational questions that guide the admin
    to provide the missing information.
    
    Args:
        field: The field name to ask about
        intent: Operation intent (for context)
        context: Current conversation context
        
    Returns:
        Natural language clarification question
        
    Requirements: 3.2, 3.3, 3.5
    
    Examples:
        >>> generate_clarification_question("semester", "add", {})
        "Which semester is this for?"
        
        >>> generate_clarification_question("subject", "add", {"day_of_week": "Monday"})
        "What subject would you like to add on Monday?"
    """
    # Generate questions based on field and context
    
    if field == "department_id":
        return "Which department is this for?"
    
    elif field == "semester":
        if intent == "add":
            return "Which semester would you like to add this class to?"
        elif intent == "update":
            return "Which semester would you like to update?"
        elif intent == "delete":
            return "Which semester is the class in?"
        elif intent == "replace":
            return "Which semester would you like to replace the timetable for?"
        else:
            return "Which semester is this for?"
    
    elif field == "day_of_week":
        if intent == "add":
            return "Which day of the week should this class be scheduled?"
        elif intent == "update":
            return "Which day is the class you want to update?"
        elif intent == "delete":
            return "Which day is the class you want to delete?"
        else:
            return "Which day of the week?"
    
    elif field == "start_time":
        subject = context.get("subject", "the class")
        day = context.get("day_of_week", "")
        
        if intent == "add":
            if day:
                return f"What time should {subject} start on {day}? (e.g., '9 AM', '09:00', '14:30')"
            else:
                return f"What time should {subject} start? (e.g., '9 AM', '09:00', '14:30')"
        elif intent == "update":
            return "What is the start time of the class you want to update?"
        else:
            return "What is the start time?"
    
    elif field == "end_time":
        start_time = context.get("start_time", "")
        if start_time:
            return f"What time should the class end? (e.g., '10 AM', '10:00') [or leave blank to default to 1 hour after {start_time}]"
        else:
            return "What time should the class end? (e.g., '10 AM', '10:00')"
    
    elif field == "subject":
        day = context.get("day_of_week", "")
        
        if intent == "add":
            if day:
                return f"What subject would you like to add on {day}?"
            else:
                return "What subject would you like to add?"
        elif intent == "update":
            return "What is the subject name of the class you want to update?"
        elif intent == "delete":
            return "What is the subject name of the class you want to delete?"
        else:
            return "What subject?"
    
    elif field == "room":
        return "Which room should this class be in? (optional)"
    
    elif field == "faculty_name":
        return "Who is the faculty member for this class? (optional)"
    
    else:
        # Generic fallback
        return f"Please provide the {field.replace('_', ' ')}."


def generate_validation_error_message(
    field: str,
    error_type: str,
    value: Any = None,
) -> str:
    """
    Generate specific error messages for validation failures.
    
    Creates user-friendly error messages that explain what went wrong
    and how to fix it.
    
    Args:
        field: The field that failed validation
        error_type: Type of validation error (invalid_day, invalid_time, time_order, semester_range, etc.)
        value: The invalid value (optional, for context)
        
    Returns:
        User-friendly error message
        
    Requirements: 9.1, 9.2, 9.3, 9.4
    
    Examples:
        >>> generate_validation_error_message("day_of_week", "invalid_day", "Mondai")
        "Invalid day name: Mondai. Please use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday."
        
        >>> generate_validation_error_message("start_time", "time_order")
        "Start time must be before end time."
    """
    if error_type == "invalid_day":
        day_list = ", ".join(VALID_DAYS)
        if value:
            return f"Invalid day name: {value}. Please use {day_list}."
        else:
            return f"Invalid day name. Please use {day_list}."
    
    elif error_type == "invalid_time":
        if value:
            return f"Invalid time format: {value}. Please use formats like '9 AM', '09:00', or '14:30'."
        else:
            return "Invalid time format. Please use formats like '9 AM', '09:00', or '14:30'."
    
    elif error_type == "time_order":
        return "Start time must be before end time. Please specify a valid time range."
    
    elif error_type == "semester_range":
        if value:
            return f"Invalid semester: {value}. Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
        else:
            return f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
    
    elif error_type == "empty_subject":
        return "Subject name cannot be empty. Please provide a subject name for the class."
    
    elif error_type == "subject_too_long":
        return f"Subject name is too long. Please keep it under {MAX_SUBJECT_LENGTH} characters."
    
    elif error_type == "room_too_long":
        return f"Room identifier is too long. Please keep it under {MAX_ROOM_LENGTH} characters."
    
    elif error_type == "faculty_too_long":
        return f"Faculty name is too long. Please keep it under {MAX_FACULTY_NAME_LENGTH} characters."
    
    elif error_type == "invalid_department":
        if value:
            return f"Invalid department identifier: {value}."
        else:
            return "Invalid department identifier."
    
    else:
        # Generic fallback
        return f"Validation error for {field}: {error_type}"


# ─── Convenience Functions ────────────────────────────────────────────────────

def validate_parameters(
    intent: str,
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> tuple[bool, list[str], str | None]:
    """
    Validate parameters for any operation type.
    
    This is a convenience function that delegates to the appropriate
    validator method based on the intent.
    
    Args:
        intent: Operation intent (add, update, delete, replace, query)
        parameters: Extracted parameters from LLM
        context: Conversation context with defaults
        
    Returns:
        Tuple of (is_valid, missing_fields, error_message)
        
    Examples:
        >>> validate_parameters("add", {"day_of_week": "Monday", ...}, {})
        (True, [], None)
        >>> validate_parameters("add", {"day_of_week": "InvalidDay"}, {})
        (False, [], "Invalid day name: InvalidDay. Please use Monday, ...")
    """
    validator = ParameterValidator()
    
    if intent == "add":
        return validator.validate_add_parameters(parameters, context)
    elif intent == "update":
        return validator.validate_update_parameters(parameters, context)
    elif intent == "delete":
        return validator.validate_delete_parameters(parameters, context)
    elif intent == "replace":
        return validator.validate_replace_parameters(parameters, context)
    elif intent == "query":
        return validator.validate_query_parameters(parameters, context)
    elif intent in ("help", "unclear"):
        # No validation needed for help and unclear intents
        return (True, [], None)
    else:
        # Unknown intent
        structured_logger.warning(
            "Unknown intent for validation",
            intent=intent,
        )
        return (False, [], f"Unknown operation intent: {intent}")
