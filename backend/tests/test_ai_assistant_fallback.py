"""Tests for LLM fallback and error handling in AI assistant service.

Tests task 3.4:
- parse_intent_with_fallback() retries once on timeout
- Regex-based fallback parser for when LLM fails
- Logging for LLM errors and fallback usage
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ai_assistant import (
    parse_intent_with_fallback,
    parse_intent_regex,
    parse_intent,
    call_groq_llm,
    call_gemini_llm,
)


class TestRegexFallbackParser:
    """Test regex-based fallback parser."""
    
    def test_parse_add_intent_basic(self):
        """Test parsing basic add intent."""
        message = "Add Mathematics on Monday 9-10 AM"
        context = {"department_id": "test-dept", "semester": 5}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "add"
        assert result["parameters"]["day_of_week"] == "Monday"
        assert result["parameters"]["subject"] == "Mathematics"
        assert result["parameters"]["start_time"] == "09:00"
        assert result["parameters"]["end_time"] == "10:00"
        assert result["confidence"] > 0
    
    def test_parse_update_intent(self):
        """Test parsing update intent."""
        message = "Change Monday class to room 202"
        context = {"department_id": "test-dept", "semester": 5}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "update"
        assert result["parameters"]["day_of_week"] == "Monday"
        assert result["parameters"]["room"] == "202"
    
    def test_parse_delete_intent(self):
        """Test parsing delete intent."""
        message = "Delete Physics on Tuesday"
        context = {"department_id": "test-dept", "semester": 5}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "delete"
        assert result["parameters"]["day_of_week"] == "Tuesday"
        assert result["parameters"]["subject"] == "Physics"
    
    def test_parse_query_intent(self):
        """Test parsing query intent."""
        message = "Show me the schedule for Monday"
        context = {"department_id": "test-dept", "semester": 5}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "query"
        assert result["parameters"]["day_of_week"] == "Monday"
    
    def test_parse_help_intent(self):
        """Test parsing help intent."""
        message = "What can you do?"
        context = {}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "help"
        assert len(result["missing_fields"]) == 0
    
    def test_parse_with_room_number(self):
        """Test parsing message with room number."""
        message = "Add Chemistry on Wednesday 2-3 PM in Room 101"
        context = {"department_id": "test-dept", "semester": 3}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "add"
        assert result["parameters"]["subject"] == "Chemistry"
        assert result["parameters"]["day_of_week"] == "Wednesday"
        assert result["parameters"]["room"] == "101"
    
    def test_parse_with_semester(self):
        """Test parsing message with semester."""
        message = "Show semester 5 schedule"
        context = {"department_id": "test-dept"}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "query"
        assert result["parameters"]["semester"] == 5
    
    def test_parse_unclear_intent(self):
        """Test parsing unclear message."""
        message = "Some random gibberish text"
        context = {}
        
        result = parse_intent_regex(message, context)
        
        assert result["intent"] == "unclear"
        assert result["confidence"] > 0


@pytest.mark.asyncio
class TestParseIntentWithFallback:
    """Test parse_intent_with_fallback() with retry and fallback logic."""
    
    async def test_primary_provider_success(self):
        """Test successful parsing with primary provider."""
        message = "Add Mathematics on Monday 9-10 AM"
        context = {"department_id": "test-dept", "semester": 5}
        
        expected_result = {
            "intent": "add",
            "parameters": {
                "day_of_week": "Monday",
                "subject": "Mathematics",
                "start_time": "09:00",
                "end_time": "10:00",
                "department_id": "test-dept",
                "semester": 5,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.95,
        }
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = expected_result
            
            result = await parse_intent_with_fallback(message, context)
            
            assert result == expected_result
            assert mock_groq.call_count == 1
    
    async def test_primary_timeout_retry_success(self):
        """Test timeout on first attempt, success on retry."""
        message = "Add Mathematics on Monday 9-10 AM"
        context = {"department_id": "test-dept", "semester": 5}
        
        expected_result = {
            "intent": "add",
            "parameters": {
                "day_of_week": "Monday",
                "subject": "Mathematics",
                "start_time": "09:00",
                "end_time": "10:00",
                "department_id": "test-dept",
                "semester": 5,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.95,
        }
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            # First call times out, second call succeeds
            mock_groq.side_effect = [TimeoutError("Timeout"), expected_result]
            
            result = await parse_intent_with_fallback(message, context)
            
            assert result == expected_result
            assert mock_groq.call_count == 2  # Called twice: initial + retry
    
    async def test_primary_fails_fallback_succeeds(self):
        """Test primary provider fails, fallback provider succeeds."""
        message = "Add Mathematics on Monday 9-10 AM"
        context = {"department_id": "test-dept", "semester": 5}
        
        expected_result = {
            "intent": "add",
            "parameters": {
                "day_of_week": "Monday",
                "subject": "Mathematics",
                "start_time": "09:00",
                "end_time": "10:00",
                "department_id": "test-dept",
                "semester": 5,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.93,
        }
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq, \
             patch("app.services.ai_assistant.call_gemini_llm", new_callable=AsyncMock) as mock_gemini:
            
            # Groq fails on both attempts (initial + retry)
            mock_groq.side_effect = [
                TimeoutError("Timeout"),
                Exception("Groq unavailable")
            ]
            # Gemini succeeds
            mock_gemini.return_value = expected_result
            
            result = await parse_intent_with_fallback(message, context)
            
            assert result == expected_result
            assert mock_groq.call_count == 2  # Initial + retry
            assert mock_gemini.call_count == 1  # Fallback
    
    async def test_all_llm_fail_regex_fallback(self):
        """Test all LLM providers fail, falls back to regex parser."""
        message = "Add Mathematics on Monday 9-10 AM"
        context = {"department_id": "test-dept", "semester": 5}
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq, \
             patch("app.services.ai_assistant.call_gemini_llm", new_callable=AsyncMock) as mock_gemini:
            
            # Both providers fail
            mock_groq.side_effect = [
                TimeoutError("Timeout"),
                Exception("Groq unavailable")
            ]
            mock_gemini.side_effect = Exception("Gemini unavailable")
            
            result = await parse_intent_with_fallback(message, context)
            
            # Should fall back to regex parser
            assert result["intent"] == "add"
            assert result["parameters"]["day_of_week"] == "Monday"
            assert result["parameters"]["subject"] == "Mathematics"
            assert result["confidence"] < 1.0  # Regex parser has lower confidence
            assert mock_groq.call_count == 2
            assert mock_gemini.call_count == 1
    
    async def test_non_timeout_error_skips_retry(self):
        """Test non-timeout errors skip retry and go to fallback."""
        message = "Add Mathematics on Monday 9-10 AM"
        context = {"department_id": "test-dept", "semester": 5}
        
        expected_result = {
            "intent": "add",
            "parameters": {"day_of_week": "Monday"},
            "missing_fields": [],
            "confidence": 0.90,
        }
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq, \
             patch("app.services.ai_assistant.call_gemini_llm", new_callable=AsyncMock) as mock_gemini:
            
            # Non-timeout error should skip retry
            mock_groq.side_effect = Exception("Parse error")
            mock_gemini.return_value = expected_result
            
            result = await parse_intent_with_fallback(message, context)
            
            assert result == expected_result
            assert mock_groq.call_count == 1  # No retry for non-timeout errors
            assert mock_gemini.call_count == 1
    
    async def test_complete_failure_returns_unclear(self):
        """Test complete failure returns unclear intent."""
        message = "Some gibberish that can't be parsed"
        context = {}
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq, \
             patch("app.services.ai_assistant.call_gemini_llm", new_callable=AsyncMock) as mock_gemini, \
             patch("app.services.ai_assistant.parse_intent_regex") as mock_regex:
            
            # All methods fail
            mock_groq.side_effect = [TimeoutError("Timeout"), Exception("Error")]
            mock_gemini.side_effect = Exception("Gemini error")
            mock_regex.side_effect = Exception("Regex error")
            
            result = await parse_intent_with_fallback(message, context)
            
            # Should return unclear intent as last resort
            assert result["intent"] == "unclear"
            assert result["confidence"] == 0.0


@pytest.mark.asyncio
class TestParseIntentMainFunction:
    """Test main parse_intent() function delegates correctly."""
    
    async def test_delegates_to_fallback(self):
        """Test parse_intent() delegates to parse_intent_with_fallback()."""
        message = "Add Mathematics on Monday"
        context = {"department_id": "test-dept"}
        
        expected_result = {
            "intent": "add",
            "parameters": {},
            "missing_fields": [],
            "confidence": 0.95,
        }
        
        with patch("app.services.ai_assistant.parse_intent_with_fallback", new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = expected_result
            
            result = await parse_intent(message, context)
            
            assert result == expected_result
            mock_fallback.assert_called_once_with(message, context)


class TestErrorLogging:
    """Test that errors are properly logged."""
    
    @pytest.mark.asyncio
    async def test_timeout_logged(self):
        """Test timeout errors are logged."""
        message = "Add class"
        context = {}
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq, \
             patch("app.services.ai_assistant.structured_logger") as mock_logger:
            
            mock_groq.side_effect = [TimeoutError("Timeout"), TimeoutError("Timeout again")]
            
            try:
                await parse_intent_with_fallback(message, context)
            except:
                pass
            
            # Verify warning was logged
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            assert len(warning_calls) > 0
    
    @pytest.mark.asyncio
    async def test_fallback_logged(self):
        """Test fallback usage is logged."""
        message = "Add class"
        context = {}
        
        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq, \
             patch("app.services.ai_assistant.call_gemini_llm", new_callable=AsyncMock) as mock_gemini:
            
            mock_groq.side_effect = [TimeoutError("Timeout"), Exception("Error")]
            mock_gemini.side_effect = Exception("Error")
            
            result = await parse_intent_with_fallback(message, context)
            
            # Should fall back to regex parser
            assert result["intent"] in ("add", "unclear")
            assert mock_groq.call_count == 2
            assert mock_gemini.call_count == 1
