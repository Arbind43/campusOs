"""Unit tests for AI Assistant LLM service."""
import json
import pytest
from datetime import time
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_assistant import (
    call_groq_llm,
    call_gemini_llm,
    parse_intent,
    parse_time_string,
    normalize_day_name,
    validate_intent_parameters,
    generate_response,
    generate_clarification,
    generate_help_message,
    LLM_SYSTEM_PROMPT,
)


class TestParseTimeString:
    """Test parse_time_string utility function."""

    def test_parse_hh_mm_format(self):
        """Test parsing HH:MM format."""
        result = parse_time_string("09:30")
        assert result == time(9, 30)

    def test_parse_h_mm_format(self):
        """Test parsing H:MM format."""
        result = parse_time_string("9:30")
        assert result == time(9, 30)

    def test_parse_hhmm_format(self):
        """Test parsing HHMM format."""
        result = parse_time_string("0930")
        assert result == time(9, 30)

    def test_parse_hour_only(self):
        """Test parsing hour only (assumes :00 minutes)."""
        result = parse_time_string("9")
        assert result == time(9, 0)

    def test_parse_invalid_time(self):
        """Test that invalid time returns None."""
        result = parse_time_string("invalid")
        assert result is None

    def test_parse_empty_string(self):
        """Test that empty string returns None."""
        result = parse_time_string("")
        assert result is None


class TestNormalizeDayName:
    """Test normalize_day_name utility function."""

    def test_normalize_full_name(self):
        """Test normalizing full day name."""
        assert normalize_day_name("monday") == "Monday"
        assert normalize_day_name("MONDAY") == "Monday"
        assert normalize_day_name("Monday") == "Monday"

    def test_normalize_abbreviation(self):
        """Test normalizing day abbreviations."""
        assert normalize_day_name("mon") == "Monday"
        assert normalize_day_name("Mon") == "Monday"
        assert normalize_day_name("MON") == "Monday"

    def test_normalize_tuesday(self):
        """Test Tuesday variations."""
        assert normalize_day_name("tuesday") == "Tuesday"
        assert normalize_day_name("tue") == "Tuesday"
        assert normalize_day_name("tues") == "Tuesday"

    def test_normalize_wednesday(self):
        """Test Wednesday variations."""
        assert normalize_day_name("wednesday") == "Wednesday"
        assert normalize_day_name("wed") == "Wednesday"

    def test_normalize_thursday(self):
        """Test Thursday variations."""
        assert normalize_day_name("thursday") == "Thursday"
        assert normalize_day_name("thu") == "Thursday"
        assert normalize_day_name("thur") == "Thursday"
        assert normalize_day_name("thurs") == "Thursday"

    def test_normalize_friday(self):
        """Test Friday variations."""
        assert normalize_day_name("friday") == "Friday"
        assert normalize_day_name("fri") == "Friday"

    def test_normalize_saturday(self):
        """Test Saturday variations."""
        assert normalize_day_name("saturday") == "Saturday"
        assert normalize_day_name("sat") == "Saturday"

    def test_normalize_sunday(self):
        """Test Sunday variations."""
        assert normalize_day_name("sunday") == "Sunday"
        assert normalize_day_name("sun") == "Sunday"

    def test_normalize_invalid_day(self):
        """Test that invalid day returns None."""
        assert normalize_day_name("invalid") is None
        assert normalize_day_name("") is None


