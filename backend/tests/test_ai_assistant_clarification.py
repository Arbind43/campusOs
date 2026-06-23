"""Tests for AI Assistant clarification question logic.

Tests task 5.3: identify_missing_fields, prioritize_clarifications, and error message generation.

Requirements: 3.2, 3.3, 3.5, 9.1, 9.2, 9.3, 9.4
"""
import pytest
from app.services.ai_assistant_validator import (
    identify_missing_fields,
    prioritize_clarifications,
    generate_clarification_question,
    generate_validation_error_message,
)


# ─── Test identify_missing_fields ─────────────────────────────────────────────

def test_identify_missing_fields_add_all_missing():
    """Test identifying missing fields for add operation with nothing provided."""
    missing = identify_missing_fields("add", {}, {})
    
    assert "department_id" in missing
    assert "semester" in missing
    assert "day_of_week" in missing
    assert "start_time" in missing
    assert "subject" in missing


def test_identify_missing_fields_add_with_context():
    """Test that context fills in missing fields."""
    context = {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 5,
    }
    missing = identify_missing_fields("add", {}, context)
    
    assert "department_id" not in missing
    assert "semester" not in missing
    assert "day_of_week" in missing
    assert "start_time" in missing
    assert "subject" in missing


def test_identify_missing_fields_add_partial_params():
    """Test with some parameters provided."""
    parameters = {
        "day_of_week": "Monday",
        "subject": "Mathematics",
    }
    context = {
        "semester": 5,
    }
    missing = identify_missing_fields("add", parameters, context)
    
    assert "day_of_week" not in missing
    assert "subject" not in missing
    assert "semester" not in missing
    assert "department_id" in missing
    assert "start_time" in missing


def test_identify_missing_fields_add_all_present():
    """Test with all required fields present."""
    parameters = {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 5,
        "day_of_week": "Monday",
        "start_time": "09:00",
        "subject": "Mathematics",
    }
    missing = identify_missing_fields("add", parameters, {})
    
    assert len(missing) == 0


def test_identify_missing_fields_update():
    """Test identifying missing fields for update operation."""
    missing = identify_missing_fields("update", {}, {})
    
    assert "semester" in missing
    assert "day_of_week" in missing
    assert "start_time" in missing
    assert "subject" in missing
    # department_id not required for update identifier


def test_identify_missing_fields_delete():
    """Test identifying missing fields for delete operation."""
    missing = identify_missing_fields("delete", {}, {})
    
    assert "semester" in missing
    assert "day_of_week" in missing
    assert "subject" in missing
    # start_time is optional for delete


def test_identify_missing_fields_replace():
    """Test identifying missing fields for replace operation."""
    missing = identify_missing_fields("replace", {}, {})
    
    assert "department_id" in missing
    assert "semester" in missing


def test_identify_missing_fields_query():
    """Test query operation has no required fields."""
    missing = identify_missing_fields("query", {}, {})
    
    assert len(missing) == 0


# ─── Test prioritize_clarifications ───────────────────────────────────────────

def test_prioritize_clarifications_department_first():
    """Test that department_id is prioritized first."""
    missing = ["subject", "semester", "department_id", "day_of_week"]
    next_field = prioritize_clarifications(missing, "add")
    
    assert next_field == "department_id"


def test_prioritize_clarifications_semester_second():
    """Test that semester is prioritized after department."""
    missing = ["subject", "semester", "day_of_week", "start_time"]
    next_field = prioritize_clarifications(missing, "add")
    
    assert next_field == "semester"


def test_prioritize_clarifications_day_third():
    """Test that day_of_week is prioritized after semester."""
    missing = ["subject", "day_of_week", "start_time"]
    next_field = prioritize_clarifications(missing, "add")
    
    assert next_field == "day_of_week"


def test_prioritize_clarifications_time_before_subject():
    """Test that start_time is prioritized before subject."""
    missing = ["subject", "start_time"]
    next_field = prioritize_clarifications(missing, "add")
    
    assert next_field == "start_time"


def test_prioritize_clarifications_subject_last():
    """Test that subject comes after time fields."""
    missing = ["subject"]
    next_field = prioritize_clarifications(missing, "add")
    
    assert next_field == "subject"


def test_prioritize_clarifications_empty_list():
    """Test with no missing fields."""
    missing = []
    next_field = prioritize_clarifications(missing, "add")
    
    assert next_field == ""


