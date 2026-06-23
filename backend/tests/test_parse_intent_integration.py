"""Integration tests for parse_intent function (Task 3.2).

This test file specifically validates that the parse_intent() function
correctly:
1. Calls LLM with message and context
2. Extracts structured intent
3. Parses parameters
4. Identifies missing required fields

Requirements: 1.1, 1.4, 11.5, 11.6
"""
import json
import pytest
from unittest.mock import AsyncMock, patch

from app.services.ai_assistant import parse_intent


class TestParseIntentIntegration:
    """Integration tests for parse_intent function."""

    @pytest.mark.asyncio
    async def test_parse_intent_add_complete_message(self):
        """Test parsing a complete add intent message.
        
        Validates: Intent extraction, parameter parsing, and missing field detection.
        """
        mock_llm_response = {
            "intent": "add",
            "parameters": {
                "day_of_week": "Monday",
                "start_time": "09:00",
                "end_time": "10:00",
                "subject": "Mathematics",
                "semester": 5,
                "department_id": None,  # Will come from context
                "room": "101",
                "faculty_name": "Dr. Smith",
            },
            "missing_fields": ["department_id"],
            "confidence": 0.95,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                result = await parse_intent(
                    "Add Mathematics on Monday 9-10 AM in room 101 with Dr. Smith",
                    {"semester": 5}
                )

                # Verify intent extracted
                assert result["intent"] == "add"
                
                # Verify parameters parsed
                assert result["parameters"]["subject"] == "Mathematics"
                assert result["parameters"]["day_of_week"] == "Monday"
                assert result["parameters"]["start_time"] == "09:00"
                assert result["parameters"]["end_time"] == "10:00"
                assert result["parameters"]["room"] == "101"
                assert result["parameters"]["faculty_name"] == "Dr. Smith"
                
                # Verify missing fields identified
                assert "department_id" in result["missing_fields"]
                
                # Verify confidence included
                assert result["confidence"] == 0.95

                # Verify LLM was called with message and context
                mock_groq.assert_called_once()
                call_args = mock_groq.call_args
                assert "Add Mathematics" in call_args[0][0]  # message
                assert call_args[0][1]["semester"] == 5  # context

    @pytest.mark.asyncio
    async def test_parse_intent_update_with_context(self):
        """Test parsing update intent with context reuse."""
        mock_llm_response = {
            "intent": "update",
            "parameters": {
                "day_of_week": "Monday",
                "start_time": "09:00",
                "subject": "Mathematics",
                "room": "202",  # Field to update
                "semester": None,  # Will come from context
                "department_id": None,
                "end_time": None,
                "faculty_name": None,
            },
            "missing_fields": [],  # Context provides semester
            "confidence": 0.92,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                context = {
                    "department_id": "123e4567-e89b-12d3-a456-426614174000",
                    "semester": 5,
                }

                result = await parse_intent(
                    "Change Monday 9 AM Mathematics class to room 202",
                    context
                )

                # Verify intent
                assert result["intent"] == "update"
                
                # Verify parameters include identifier fields
                assert result["parameters"]["day_of_week"] == "Monday"
                assert result["parameters"]["start_time"] == "09:00"
                assert result["parameters"]["subject"] == "Mathematics"
                assert result["parameters"]["room"] == "202"
                
                # Verify context was passed to LLM
                mock_groq.assert_called_once()
                call_args = mock_groq.call_args
                assert call_args[0][1]["semester"] == 5
                assert call_args[0][1]["department_id"] == "123e4567-e89b-12d3-a456-426614174000"

    @pytest.mark.asyncio
    async def test_parse_intent_delete_identification(self):
        """Test parsing delete intent with entry identification."""
        mock_llm_response = {
            "intent": "delete",
            "parameters": {
                "day_of_week": "Tuesday",
                "subject": "Physics",
                "semester": 5,
                "department_id": None,
                "start_time": None,
                "end_time": None,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": ["department_id"],
            "confidence": 0.88,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                result = await parse_intent(
                    "Delete Physics class on Tuesday",
                    {"semester": 5}
                )

                # Verify intent
                assert result["intent"] == "delete"
                
                # Verify identifier parameters
                assert result["parameters"]["day_of_week"] == "Tuesday"
                assert result["parameters"]["subject"] == "Physics"
                
                # Verify missing fields for complete identification
                assert "department_id" in result["missing_fields"]

    @pytest.mark.asyncio
    async def test_parse_intent_query_no_requirements(self):
        """Test parsing query intent with no required fields."""
        mock_llm_response = {
            "intent": "query",
            "parameters": {
                "day_of_week": "Monday",
                "semester": 5,
                "department_id": None,
                "subject": None,
                "start_time": None,
                "end_time": None,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.97,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                result = await parse_intent(
                    "Show me Monday's schedule for semester 5",
                    {}
                )

                # Verify intent
                assert result["intent"] == "query"
                
                # Verify optional filter parameters
                assert result["parameters"]["day_of_week"] == "Monday"
                assert result["parameters"]["semester"] == 5
                
                # Verify no missing fields (query has no requirements)
                assert result["missing_fields"] == []

    @pytest.mark.asyncio
    async def test_parse_intent_help_intent(self):
        """Test parsing help intent."""
        mock_llm_response = {
            "intent": "help",
            "parameters": {
                "day_of_week": None,
                "semester": None,
                "department_id": None,
                "subject": None,
                "start_time": None,
                "end_time": None,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.99,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                result = await parse_intent("What can you do?", {})

                # Verify intent
                assert result["intent"] == "help"
                
                # Verify no missing fields
                assert result["missing_fields"] == []

    @pytest.mark.asyncio
    async def test_parse_intent_unclear_fallback(self):
        """Test parsing unclear intent for ambiguous messages."""
        mock_llm_response = {
            "intent": "unclear",
            "parameters": {
                "day_of_week": None,
                "semester": None,
                "department_id": None,
                "subject": None,
                "start_time": None,
                "end_time": None,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.3,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                result = await parse_intent("xyz abc 123", {})

                # Verify intent is unclear
                assert result["intent"] == "unclear"
                
                # Verify low confidence
                assert result["confidence"] < 0.5

    @pytest.mark.asyncio
    async def test_parse_intent_replace_bulk_operation(self):
        """Test parsing replace intent for bulk timetable replacement."""
        mock_llm_response = {
            "intent": "replace",
            "parameters": {
                "semester": 5,
                "department_id": "123e4567-e89b-12d3-a456-426614174000",
                "day_of_week": None,
                "subject": None,
                "start_time": None,
                "end_time": None,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.85,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                context = {
                    "department_id": "123e4567-e89b-12d3-a456-426614174000",
                }

                result = await parse_intent(
                    "Replace entire semester 5 timetable",
                    context
                )

                # Verify intent
                assert result["intent"] == "replace"
                
                # Verify required parameters
                assert result["parameters"]["semester"] == 5
                assert result["parameters"]["department_id"] == "123e4567-e89b-12d3-a456-426614174000"
                
                # Verify no missing fields
                assert result["missing_fields"] == []

    @pytest.mark.asyncio
    async def test_parse_intent_missing_multiple_fields(self):
        """Test identifying multiple missing required fields."""
        mock_llm_response = {
            "intent": "add",
            "parameters": {
                "day_of_week": "Monday",
                "start_time": None,  # Missing
                "end_time": None,
                "subject": None,  # Missing
                "semester": None,  # Missing
                "department_id": None,  # Missing
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": ["start_time", "subject", "semester", "department_id"],
            "confidence": 0.7,
        }

        with patch("app.services.ai_assistant.call_groq_llm", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = mock_llm_response
            
            with patch("app.services.ai_assistant.settings") as mock_settings:
                mock_settings.AI_ASSISTANT_LLM_PROVIDER = "groq"
                mock_settings.AI_ASSISTANT_LLM_TIMEOUT = 10

                result = await parse_intent("Add a class on Monday", {})

                # Verify intent recognized
                assert result["intent"] == "add"
                
                # Verify day parsed
                assert result["parameters"]["day_of_week"] == "Monday"
                
                # Verify multiple missing fields identified
                assert "start_time" in result["missing_fields"]
                assert "subject" in result["missing_fields"]
                assert "semester" in result["missing_fields"]
                assert "department_id" in result["missing_fields"]