class TestValidateIntentParameters:
    """Test validate_intent_parameters function."""

    def test_validate_add_intent_complete(self):
        """Test validation for complete add intent."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "semester": 5,
            "department_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        is_valid, missing, error = validate_intent_parameters("add", parameters, {})
        assert is_valid is True
        assert missing == []
        assert error is None

    def test_validate_add_intent_missing_day(self):
        """Test validation for add intent missing day."""
        parameters = {
            "start_time": "09:00",
            "subject": "Mathematics",
            "semester": 5,
            "department_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        is_valid, missing, error = validate_intent_parameters("add", parameters, {})
        assert is_valid is False
        assert "day_of_week" in missing
        assert error is None  # No field validation error, just missing field

    def test_validate_add_intent_with_context(self):
        """Test validation uses context to fill missing parameters."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        context = {
            "semester": 5,
            "department_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        is_valid, missing, error = validate_intent_parameters("add", parameters, context)
        assert is_valid is True
        assert missing == []
        assert error is None

    def test_validate_update_intent_complete(self):
        """Test validation for complete update intent."""
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "subject": "Mathematics",
            "semester": 5,
        }
        is_valid, missing, error = validate_intent_parameters("update", parameters, {})
        assert is_valid is True
        assert missing == []
        assert error is None

    def test_validate_delete_intent_complete(self):
        """Test validation for complete delete intent."""
        parameters = {
            "day_of_week": "Monday",
            "subject": "Mathematics",
            "semester": 5,
        }
        is_valid, missing, error = validate_intent_parameters("delete", parameters, {})
        assert is_valid is True
        assert missing == []
        assert error is None

    def test_validate_replace_intent_complete(self):
        """Test validation for complete replace intent."""
        parameters = {
            "semester": 5,
            "department_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        is_valid, missing, error = validate_intent_parameters("replace", parameters, {})
        assert is_valid is True
        assert missing == []
        assert error is None

    def test_validate_query_intent_no_requirements(self):
        """Test validation for query intent (no required fields)."""
        is_valid, missing, error = validate_intent_parameters("query", {}, {})
        assert is_valid is True
        assert missing == []
        assert error is None

    def test_validate_help_intent_no_requirements(self):
        """Test validation for help intent (no required fields)."""
        is_valid, missing, error = validate_intent_parameters("help", {}, {})
        assert is_valid is True
        assert missing == []
        assert error is None


class TestFieldValidation:
    """Test field-specific validation rules (Task 5.2)."""

    def test_validate_invalid_day_name(self):
        """Test validation rejects invalid day names."""
        from app.services.ai_assistant import validate_field_values
        
        parameters = {
            "day_of_week": "InvalidDay",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "semester": 5,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Invalid day name" in error
        assert "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday" in error

    def test_validate_valid_day_names(self):
        """Test validation accepts all valid day names."""
        from app.services.ai_assistant import validate_field_values
        
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in valid_days:
            parameters = {
                "day_of_week": day,
                "start_time": "09:00",
                "end_time": "10:00",
                "subject": "Mathematics",
                "semester": 5,
            }
            is_valid, error = validate_field_values(parameters)
            assert is_valid is True, f"Day {day} should be valid"
            assert error is None

    def test_validate_start_time_after_end_time(self):
        """Test validation rejects start_time >= end_time."""
        from app.services.ai_assistant import validate_field_values
        
        # Test start_time > end_time
        parameters = {
            "day_of_week": "Monday",
            "start_time": "15:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "semester": 5,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Start time must be before end time" in error

        # Test start_time == end_time
        parameters["start_time"] = "10:00"
        parameters["end_time"] = "10:00"
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Start time must be before end time" in error

    def test_validate_valid_time_order(self):
        """Test validation accepts start_time < end_time."""
        from app.services.ai_assistant import validate_field_values
        
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "semester": 5,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is True
        assert error is None

    def test_validate_semester_out_of_range(self):
        """Test validation rejects semester outside 1-8 range."""
        from app.services.ai_assistant import validate_field_values
        
        # Test semester < 1
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "semester": 0,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Semester must be between 1 and 8" in error

        # Test semester > 8
        parameters["semester"] = 9
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Semester must be between 1 and 8" in error

    def test_validate_valid_semester_range(self):
        """Test validation accepts semester 1-8."""
        from app.services.ai_assistant import validate_field_values
        
        for semester in range(1, 9):
            parameters = {
                "day_of_week": "Monday",
                "start_time": "09:00",
                "end_time": "10:00",
                "subject": "Mathematics",
                "semester": semester,
            }
            is_valid, error = validate_field_values(parameters)
            assert is_valid is True, f"Semester {semester} should be valid"
            assert error is None

    def test_validate_subject_length_too_long(self):
        """Test validation rejects subject longer than 100 characters."""
        from app.services.ai_assistant import validate_field_values
        
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "A" * 101,  # 101 characters
            "semester": 5,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Subject name must be 100 characters or less" in error

    def test_validate_subject_length_empty(self):
        """Test validation rejects empty subject."""
        from app.services.ai_assistant import validate_field_values
        
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "",
            "semester": 5,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Subject name is required" in error

    def test_validate_subject_valid_length(self):
        """Test validation accepts subject 1-100 characters."""
        from app.services.ai_assistant import validate_field_values
        
        # Test 1 character
        parameters = {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "M",
            "semester": 5,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is True
        assert error is None

        # Test 100 characters
        parameters["subject"] = "A" * 100
        is_valid, error = validate_field_values(parameters)
        assert is_valid is True
        assert error is None

    def test_validate_time_format_invalid(self):
        """Test validation rejects invalid HH:MM format."""
        from app.services.ai_assistant import validate_field_values
        
        # Test invalid start_time format
        parameters = {
            "day_of_week": "Monday",
            "start_time": "9:00",  # Should be 09:00
            "end_time": "10:00",
            "subject": "Mathematics",
            "semester": 5,
        }
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Invalid start time format" in error
        assert "HH:MM" in error

        # Test invalid end_time format
        parameters["start_time"] = "09:00"
        parameters["end_time"] = "25:00"  # Hour out of range
        is_valid, error = validate_field_values(parameters)
        assert is_valid is False
        assert "Invalid end time format" in error

    def test_validate_time_format_valid(self):
        """Test validation accepts valid HH:MM format."""
        from app.services.ai_assistant import validate_field_values
        
        valid_times = [
            ("00:00", "01:00"),
            ("09:00", "10:00"),
            ("23:00", "23:59"),
        ]
        for start, end in valid_times:
            parameters = {
                "day_of_week": "Monday",
                "start_time": start,
                "end_time": end,
                "subject": "Mathematics",
                "semester": 5,
            }
            is_valid, error = validate_field_values(parameters)
            assert is_valid is True, f"Times {start}-{end} should be valid"
            assert error is None

    def test_validate_integration_with_intent_parameters(self):
        """Test field validation is called by validate_intent_parameters."""
        # Test with invalid day
        parameters = {
            "day_of_week": "BadDay",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "semester": 5,
            "department_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        is_valid, missing, error = validate_intent_parameters("add", parameters, {})
        assert is_valid is False
        assert missing == []  # All required fields present
        assert error is not None  # But field validation failed
        assert "Invalid day name" in error

        # Test with invalid time order
        parameters["day_of_week"] = "Monday"
        parameters["start_time"] = "15:00"
        parameters["end_time"] = "10:00"
        is_valid, missing, error = validate_intent_parameters("add", parameters, {})
        assert is_valid is False
        assert missing == []
        assert error is not None
        assert "Start time must be before end time" in error


class TestCallGroqLLM:
    """Test call_groq_llm function."""

    @pytest.mark.asyncio
    async def test_groq_llm_success(self):
        """Test successful Groq LLM call."""
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "intent": "add",
                            "parameters": {
                                "day_of_week": "Monday",
                                "start_time": "09:00",
                                "end_time": "10:00",
                                "subject": "Mathematics",
                            },
                            "missing_fields": [],
                            "confidence": 0.95,
                        })
                    }
                }
            ]
        }

        with patch("app.services.ai_assistant.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"
            
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = MagicMock(
                    status_code=200,
                    json=lambda: mock_response,
                )
                mock_post.return_value.raise_for_status = MagicMock()

                result = await call_groq_llm("Add Math on Monday 9-10", {})

                assert result["intent"] == "add"
                assert result["parameters"]["subject"] == "Mathematics"
                assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_groq_llm_no_api_key(self):
        """Test Groq LLM call fails when API key is not configured."""
        with patch("app.services.ai_assistant.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = ""

            with pytest.raises(Exception) as exc_info:
                await call_groq_llm("Test message", {})

            assert "GROQ_API_KEY not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_groq_llm_timeout(self):
        """Test Groq LLM call timeout handling."""
        import httpx

        with patch("app.services.ai_assistant.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = httpx.TimeoutException("Timeout")

                with pytest.raises(TimeoutError) as exc_info:
                    await call_groq_llm("Test message", {}, timeout=5)

                assert "exceeded 5 seconds" in str(exc_info.value)


class TestCallGeminiLLM:
    """Test call_gemini_llm function."""

    @pytest.mark.asyncio
    async def test_gemini_llm_no_api_key(self):
        """Test Gemini LLM call fails when API key is not configured."""
        with patch("app.services.ai_assistant.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""

            with pytest.raises(Exception) as exc_info:
                await call_gemini_llm("Test message", {})

            assert "GEMINI_API_KEY not configured" in str(exc_info.value)


class TestParseIntent:
    """Test parse_intent function with fallback logic."""

    @pytest.mark.asyncio
    async def test_parse_intent_uses_groq_by_default(self):
        """Test that parse_intent uses Groq as primary provider."""
        mock_response = {
            "intent": "add",
            "parameters": {"subject": "Mathematics"},
            "missing_fields": [],
            "confidence": 0.95,
        }

        with patch("app.services.ai_assistant.settings") as mock_settings:
            mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
            mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

            with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
                mock_groq.return_value = mock_response

                result = await parse_intent("Add Math", {})

                assert result["intent"] == "add"
                mock_groq.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_intent_fallback_to_gemini(self):
        """Test that parse_intent falls back to Gemini when Groq fails."""
        mock_response = {
            "intent": "add",
            "parameters": {"subject": "Mathematics"},
            "missing_fields": [],
            "confidence": 0.95,
        }

        with patch("app.services.ai_assistant.settings") as mock_settings:
            mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
            mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

            with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
                mock_groq.side_effect = Exception("Groq failed")

                with patch("app.services.ai_assistant.call_gemini_llm", new_callable=AsyncMock) as mock_gemini:
                    mock_gemini.return_value = mock_response

                    result = await parse_intent("Add Math", {})

                    assert result["intent"] == "add"
                    mock_groq.assert_called_once()
                    mock_gemini.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_intent_both_providers_fail(self):
        """Test that parse_intent falls back to regex parser when both providers fail."""
        with patch("app.services.ai_assistant.settings") as mock_settings:
            mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
            mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

            with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
                mock_groq.side_effect = Exception("Groq failed")

                with patch("app.services.ai_assistant.call_gemini_llm", new_callable=AsyncMock) as mock_gemini:
                    mock_gemini.side_effect = Exception("Gemini failed")

                    # Should not raise exception - should fall back to regex parser
                    result = await parse_intent("Add Math", {})

                    # Verify both providers were called
                    mock_groq.assert_called_once()
                    mock_gemini.assert_called_once()
                    
                    # Verify result is returned (from regex fallback)
                    assert "intent" in result
                    assert result["intent"] in ["add", "update", "delete", "replace", "query", "help", "unclear"]


class TestLLMSystemPrompt:
    """Test that LLM system prompt is properly defined."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert LLM_SYSTEM_PROMPT is not None
        assert len(LLM_SYSTEM_PROMPT) > 0

    def test_system_prompt_contains_key_instructions(self):
        """Test that system prompt contains essential instructions."""
        assert "intent" in LLM_SYSTEM_PROMPT.lower()
        assert "json" in LLM_SYSTEM_PROMPT.lower()
        assert "day_of_week" in LLM_SYSTEM_PROMPT
        assert "start_time" in LLM_SYSTEM_PROMPT
        assert "end_time" in LLM_SYSTEM_PROMPT
        assert "subject" in LLM_SYSTEM_PROMPT
        assert "semester" in LLM_SYSTEM_PROMPT

    def test_system_prompt_includes_intents(self):
        """Test that system prompt includes all intent types."""
        assert "add" in LLM_SYSTEM_PROMPT
        assert "update" in LLM_SYSTEM_PROMPT
        assert "delete" in LLM_SYSTEM_PROMPT
        assert "replace" in LLM_SYSTEM_PROMPT
        assert "query" in LLM_SYSTEM_PROMPT
        assert "help" in LLM_SYSTEM_PROMPT


class TestGenerateResponse:
    """Test generate_response function (Task 3.5)."""

    def test_generate_response_add_success_full_details(self):
        """Test response generation for successful add with all details."""
        result = {
            "operation_type": "add",
            "success": True,
            "affected_entries_count": 1,
            "entries": [
                {
                    "subject": "Mathematics",
                    "day_of_week": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "room": "Room 101",
                    "faculty_name": "Dr. Smith",
                }
            ],
        }
        response = generate_response(result, {})
        
        assert "✓" in response
        assert "Mathematics" in response
        assert "Monday" in response
        assert "09:00" in response
        assert "10:00" in response
        assert "Room 101" in response
        assert "Dr. Smith" in response

    def test_generate_response_add_success_minimal_details(self):
        """Test response generation for successful add with minimal details."""
        result = {
            "operation_type": "add",
            "success": True,
            "affected_entries_count": 1,
            "entries": [
                {
                    "subject": "Physics",
                    "day_of_week": "Tuesday",
                    "start_time": "14:00",
                    "end_time": "15:00",
                }
            ],
        }
        response = generate_response(result, {})
        
        assert "✓" in response
        assert "Physics" in response
        assert "Tuesday" in response
        assert "14:00" in response

    def test_generate_response_add_success_with_time_objects(self):
        """Test response generation with time objects instead of strings."""
        from datetime import time as time_obj
        
        result = {
            "operation_type": "add",
            "success": True,
            "affected_entries_count": 1,
            "entries": [
                {
                    "subject": "Chemistry",
                    "day_of_week": "Wednesday",
                    "start_time": time_obj(9, 0),
                    "end_time": time_obj(10, 0),
                }
            ],
        }
        response = generate_response(result, {})
        
        assert "✓" in response
        assert "Chemistry" in response
        assert "09:00" in response
        assert "10:00" in response

    def test_generate_response_update_success(self):
        """Test response generation for successful update."""
        result = {
            "operation_type": "update",
            "success": True,
            "affected_entries_count": 1,
            "entries": [
                {
                    "subject": "Mathematics",
                    "day_of_week": "Monday",
                }
            ],
        }
        response = generate_response(result, {})
        
        assert "✓" in response
        assert "Updated" in response
        assert "Mathematics" in response

    def test_generate_response_delete_success(self):
        """Test response generation for successful delete."""
        result = {
            "operation_type": "delete",
            "success": True,
            "affected_entries_count": 1,
        }
        response = generate_response(result, {})
        
        assert "✓" in response
        assert "Deleted" in response
        assert "1" in response

    def test_generate_response_delete_multiple(self):
        """Test response generation for deleting multiple entries."""
        result = {
            "operation_type": "delete",
            "success": True,
            "affected_entries_count": 3,
        }
        response = generate_response(result, {})
        
        assert "✓" in response
        assert "3" in response
        assert "entries" in response

    def test_generate_response_replace_success(self):
        """Test response generation for successful replace."""
        result = {
            "operation_type": "replace",
            "success": True,
            "affected_entries_count": 15,
        }
        context = {"semester": 5}
        response = generate_response(result, context)
        
        assert "✓" in response
        assert "Replaced" in response
        assert "semester 5" in response
        assert "15" in response

    def test_generate_response_query_success(self):
        """Test response generation for successful query."""
        result = {
            "operation_type": "query",
            "success": True,
            "entries": [
                {
                    "subject": "Mathematics",
                    "day_of_week": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "room": "Room 101",
                    "faculty_name": "Dr. Smith",
                },
                {
                    "subject": "Physics",
                    "day_of_week": "Monday",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "room": "Lab A",
                },
            ],
        }
        context = {"semester": 5}
        response = generate_response(result, context)
        
        assert "schedule" in response.lower()
        assert "Mathematics" in response
        assert "Physics" in response
        assert "09:00" in response
        assert "Found 2 classes" in response

    def test_generate_response_query_no_results(self):
        """Test response generation for query with no results."""
        result = {
            "operation_type": "query",
            "success": True,
            "entries": [],
        }
        response = generate_response(result, {})
        
        assert "No classes found" in response

    def test_generate_response_error(self):
        """Test response generation for operation error."""
        result = {
            "operation_type": "add",
            "success": False,
            "error_message": "Invalid time format",
        }
        response = generate_response(result, {})
        
        assert "❌" in response
        assert "Invalid time format" in response

    def test_generate_response_error_no_message(self):
        """Test response generation for error without specific message."""
        result = {
            "operation_type": "add",
            "success": False,
        }
        response = generate_response(result, {})
        
        assert "❌" in response
        assert "error occurred" in response.lower()


class TestGenerateClarification:
    """Test generate_clarification function (Task 3.5)."""

    def test_generate_clarification_semester(self):
        """Test clarification question for missing semester."""
        missing = ["semester"]
        question = generate_clarification(missing, {}, "add")
        
        assert "semester" in question.lower()
        assert "1 and 8" in question or "between" in question.lower()

    def test_generate_clarification_day_for_add(self):
        """Test clarification question for missing day in add intent."""
        missing = ["day_of_week"]
        question = generate_clarification(missing, {}, "add")
        
        assert "day" in question.lower()
        assert "class" in question.lower() or "scheduled" in question.lower()

    def test_generate_clarification_day_for_update(self):
        """Test clarification question for missing day in update intent."""
        missing = ["day_of_week"]
        question = generate_clarification(missing, {}, "update")
        
        assert "day" in question.lower()
        assert "update" in question.lower()

    def test_generate_clarification_day_for_delete(self):
        """Test clarification question for missing day in delete intent."""
        missing = ["day_of_week"]
        question = generate_clarification(missing, {}, "delete")
        
        assert "day" in question.lower()
        assert "delete" in question.lower()

    def test_generate_clarification_start_time_for_add(self):
        """Test clarification question for missing start time in add intent."""
        missing = ["start_time"]
        question = generate_clarification(missing, {}, "add")
        
        assert "time" in question.lower()
        assert "start" in question.lower()
        # Should provide examples
        assert "9 AM" in question or "09:00" in question

    def test_generate_clarification_subject_for_add(self):
        """Test clarification question for missing subject in add intent."""
        missing = ["subject"]
        question = generate_clarification(missing, {}, "add")
        
        assert "subject" in question.lower()
        assert "add" in question.lower()

    def test_generate_clarification_priority_order(self):
        """Test that clarification follows priority order."""
        # When multiple fields are missing, should ask for highest priority first
        missing = ["subject", "semester", "day_of_week"]
        question = generate_clarification(missing, {}, "add")
        
        # Semester has higher priority than day and subject
        assert "semester" in question.lower()

    def test_generate_clarification_department(self):
        """Test clarification question for missing department."""
        missing = ["department_id"]
        question = generate_clarification(missing, {}, "add")
        
        assert "department" in question.lower()

    def test_generate_clarification_end_time(self):
        """Test clarification question for missing end time."""
        missing = ["end_time"]
        question = generate_clarification(missing, {}, "add")
        
        assert "end" in question.lower() or "time" in question.lower()

    def test_generate_clarification_room_optional(self):
        """Test clarification question for optional room field."""
        missing = ["room"]
        question = generate_clarification(missing, {}, "add")
        
        assert "room" in question.lower()
        assert "optional" in question.lower() or "skip" in question.lower()

    def test_generate_clarification_faculty_optional(self):
        """Test clarification question for optional faculty field."""
        missing = ["faculty_name"]
        question = generate_clarification(missing, {}, "add")
        
        assert "faculty" in question.lower()
        assert "optional" in question.lower() or "skip" in question.lower()

    def test_generate_clarification_no_missing_fields(self):
        """Test clarification when no fields are missing."""
        missing = []
        question = generate_clarification(missing, {}, "add")
        
        # Should indicate no more info needed
        assert "proceed" in question.lower() or "information" in question.lower()


class TestGenerateHelpMessage:
    """Test generate_help_message function (Task 3.5)."""

    def test_generate_help_message_contains_operations(self):
        """Test that help message contains all operation types."""
        help_msg = generate_help_message()
        
        assert "add" in help_msg.lower()
        assert "update" in help_msg.lower()
        assert "delete" in help_msg.lower()
        assert "replace" in help_msg.lower()
        assert "query" in help_msg.lower() or "view" in help_msg.lower()

    def test_generate_help_message_contains_examples(self):
        """Test that help message contains example phrases."""
        help_msg = generate_help_message()
        
        assert "example" in help_msg.lower()
        # Should have at least one concrete example
        assert "Monday" in help_msg or "Tuesday" in help_msg

    def test_generate_help_message_contains_tips(self):
        """Test that help message contains helpful tips."""
        help_msg = generate_help_message()
        
        assert "tip" in help_msg.lower() or "remember" in help_msg.lower()

    def test_generate_help_message_friendly_tone(self):
        """Test that help message has a friendly, welcoming tone."""
        help_msg = generate_help_message()
        
        # Should have some friendly indicators
        assert "👋" in help_msg or "Hi" in help_msg or "Hello" in help_msg
        assert "help" in help_msg.lower()

    def test_generate_help_message_non_empty(self):
        """Test that help message is not empty."""
        help_msg = generate_help_message()
        
        assert len(help_msg) > 100  # Should be substantial
        assert help_msg.strip() != ""