def test_prioritize_clarifications_full_order():
    """Test the complete priority order."""
    missing = [
        "faculty_name",
        "room",
        "subject",
        "end_time",
        "start_time",
        "day_of_week",
        "semester",
        "department_id",
    ]
    
    # Should return department_id first
    assert prioritize_clarifications(missing, "add") == "department_id"
    
    # Remove department_id, should return semester
    missing.remove("department_id")
    assert prioritize_clarifications(missing, "add") == "semester"
    
    # Remove semester, should return day_of_week
    missing.remove("semester")
    assert prioritize_clarifications(missing, "add") == "day_of_week"
    
    # Remove day_of_week, should return start_time
    missing.remove("day_of_week")
    assert prioritize_clarifications(missing, "add") == "start_time"
    
    # Remove start_time, should return end_time
    missing.remove("start_time")
    assert prioritize_clarifications(missing, "add") == "end_time"
    
    # Remove end_time, should return subject
    missing.remove("end_time")
    assert prioritize_clarifications(missing, "add") == "subject"


# ─── Test generate_clarification_question ─────────────────────────────────────

def test_generate_clarification_question_semester_add():
    """Test semester clarification for add operation."""
    question = generate_clarification_question("semester", "add", {})
    
    assert "semester" in question.lower()
    assert "add" in question.lower()


def test_generate_clarification_question_semester_update():
    """Test semester clarification for update operation."""
    question = generate_clarification_question("semester", "update", {})
    
    assert "semester" in question.lower()
    assert "update" in question.lower()


def test_generate_clarification_question_day():
    """Test day_of_week clarification."""
    question = generate_clarification_question("day_of_week", "add", {})
    
    assert "day" in question.lower()


def test_generate_clarification_question_start_time_with_context():
    """Test start_time clarification with context."""
    context = {
        "day_of_week": "Monday",
        "subject": "Mathematics",
    }
    question = generate_clarification_question("start_time", "add", context)
    
    assert "Mathematics" in question
    assert "Monday" in question


def test_generate_clarification_question_start_time_no_context():
    """Test start_time clarification without context."""
    question = generate_clarification_question("start_time", "add", {})
    
    assert "time" in question.lower()
    # Should include format examples
    assert "9 AM" in question or "09:00" in question


def test_generate_clarification_question_subject_with_day():
    """Test subject clarification with day in context."""
    context = {
        "day_of_week": "Monday",
    }
    question = generate_clarification_question("subject", "add", context)
    
    assert "subject" in question.lower()
    assert "Monday" in question


def test_generate_clarification_question_subject_no_context():
    """Test subject clarification without context."""
    question = generate_clarification_question("subject", "add", {})
    
    assert "subject" in question.lower()


def test_generate_clarification_question_end_time_with_start():
    """Test end_time clarification when start_time is known."""
    context = {
        "start_time": "09:00",
    }
    question = generate_clarification_question("end_time", "add", context)
    
    assert "end" in question.lower()
    assert "09:00" in question


def test_generate_clarification_question_department():
    """Test department_id clarification."""
    question = generate_clarification_question("department_id", "add", {})
    
    assert "department" in question.lower()


def test_generate_clarification_question_room():
    """Test room clarification (optional field)."""
    question = generate_clarification_question("room", "add", {})
    
    assert "room" in question.lower()
    assert "optional" in question.lower()


def test_generate_clarification_question_faculty():
    """Test faculty_name clarification (optional field)."""
    question = generate_clarification_question("faculty_name", "add", {})
    
    assert "faculty" in question.lower()
    assert "optional" in question.lower()


# ─── Test generate_validation_error_message ───────────────────────────────────

def test_generate_validation_error_invalid_day():
    """Test error message for invalid day name."""
    error = generate_validation_error_message("day_of_week", "invalid_day", "Mondai")
    
    assert "Mondai" in error
    assert "Monday" in error
    assert "Sunday" in error


def test_generate_validation_error_invalid_day_no_value():
    """Test error message for invalid day without value."""
    error = generate_validation_error_message("day_of_week", "invalid_day")
    
    assert "Invalid day" in error
    assert "Monday" in error


def test_generate_validation_error_invalid_time():
    """Test error message for invalid time format."""
    error = generate_validation_error_message("start_time", "invalid_time", "25:00")
    
    assert "25:00" in error
    assert "9 AM" in error or "09:00" in error


def test_generate_validation_error_invalid_time_no_value():
    """Test error message for invalid time without value."""
    error = generate_validation_error_message("start_time", "invalid_time")
    
    assert "Invalid time" in error
    assert "9 AM" in error or "09:00" in error


