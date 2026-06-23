"""Integration test for clarification question logic with validator.

Tests that the clarification functions in the validator module work correctly
with the validation functions to provide a complete clarification flow.

Requirements: 3.2, 3.3, 3.5, 9.1, 9.2, 9.3, 9.4
"""
import pytest
from app.services.ai_assistant_validator import (
    validate_parameters,
    identify_missing_fields,
    prioritize_clarifications,
    generate_clarification_question,
    generate_validation_error_message,
    ValidationError,
)


def test_add_operation_complete_clarification_flow():
    """Test complete clarification flow for add operation from empty to complete."""
    
    # Step 1: User says "Add a class"
    intent = "add"
    params = {}
    context = {}
    
    # Validate - should fail with missing fields
    is_valid, missing, error = validate_parameters(intent, params, context)
    assert not is_valid
    assert len(missing) > 0
    assert error is None  # No validation error, just missing fields
    
    # Step 2: Identify what's missing and ask for first field
    missing_fields = identify_missing_fields(intent, params, context)
    assert len(missing_fields) == 5  # department_id, semester, day, time, subject
    
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "department_id"
    
    question = generate_clarification_question(next_field, intent, context)
    assert "department" in question.lower()
    
    # Step 3: User provides department
    context["department_id"] = "123e4567-e89b-12d3-a456-426614174000"
    
    missing_fields = identify_missing_fields(intent, params, context)
    assert "department_id" not in missing_fields
    
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "semester"
    
    question = generate_clarification_question(next_field, intent, context)
    assert "semester" in question.lower()
    
    # Step 4: User provides semester
    context["semester"] = 5
    
    missing_fields = identify_missing_fields(intent, params, context)
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "day_of_week"
    
    question = generate_clarification_question(next_field, intent, context)
    assert "day" in question.lower()
    
    # Step 5: User provides day
    params["day_of_week"] = "Monday"
    
    missing_fields = identify_missing_fields(intent, params, context)
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "start_time"
    
    question = generate_clarification_question(next_field, intent, context)
    assert "time" in question.lower()
    assert "start" in question.lower()
    
    # Step 6: User provides time
    params["start_time"] = "09:00"
    params["end_time"] = "10:00"
    
    missing_fields = identify_missing_fields(intent, params, context)
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "subject"
    
    question = generate_clarification_question(next_field, intent, context)
    assert "subject" in question.lower()
    
    # Step 7: User provides subject
    params["subject"] = "Mathematics"
    
    missing_fields = identify_missing_fields(intent, params, context)
    assert len(missing_fields) == 0
    
    # Step 8: Validate - should now pass
    is_valid, missing, error = validate_parameters(intent, params, context)
    assert is_valid
    assert len(missing) == 0
    assert error is None


def test_validation_error_generates_helpful_message():
    """Test that validation errors generate user-friendly messages."""
    
    intent = "add"
    params = {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 5,
        "day_of_week": "Mondai",  # Typo
        "start_time": "09:00",
        "end_time": "10:00",
        "subject": "Mathematics",
    }
    context = {}
    
    # Validate - should fail with invalid day
    is_valid, missing, error = validate_parameters(intent, params, context)
    assert not is_valid
    assert len(missing) == 0  # All fields present
    assert error is not None  # Validation error
    
    # The error should mention the invalid day
    assert "Mondai" in error
    assert "Monday" in error  # Should suggest correct days
    
    # We can also generate the same error with our utility
    generated_error = generate_validation_error_message("day_of_week", "invalid_day", "Mondai")
    assert "Mondai" in generated_error
    assert "Monday" in generated_error


def test_time_ordering_validation_error():
    """Test validation error for start_time >= end_time."""
    
    intent = "add"
    params = {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 5,
        "day_of_week": "Monday",
        "start_time": "10:00",
        "end_time": "09:00",  # End before start!
        "subject": "Mathematics",
    }
    context = {}
    
    # Validate - should fail with time ordering error
    is_valid, missing, error = validate_parameters(intent, params, context)
    assert not is_valid
    assert error is not None
    assert "Start time" in error
    assert "before" in error
    
    # Generate the same error with utility
    generated_error = generate_validation_error_message("start_time", "time_order")
    assert "Start time" in generated_error
    assert "before" in generated_error


