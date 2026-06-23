"""Unit tests for AI Assistant parameter validator.

Tests validation logic for all operation types (add, update, delete, replace, query)
and enforces business rules like time ordering, field lengths, and required fields.
"""
import pytest

from app.services.ai_assistant_validator import (
    ParameterValidator,
    ValidationError,
    validate_parameters,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def validator():
    """Create parameter validator instance."""
    return ParameterValidator()


@pytest.fixture
def valid_context():
    """Create valid conversation context."""
    return {
        "department_id": "123e4567-e89b-12d3-a456-426614174000",
        "semester": 5,
    }


# ─── Add Operation Tests ──────────────────────────────────────────────────────

class TestAddParameterValidation:
    """Test cases for add operation parameter validation."""
    
    def test_add_with_all_required_fields(self, validator, valid_context):
        """Test add validation with all required fields present."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_add_with_missing_day(self, validator, valid_context):
        """Test add validation fails when day_of_week is missing."""
        parameters = {
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert "day_of_week" in missing
        assert error is None
    
    def test_add_with_missing_subject(self, validator, valid_context):
        """Test add validation fails when subject is missing."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert "subject" in missing
        assert error is None
    
    def test_add_with_missing_start_time(self, validator, valid_context):
        """Test add validation fails when start_time is missing."""
        parameters = {
            "day_of_week": "Monday",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert "start_time" in missing
        assert error is None
    
    def test_add_with_missing_semester(self, validator):
        """Test add validation fails when semester is missing from both params and context."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "subject": "Mathematics",
        }
        context = {"department_id": "123e4567-e89b-12d3-a456-426614174000"}
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, context)
        
        assert is_valid is False
        assert "semester" in missing
        assert error is None
    
    def test_add_with_invalid_day_name(self, validator, valid_context):
        """Test add validation fails with invalid day name."""
        parameters = {
            "day_of_week": "Funday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Invalid day name" in error
    
    def test_add_with_start_time_after_end_time(self, validator, valid_context):
        """Test add validation fails when start_time is after end_time."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "11:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Start time must be before end time" in error
    
    def test_add_with_invalid_semester_range(self, validator):
        """Test add validation fails with semester outside 1-8 range."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        context = {"department_id": "123e4567-e89b-12d3-a456-426614174000", "semester": 10}
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Semester must be between 1 and 8" in error
    
    def test_add_with_invalid_time_format(self, validator, valid_context):
        """Test add validation fails with invalid time format."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "9 AM",  # Invalid format, should be HH:MM
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Invalid start time format" in error
    
    def test_add_with_subject_too_long(self, validator, valid_context):
        """Test add validation fails when subject exceeds max length."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "A" * 101,  # 101 characters, exceeds max 100
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "too long" in error
    
    def test_add_with_empty_subject(self, validator, valid_context):
        """Test add validation fails when subject is empty."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "   ",  # Empty after strip
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "cannot be empty" in error
    
    def test_add_with_optional_fields(self, validator, valid_context):
        """Test add validation succeeds with optional room and faculty fields."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "room": "Room 301",
            "faculty_name": "Dr. Smith",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_add_without_end_time(self, validator, valid_context):
        """Test add validation succeeds without end_time (can be calculated)."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_add_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None


# ─── Update Operation Tests ───────────────────────────────────────────────────

class TestUpdateParameterValidation:
    """Test cases for update operation parameter validation."""
    
    def test_update_with_all_identifier_fields(self, validator, valid_context):
        """Test update validation with all identifier fields present."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "subject": "Mathematics",
            "room": "Room 301",  # Field to change
        }
        
        is_valid, missing, error = validator.validate_update_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_update_with_missing_identifier(self, validator, valid_context):
        """Test update validation fails when identifier fields are missing."""
        parameters = {
            "day_of_week": "Monday",
            "room": "Room 301",
        }
        
        is_valid, missing, error = validator.validate_update_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert "start_time" in missing
        assert "subject" in missing
        assert error is None
    
    def test_update_with_invalid_day(self, validator, valid_context):
        """Test update validation fails with invalid day name."""
        parameters = {
            "day_of_week": "InvalidDay",
            "start_time": "09:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_update_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Invalid day name" in error
    
    def test_update_with_invalid_end_time(self, validator, valid_context):
        """Test update validation fails when changing end_time to invalid value."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "subject": "Mathematics",
            "end_time": "08:00",  # Before start_time
        }
        
        is_valid, missing, error = validator.validate_update_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Start time must be before end time" in error


# ─── Delete Operation Tests ───────────────────────────────────────────────────

class TestDeleteParameterValidation:
    """Test cases for delete operation parameter validation."""
    
    def test_delete_with_required_fields(self, validator, valid_context):
        """Test delete validation with required identifier fields."""
        parameters = {
            "day_of_week": "Monday",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_delete_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_delete_with_optional_time(self, validator, valid_context):
        """Test delete validation with optional start_time for better identification."""
        parameters = {
            "day_of_week": "Monday",
            "subject": "Mathematics",
            "start_time": "09:00",
        }
        
        is_valid, missing, error = validator.validate_delete_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_delete_with_missing_day(self, validator, valid_context):
        """Test delete validation fails when day_of_week is missing."""
        parameters = {
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_delete_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert "day_of_week" in missing
        assert error is None
    
    def test_delete_with_missing_subject(self, validator, valid_context):
        """Test delete validation fails when subject is missing."""
        parameters = {
            "day_of_week": "Monday",
        }
        
        is_valid, missing, error = validator.validate_delete_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert "subject" in missing
        assert error is None
    
    def test_delete_with_invalid_day(self, validator, valid_context):
        """Test delete validation fails with invalid day name."""
        parameters = {
            "day_of_week": "NotADay",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_delete_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Invalid day name" in error


# ─── Replace Operation Tests ──────────────────────────────────────────────────

class TestReplaceParameterValidation:
    """Test cases for replace operation parameter validation."""
    
    def test_replace_with_required_fields(self, validator, valid_context):
        """Test replace validation with required fields."""
        parameters = {}
        
        is_valid, missing, error = validator.validate_replace_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_replace_with_missing_semester(self, validator):
        """Test replace validation fails when semester is missing."""
        parameters = {}
        context = {"department_id": "123e4567-e89b-12d3-a456-426614174000"}
        
        is_valid, missing, error = validator.validate_replace_parameters(parameters, context)
        
        assert is_valid is False
        assert "semester" in missing
        assert error is None
    
    def test_replace_with_missing_department_id(self, validator):
        """Test replace validation fails when department_id is missing."""
        parameters = {}
        context = {"semester": 5}
        
        is_valid, missing, error = validator.validate_replace_parameters(parameters, context)
        
        assert is_valid is False
        assert "department_id" in missing
        assert error is None
    
    def test_replace_with_valid_entries_list(self, validator, valid_context):
        """Test replace validation with valid entries list."""
        parameters = {
            "entries": [
                {
                    "day_of_week": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "subject": "Mathematics",
                },
                {
                    "day_of_week": "Tuesday",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "subject": "Physics",
                },
            ]
        }
        
        is_valid, missing, error = validator.validate_replace_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_replace_with_invalid_entry(self, validator, valid_context):
        """Test replace validation fails when an entry is invalid."""
        parameters = {
            "entries": [
                {
                    "day_of_week": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "subject": "Mathematics",
                },
                {
                    "day_of_week": "InvalidDay",  # Invalid
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "subject": "Physics",
                },
            ]
        }
        
        is_valid, missing, error = validator.validate_replace_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Entry 2" in error
    
    def test_replace_with_invalid_semester(self, validator):
        """Test replace validation fails with invalid semester."""
        parameters = {}
        context = {
            "department_id": "123e4567-e89b-12d3-a456-426614174000",
            "semester": 0,  # Invalid, must be 1-8
        }
        
        is_valid, missing, error = validator.validate_replace_parameters(parameters, context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Semester must be between 1 and 8" in error


# ─── Query Operation Tests ────────────────────────────────────────────────────

class TestQueryParameterValidation:
    """Test cases for query operation parameter validation."""
    
    def test_query_with_no_filters(self, validator, valid_context):
        """Test query validation succeeds with no filters."""
        parameters = {}
        
        is_valid, missing, error = validator.validate_query_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_query_with_day_filter(self, validator, valid_context):
        """Test query validation with valid day filter."""
        parameters = {
            "day_of_week": "Monday",
        }
        
        is_valid, missing, error = validator.validate_query_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_query_with_invalid_day_filter(self, validator, valid_context):
        """Test query validation fails with invalid day filter."""
        parameters = {
            "day_of_week": "NotADay",
        }
        
        is_valid, missing, error = validator.validate_query_parameters(parameters, valid_context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Invalid day name" in error
    
    def test_query_with_semester_filter(self, validator):
        """Test query validation with valid semester filter."""
        parameters = {
            "semester": 3,
        }
        context = {"department_id": "123e4567-e89b-12d3-a456-426614174000"}
        
        is_valid, missing, error = validator.validate_query_parameters(parameters, context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_query_with_invalid_semester_filter(self, validator):
        """Test query validation fails with invalid semester filter."""
        parameters = {
            "semester": 9,  # Out of range
        }
        context = {"department_id": "123e4567-e89b-12d3-a456-426614174000"}
        
        is_valid, missing, error = validator.validate_query_parameters(parameters, context)
        
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Semester must be between 1 and 8" in error
    
    def test_query_with_subject_filter(self, validator, valid_context):
        """Test query validation with subject filter."""
        parameters = {
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_query_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_query_with_multiple_filters(self, validator, valid_context):
        """Test query validation with multiple filters."""
        parameters = {
            "day_of_week": "Monday",
            "semester": 5,
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validator.validate_query_parameters(parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None


# ─── Convenience Function Tests ───────────────────────────────────────────────

class TestValidateParametersFunction:
    """Test cases for the convenience validate_parameters function."""
    
    def test_validate_add_intent(self, valid_context):
        """Test validate_parameters delegates to add validator."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validate_parameters("add", parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_validate_update_intent(self, valid_context):
        """Test validate_parameters delegates to update validator."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validate_parameters("update", parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_validate_delete_intent(self, valid_context):
        """Test validate_parameters delegates to delete validator."""
        parameters = {
            "day_of_week": "Monday",
            "subject": "Mathematics",
        }
        
        is_valid, missing, error = validate_parameters("delete", parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_validate_replace_intent(self, valid_context):
        """Test validate_parameters delegates to replace validator."""
        parameters = {}
        
        is_valid, missing, error = validate_parameters("replace", parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_validate_query_intent(self, valid_context):
        """Test validate_parameters delegates to query validator."""
        parameters = {"day_of_week": "Monday"}
        
        is_valid, missing, error = validate_parameters("query", parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_validate_help_intent(self, valid_context):
        """Test validate_parameters succeeds for help intent (no validation needed)."""
        parameters = {}
        
        is_valid, missing, error = validate_parameters("help", parameters, valid_context)
        
        assert is_valid is True
        assert missing == []
        assert error is None
    
    def test_validate_unknown_intent(self, valid_context):
        """Test validate_parameters fails for unknown intent."""
        parameters = {}
        
        is_valid, missing, error = validate_parameters("unknown", parameters, valid_context)
        
        assert is_valid is False
        assert error is not None
        assert "Unknown operation intent" in error


# ─── Helper Method Tests ──────────────────────────────────────────────────────

class TestHelperMethods:
    """Test cases for validator helper methods."""
    
    def test_is_valid_time_format_valid(self, validator):
        """Test _is_valid_time_format with valid time strings."""
        assert validator._is_valid_time_format("09:00") is True
        assert validator._is_valid_time_format("14:30") is True
        assert validator._is_valid_time_format("00:00") is True
        assert validator._is_valid_time_format("23:59") is True
    
    def test_is_valid_time_format_invalid(self, validator):
        """Test _is_valid_time_format with invalid time strings."""
        assert validator._is_valid_time_format("9:00") is True  # Single digit hour is valid
        assert validator._is_valid_time_format("25:00") is False  # Invalid hour
        assert validator._is_valid_time_format("12:60") is False  # Invalid minute
        assert validator._is_valid_time_format("9 AM") is False  # Wrong format
        assert validator._is_valid_time_format("") is False  # Empty
        assert validator._is_valid_time_format(None) is False  # None
    
    def test_is_time_before_valid(self, validator):
        """Test _is_time_before with valid time comparisons."""
        assert validator._is_time_before("09:00", "10:00") is True
        assert validator._is_time_before("09:00", "09:30") is True
        assert validator._is_time_before("00:00", "23:59") is True
    
    def test_is_time_before_invalid(self, validator):
        """Test _is_time_before with invalid time comparisons."""
        assert validator._is_time_before("10:00", "09:00") is False
        assert validator._is_time_before("09:30", "09:00") is False
        assert validator._is_time_before("09:00", "09:00") is False  # Equal times
    
    def test_is_time_before_edge_cases(self, validator):
        """Test _is_time_before with edge cases."""
        assert validator._is_time_before("23:59", "00:00") is False  # Wraps to next day
        assert validator._is_time_before("00:00", "00:01") is True