def test_generate_validation_error_time_order():
    """Test error message for start_time >= end_time."""
    error = generate_validation_error_message("start_time", "time_order")
    
    assert "Start time" in error
    assert "before" in error
    assert "end time" in error


def test_generate_validation_error_semester_range():
    """Test error message for semester out of range."""
    error = generate_validation_error_message("semester", "semester_range", 9)
    
    assert "9" in error
    assert "1" in error
    assert "8" in error


def test_generate_validation_error_semester_range_no_value():
    """Test error message for semester range without value."""
    error = generate_validation_error_message("semester", "semester_range")
    
    assert "1" in error
    assert "8" in error


def test_generate_validation_error_empty_subject():
    """Test error message for empty subject."""
    error = generate_validation_error_message("subject", "empty_subject")
    
    assert "Subject" in error
    assert "empty" in error.lower()


def test_generate_validation_error_subject_too_long():
    """Test error message for subject too long."""
    error = generate_validation_error_message("subject", "subject_too_long")
    
    assert "too long" in error.lower()
    assert "100" in error


def test_generate_validation_error_room_too_long():
    """Test error message for room too long."""
    error = generate_validation_error_message("room", "room_too_long")
    
    assert "too long" in error.lower()
    assert "50" in error


def test_generate_validation_error_faculty_too_long():
    """Test error message for faculty name too long."""
    error = generate_validation_error_message("faculty_name", "faculty_too_long")
    
    assert "too long" in error.lower()
    assert "100" in error


def test_generate_validation_error_invalid_department():
    """Test error message for invalid department identifier."""
    error = generate_validation_error_message("department_id", "invalid_department", "abc")
    
    assert "abc" in error
    assert "Invalid" in error
    assert "department" in error.lower()


def test_generate_validation_error_unknown_type():
    """Test fallback error message for unknown error type."""
    error = generate_validation_error_message("some_field", "unknown_error")
    
    assert "some_field" in error
    assert "unknown_error" in error


# ─── Integration Tests ────────────────────────────────────────────────────────

def test_clarification_flow_add_operation():
    """Test complete clarification flow for add operation."""
    # Start with minimal info
    params = {}
    context = {}
    
    # Identify missing fields
    missing = identify_missing_fields("add", params, context)
    assert len(missing) > 0
    
    # Get first field to ask about (should be department_id)
    next_field = prioritize_clarifications(missing, "add")
    assert next_field == "department_id"
    
    # Generate question
    question = generate_clarification_question(next_field, "add", context)
    assert "department" in question.lower()
    
    # User provides department, add to context
    context["department_id"] = "123e4567-e89b-12d3-a456-426614174000"
    
    # Check what's still missing
    missing = identify_missing_fields("add", params, context)
    next_field = prioritize_clarifications(missing, "add")
    assert next_field == "semester"


def test_clarification_flow_progressive():
    """Test progressive clarification with context building."""
    params = {"subject": "Mathematics"}
    context = {}
    
    # Round 1: Need department
    missing = identify_missing_fields("add", params, context)
    next_field = prioritize_clarifications(missing, "add")
    assert next_field == "department_id"
    
    # Round 2: Add department, need semester
    context["department_id"] = "123e4567-e89b-12d3-a456-426614174000"
    missing = identify_missing_fields("add", params, context)
    next_field = prioritize_clarifications(missing, "add")
    assert next_field == "semester"
    
    # Round 3: Add semester, need day
    context["semester"] = 5
    missing = identify_missing_fields("add", params, context)
    next_field = prioritize_clarifications(missing, "add")
    assert next_field == "day_of_week"
    
    # Round 4: Add day, need time
    context["day_of_week"] = "Monday"
    missing = identify_missing_fields("add", params, context)
    next_field = prioritize_clarifications(missing, "add")
    assert next_field == "start_time"
    
    # Round 5: Add time, should be complete (subject already in params)
    context["start_time"] = "09:00"
    missing = identify_missing_fields("add", params, context)
    assert len(missing) == 0


def test_clarification_with_validation_error():
    """Test that validation errors generate helpful messages."""
    # Invalid day
    error = generate_validation_error_message("day_of_week", "invalid_day", "Mondai")
    assert "Monday" in error
    assert "Mondai" in error
    
    # Invalid time
    error = generate_validation_error_message("start_time", "invalid_time", "25:99")
    assert "25:99" in error
    assert "9 AM" in error or "09:00" in error
    
    # Time ordering
    error = generate_validation_error_message("start_time", "time_order")
    assert "before" in error