def test_semester_out_of_range_error():
    """Test validation error for semester outside 1-8 range."""
    
    intent = "add"
    params = {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 9,  # Out of range
        "day_of_week": "Monday",
        "start_time": "09:00",
        "end_time": "10:00",
        "subject": "Mathematics",
    }
    context = {}
    
    # Validate - should fail with semester range error
    is_valid, missing, error = validate_parameters(intent, params, context)
    assert not is_valid
    assert error is not None
    assert "Semester" in error
    assert "1" in error
    assert "8" in error
    
    # Generate the same error with utility - this one includes the value
    generated_error = generate_validation_error_message("semester", "semester_range", 9)
    assert "9" in generated_error
    assert "1" in generated_error
    assert "8" in generated_error


def test_clarification_with_partial_context():
    """Test clarification when some info is in context, some in params."""
    
    intent = "add"
    params = {
        "subject": "Physics",
        "day_of_week": "Tuesday",
    }
    context = {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 3,
    }
    
    # Should only need time info
    missing_fields = identify_missing_fields(intent, params, context)
    assert "department_id" not in missing_fields
    assert "semester" not in missing_fields
    assert "subject" not in missing_fields
    assert "day_of_week" not in missing_fields
    assert "start_time" in missing_fields
    
    # Next question should be about time
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "start_time"
    
    # Question should be context-aware
    question = generate_clarification_question(next_field, intent, {
        "subject": "Physics",
        "day_of_week": "Tuesday",
    })
    assert "Physics" in question
    assert "Tuesday" in question


def test_update_operation_clarification():
    """Test clarification flow for update operation."""
    
    intent = "update"
    params = {
        "subject": "Mathematics",
    }
    context = {
        "semester": 5,
    }
    
    # Update needs identifier fields: day, time, subject
    missing_fields = identify_missing_fields(intent, params, context)
    assert "semester" not in missing_fields
    assert "subject" not in missing_fields
    assert "day_of_week" in missing_fields
    assert "start_time" in missing_fields
    
    # Should ask for day first
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "day_of_week"
    
    question = generate_clarification_question(next_field, intent, context)
    assert "day" in question.lower()
    assert "update" in question.lower()


def test_delete_operation_clarification():
    """Test clarification flow for delete operation."""
    
    intent = "delete"
    params = {}
    context = {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 6,
    }
    
    # Delete needs: day, subject (time optional but helpful)
    missing_fields = identify_missing_fields(intent, params, context)
    assert "semester" not in missing_fields
    assert "day_of_week" in missing_fields
    assert "subject" in missing_fields
    
    # Should ask for day first
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "day_of_week"
    
    question = generate_clarification_question(next_field, intent, context)
    assert "day" in question.lower()
    assert "delete" in question.lower()


def test_replace_operation_minimal_fields():
    """Test that replace operation has minimal required fields."""
    
    intent = "replace"
    params = {}
    context = {}
    
    # Replace only needs department and semester
    missing_fields = identify_missing_fields(intent, params, context)
    assert "department_id" in missing_fields
    assert "semester" in missing_fields
    assert "day_of_week" not in missing_fields
    assert "subject" not in missing_fields
    
    # Should ask for department first
    next_field = prioritize_clarifications(missing_fields, intent)
    assert next_field == "department_id"


def test_query_operation_no_required_fields():
    """Test that query operation has no required fields."""
    
    intent = "query"
    params = {}
    context = {}
    
    # Query has no required fields
    missing_fields = identify_missing_fields(intent, params, context)
    assert len(missing_fields) == 0
    
    # Should validate successfully even with no params
    is_valid, missing, error = validate_parameters(intent, params, context)
    assert is_valid
    assert len(missing) == 0
    assert error is None
