"""LLM service for AI Assistant natural language processing.

Provides intent extraction and parameter parsing for timetable management
using Groq LLM (primary) and Google Gemini (fallback).
"""
import asyncio
import json
import logging
import re
from datetime import time
from typing import Any, Literal

import httpx

from app.config import settings
from app.core.logging_config import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)


# ─── LLM System Prompt ───────────────────────────────────────────────────────

LLM_SYSTEM_PROMPT = """You are an AI assistant for academic timetable management. Your role is to:

1. Extract structured information from natural language requests about timetable operations
2. Identify the intent: add, update, delete, replace, query, or help
3. Extract parameters: department, semester, day_of_week, start_time, end_time, subject, room, faculty_name

**RULES:**
- Day names: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday (full names, capitalized)
- Time format: HH:MM (24-hour). Parse "9 AM" as "09:00", "2:30 PM" as "14:30", "9" as "09:00"
- If end_time missing but duration implied, calculate: "9-10" means start=09:00, end=10:00
- If only start time provided with no end time, assume 1-hour duration: "9 AM" → start=09:00, end=10:00
- Semester: integer 1-8
- Mark fields as "missing" if not explicitly stated or inferable from context

**TIME PARSING EXAMPLES:**
- "9 AM" → start_time: "09:00", end_time: "10:00" (assume 1 hour if no end specified)
- "2:30 PM" → "14:30"
- "9-10" or "9 to 10" → start_time: "09:00", end_time: "10:00"
- "14:00-15:30" → start_time: "14:00", end_time: "15:30"
- "9:30 AM to 11 AM" → start_time: "09:30", end_time: "11:00"

**DAY PARSING EXAMPLES:**
- "Monday", "Mon", "monday" → "Monday"
- "tue", "Tue", "Tuesday" → "Tuesday"

**INTENT EXAMPLES:**
- "Add Mathematics on Monday 9-10 AM" → intent: "add"
- "Update the Monday class" → intent: "update"
- "Delete Tuesday Physics" → intent: "delete"
- "Replace entire semester 5 timetable" → intent: "replace"
- "Show me the schedule" → intent: "query"
- "What can you do?" → intent: "help"

**OUTPUT FORMAT (MUST BE VALID JSON):**
{
  "intent": "add|update|delete|replace|query|help|unclear",
  "parameters": {
    "department_id": null,
    "semester": null,
    "day_of_week": null,
    "start_time": null,
    "end_time": null,
    "subject": null,
    "room": null,
    "faculty_name": null
  },
  "missing_fields": ["list", "of", "missing", "required", "fields"],
  "confidence": 0.95
}

**MISSING FIELDS BY INTENT:**
- add: requires day_of_week, start_time, subject, semester, department_id (end_time can be calculated)
- update: requires identifier fields (day + time + subject) + fields to change
- delete: requires identifier (day + time + subject OR unique description)
- replace: requires semester, department_id
- query: no required fields (all optional filters)
- help: no required fields

Return ONLY the JSON object, no other text."""


# ─── LLM Provider Functions ──────────────────────────────────────────────────


async def call_groq_llm(
    message: str,
    context: dict[str, Any],
    timeout: int = 10,
) -> dict[str, Any]:
    """
    Call Groq LLM API with JSON mode for intent extraction.
    
    Uses Llama-3.1-70B-versatile model with structured JSON output.
    
    Args:
        message: User's natural language message
        context: Conversation context (department_id, semester, etc.)
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        dict with keys: intent, parameters, missing_fields, confidence
    
    Raises:
        TimeoutError: If LLM request exceeds timeout
        Exception: If LLM API call fails or response is invalid
    """
    if not settings.GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not configured")

    structured_logger.info(
        "Calling Groq LLM for intent extraction",
        message_length=len(message),
        context_keys=list(context.keys()),
        model="llama-3.1-70b-versatile",
    )

    # Build context string for the LLM
    context_str = ""
    if context:
        context_parts = []
        if context.get("department_id"):
            context_parts.append(f"Department: {context['department_id']}")
        if context.get("semester"):
            context_parts.append(f"Semester: {context['semester']}")
        if context_parts:
            context_str = "\n\nCONVERSATION CONTEXT:\n" + "\n".join(context_parts)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": f"{message}{context_str}"},
        ],
        "temperature": 0.3,  # Low temperature for consistent structured output
        "max_tokens": 500,
        "response_format": {"type": "json_object"},  # Force JSON output
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # Extract and parse JSON response
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            structured_logger.info(
                "Groq LLM response received",
                intent=parsed.get("intent"),
                confidence=parsed.get("confidence"),
                missing_fields_count=len(parsed.get("missing_fields", [])),
            )

            return parsed

    except asyncio.TimeoutError:
        structured_logger.error(
            "Groq LLM request timeout",
            timeout_seconds=timeout,
        )
        raise TimeoutError(f"Groq LLM request exceeded {timeout} seconds")

    except httpx.TimeoutException:
        structured_logger.error(
            "Groq LLM HTTP timeout",
            timeout_seconds=timeout,
        )
        raise TimeoutError(f"Groq LLM request exceeded {timeout} seconds")

    except httpx.HTTPStatusError as e:
        structured_logger.error(
            "Groq LLM API error",
            status_code=e.response.status_code,
            error_message=str(e),
        )
        raise Exception(f"Groq API error: {e.response.status_code} - {str(e)}")

    except (json.JSONDecodeError, KeyError) as e:
        structured_logger.error(
            "Failed to parse Groq LLM response",
            exception_type=type(e).__name__,
            error_message=str(e),
        )
        raise Exception(f"Invalid response from Groq LLM: {str(e)}")


async def call_gemini_llm(
    message: str,
    context: dict[str, Any],
    timeout: int = 10,
) -> dict[str, Any]:
    """
    Call Google Gemini API as fallback for intent extraction.
    
    Uses Gemini-1.5-flash model.
    
    Args:
        message: User's natural language message
        context: Conversation context (department_id, semester, etc.)
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        dict with keys: intent, parameters, missing_fields, confidence
    
    Raises:
        TimeoutError: If LLM request exceeds timeout
        Exception: If LLM API call fails or response is invalid
    """
    if not settings.GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY not configured")

    structured_logger.info(
        "Calling Gemini LLM for intent extraction (fallback)",
        message_length=len(message),
        context_keys=list(context.keys()),
        model="gemini-1.5-flash",
    )

    # Build context string for the LLM
    context_str = ""
    if context:
        context_parts = []
        if context.get("department_id"):
            context_parts.append(f"Department: {context['department_id']}")
        if context.get("semester"):
            context_parts.append(f"Semester: {context['semester']}")
        if context_parts:
            context_str = "\n\nCONVERSATION CONTEXT:\n" + "\n".join(context_parts)

    # Combine system prompt with user message for Gemini
    full_prompt = f"{LLM_SYSTEM_PROMPT}\n\nUSER MESSAGE:\n{message}{context_str}\n\nRespond with ONLY the JSON object:"

    try:
        import google.generativeai as genai

        # Configure Gemini with timeout
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Call Gemini with timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, full_prompt),
            timeout=timeout,
        )

        # Extract text and parse JSON
        response_text = response.text

        # Try to extract JSON from response (may have markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(1))
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                raise Exception("No JSON object found in Gemini response")

        structured_logger.info(
            "Gemini LLM response received",
            intent=parsed.get("intent"),
            confidence=parsed.get("confidence"),
            missing_fields_count=len(parsed.get("missing_fields", [])),
        )

        return parsed

    except asyncio.TimeoutError:
        structured_logger.error(
            "Gemini LLM request timeout",
            timeout_seconds=timeout,
        )
        raise TimeoutError(f"Gemini LLM request exceeded {timeout} seconds")

    except (json.JSONDecodeError, AttributeError) as e:
        structured_logger.error(
            "Failed to parse Gemini LLM response",
            exception_type=type(e).__name__,
            error_message=str(e),
        )
        raise Exception(f"Invalid response from Gemini LLM: {str(e)}")

    except Exception as e:
        structured_logger.error(
            "Gemini LLM API error",
            exception_type=type(e).__name__,
            error_message=str(e),
        )
        raise Exception(f"Gemini API error: {str(e)}")


# ─── Regex-Based Fallback Parser ─────────────────────────────────────────────


def parse_intent_regex(
    message: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Regex-based fallback parser for when LLM fails.
    
    Uses pattern matching to extract intent and parameters from natural language.
    This is a simple rule-based fallback that handles common patterns.
    
    Args:
        message: User's natural language message
        context: Conversation context (department_id, semester, etc.)
    
    Returns:
        dict with keys:
        - intent: "add" | "update" | "delete" | "replace" | "query" | "help" | "unclear"
        - parameters: dict with extracted parameters
        - missing_fields: list of required fields not extracted
        - confidence: float (lower than LLM, typically 0.5-0.7)
        
    Requirements: 9.5, 9.7, 14.4
    """
    structured_logger.info(
        "Using regex-based fallback parser",
        message_length=len(message),
        context_keys=list(context.keys()),
    )
    
    message_lower = message.lower().strip()
    
    # Initialize parameters with None
    parameters: dict[str, Any] = {
        "department_id": context.get("department_id"),
        "semester": context.get("semester"),
        "day_of_week": None,
        "start_time": None,
        "end_time": None,
        "subject": None,
        "room": None,
        "faculty_name": None,
    }
    
    # ─── Intent Detection ─────────────────────────────────────────────────────
    
    intent = "unclear"
    confidence = 0.5
    
    # Help intent (highest priority)
    if any(keyword in message_lower for keyword in ["help", "what can you do", "how do i", "guide"]):
        intent = "help"
        confidence = 0.8
        return {
            "intent": intent,
            "parameters": parameters,
            "missing_fields": [],
            "confidence": confidence,
        }
    
    # Query intent (check before add/update/delete to avoid conflicts)
    if any(keyword in message_lower for keyword in ["show", "list", "view", "display", "get schedule", "what is"]):
        intent = "query"
        confidence = 0.7
    
    # Replace intent
    elif any(keyword in message_lower for keyword in ["replace", "bulk", "entire timetable"]):
        intent = "replace"
        confidence = 0.6
    
    # Update intent
    elif any(keyword in message_lower for keyword in ["update", "change", "modify", "edit"]):
        intent = "update"
        confidence = 0.6
    
    # Delete intent
    elif any(keyword in message_lower for keyword in ["delete", "remove", "cancel"]):
        intent = "delete"
        confidence = 0.6
    
    # Add intent (lowest priority to avoid false positives)
    elif any(keyword in message_lower for keyword in ["add", "create", "schedule", "new class"]):
        intent = "add"
        confidence = 0.6
    
    # ─── Parameter Extraction ─────────────────────────────────────────────────
    
    # Extract day name
    day_pattern = r'\b(monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)\b'
    day_match = re.search(day_pattern, message_lower)
    if day_match:
        try:
            parameters["day_of_week"] = parse_day_name(day_match.group(1))
        except ValueError:
            pass
    
    # Extract time expressions
    # Pattern 1: "9-10", "9 to 10", "9:00-10:00"
    time_range_pattern = r'(\d{1,2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)\s*(?:-|to)\s*(\d{1,2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)'
    time_range_match = re.search(time_range_pattern, message, re.IGNORECASE)
    
    if time_range_match:
        try:
            parameters["start_time"] = parse_time_expression(time_range_match.group(1))
            parameters["end_time"] = parse_time_expression(time_range_match.group(2))
        except ValueError:
            pass
    else:
        # Pattern 2: Single time "9 AM", "09:00"
        single_time_pattern = r'\b(\d{1,2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)\b'
        time_matches = re.findall(single_time_pattern, message, re.IGNORECASE)
        if time_matches:
            try:
                parameters["start_time"] = parse_time_expression(time_matches[0])
                # Auto-calculate end time if not specified
                if parameters["start_time"]:
                    parameters["end_time"] = calculate_end_time(parameters["start_time"])
            except ValueError:
                pass
    
    # Extract semester
    semester_pattern = r'\b(?:semester|sem)\s*(\d)\b'
    semester_match = re.search(semester_pattern, message_lower)
    if semester_match:
        semester = int(semester_match.group(1))
        if 1 <= semester <= 8:
            parameters["semester"] = semester
    
    # Extract subject (look for capitalized words or quoted strings)
    # Pattern 1: Quoted string
    quoted_pattern = r'["\']([^"\']+)["\']'
    quoted_match = re.search(quoted_pattern, message)
    if quoted_match:
        parameters["subject"] = quoted_match.group(1).strip()
    else:
        # Pattern 2: Subject after action words
        # Look for capitalized words after "add", "delete", "schedule", etc.
        subject_after_action_pattern = r'\b(?:add|create|schedule|delete|remove|cancel)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*?)\s+(?:on|at|in|for|to)'
        subject_match = re.search(subject_after_action_pattern, message, re.IGNORECASE)
        if subject_match:
            parameters["subject"] = subject_match.group(1).strip()
        else:
            # Pattern 3: Look for words after "subject", "class", "course"
            subject_keyword_pattern = r'\b(?:subject|class|course)\s+(?:called\s+)?([A-Z][a-zA-Z\s]+?)(?:\s+on|\s+at|\s+in|\s+for|$)'
            subject_match = re.search(subject_keyword_pattern, message)
            if subject_match:
                parameters["subject"] = subject_match.group(1).strip()
            else:
                # Pattern 4: Capitalized word(s) in the middle of the sentence
                # Exclude common words like days and action words
                capitalized_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
                cap_matches = re.findall(capitalized_pattern, message)
                # Filter out common words and action words
                common_words = {
                    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
                    "AM", "PM", "Room", "Add", "Delete", "Remove", "Update", "Change", "Modify",
                    "Show", "List", "View", "Display", "Schedule", "Create", "New", "Cancel"
                }
                for cap_word in cap_matches:
                    if cap_word not in common_words:
                        parameters["subject"] = cap_word
                        break
    
    # Extract room
    room_pattern = r'\b(?:room|Room)\s+([A-Za-z0-9]+)\b'
    room_match = re.search(room_pattern, message)
    if room_match:
        parameters["room"] = room_match.group(1)
    
    # Extract faculty name (look for "Dr.", "Prof.", or after "by", "with")
    faculty_pattern = r'\b(?:by|with|faculty)\s+(?:Dr\.|Prof\.)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    faculty_match = re.search(faculty_pattern, message)
    if faculty_match:
        parameters["faculty_name"] = faculty_match.group(1).strip()
    
    # ─── Determine Missing Fields ─────────────────────────────────────────────
    
    _, missing_fields, _ = validate_intent_parameters(intent, parameters, context)
    
    structured_logger.info(
        "Regex parser extracted intent",
        intent=intent,
        confidence=confidence,
        missing_fields_count=len(missing_fields),
        parameters_extracted=sum(1 for v in parameters.values() if v is not None),
    )
    
    return {
        "intent": intent,
        "parameters": parameters,
        "missing_fields": missing_fields,
        "confidence": confidence,
    }


# ─── Intent Parsing with Fallback ────────────────────────────────────────────


async def parse_intent_with_fallback(
    message: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract structured intent and parameters with robust error handling.
    
    Strategy:
    1. Try primary LLM provider (Groq or Gemini)
    2. On timeout, retry once with same provider
    3. On failure, try fallback LLM provider
    4. On complete LLM failure, use regex-based fallback parser
    
    Args:
        message: User's natural language message
        context: Conversation context (department_id, semester, etc.)
    
    Returns:
        dict with keys:
        - intent: "add" | "update" | "delete" | "replace" | "query" | "help" | "unclear"
        - parameters: dict with extracted parameters
        - missing_fields: list of required fields not extracted
        - confidence: float (0-1)
    
    Requirements: 9.5, 14.4
    """
    timeout = settings.AI_ASSISTANT_LLM_TIMEOUT
    provider = settings.AI_ASSISTANT_LLM_PROVIDER
    
    structured_logger.info(
        "Starting intent parsing with fallback",
        primary_provider=provider,
        timeout_seconds=timeout,
        message_length=len(message),
    )
    
    # Initialize error tracking
    primary_error: Exception | None = None
    
    # ─── Step 1: Try Primary Provider ────────────────────────────────────────
    
    try:
        if provider == "groq":
            result = await call_groq_llm(message, context, timeout)
        elif provider == "gemini":
            result = await call_gemini_llm(message, context, timeout)
        else:
            structured_logger.warning(
                f"Unknown LLM provider '{provider}', defaulting to Groq"
            )
            result = await call_groq_llm(message, context, timeout)
        
        structured_logger.info(
            "Primary LLM provider succeeded",
            provider=provider,
            intent=result.get("intent"),
            confidence=result.get("confidence"),
        )
        return result
        
    except TimeoutError as timeout_error:
        structured_logger.warning(
            "Primary LLM provider timeout, retrying once",
            provider=provider,
            error_message=str(timeout_error),
        )
        
        # ─── Step 2: Retry Once on Timeout ───────────────────────────────────
        
        try:
            if provider == "groq":
                result = await call_groq_llm(message, context, timeout)
            else:
                result = await call_gemini_llm(message, context, timeout)
            
            structured_logger.info(
                "Primary LLM provider succeeded on retry",
                provider=provider,
                intent=result.get("intent"),
            )
            return result
            
        except Exception as retry_error:
            structured_logger.warning(
                "Primary LLM provider retry failed, trying fallback provider",
                provider=provider,
                error_message=str(retry_error),
            )
            primary_error = retry_error
    
    except Exception as e:
        primary_error = e
        structured_logger.warning(
            "Primary LLM provider failed (non-timeout), trying fallback provider",
            provider=provider,
            error_type=type(primary_error).__name__,
            error_message=str(primary_error),
        )
    
    # ─── Step 3: Try Fallback LLM Provider ───────────────────────────────────
    
    try:
        if provider == "groq":
            # Fallback to Gemini
            fallback_provider = "gemini"
            result = await call_gemini_llm(message, context, timeout)
        else:
            # Fallback to Groq
            fallback_provider = "groq"
            result = await call_groq_llm(message, context, timeout)
        
        structured_logger.info(
            "Fallback LLM provider succeeded",
            fallback_provider=fallback_provider,
            intent=result.get("intent"),
            confidence=result.get("confidence"),
        )
        return result
        
    except Exception as fallback_error:
        structured_logger.error(
            "Both primary and fallback LLM providers failed, using regex parser",
            primary_provider=provider,
            primary_error=str(primary_error),
            fallback_error=str(fallback_error),
            fallback_error_type=type(fallback_error).__name__,
        )
    
    # ─── Step 4: Use Regex-Based Fallback Parser ─────────────────────────────
    
    try:
        result = parse_intent_regex(message, context)
        
        structured_logger.info(
            "Regex fallback parser succeeded",
            intent=result.get("intent"),
            confidence=result.get("confidence"),
        )
        return result
        
    except Exception as regex_error:
        structured_logger.error(
            "Regex fallback parser failed",
            error_type=type(regex_error).__name__,
            error_message=str(regex_error),
        )
        
        # ─── Last Resort: Return Unclear Intent ──────────────────────────────
        
        structured_logger.error(
            "All parsing methods failed, returning unclear intent"
        )
        
        return {
            "intent": "unclear",
            "parameters": {
                "department_id": context.get("department_id"),
                "semester": context.get("semester"),
                "day_of_week": None,
                "start_time": None,
                "end_time": None,
                "subject": None,
                "room": None,
                "faculty_name": None,
            },
            "missing_fields": [],
            "confidence": 0.0,
        }


async def parse_intent(
    message: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract structured intent and parameters from natural language.
    
    This is the main entry point for intent parsing. It delegates to
    parse_intent_with_fallback() which handles retries and fallback logic.
    
    Args:
        message: User's natural language message
        context: Conversation context (department_id, semester, etc.)
    
    Returns:
        dict with keys:
        - intent: "add" | "update" | "delete" | "replace" | "query" | "help" | "unclear"
        - parameters: dict with extracted parameters
        - missing_fields: list of required fields not extracted
        - confidence: float (0-1)
    """
    return await parse_intent_with_fallback(message, context)


# ─── Helper Functions ─────────────────────────────────────────────────────────


def parse_time_string(time_str: str) -> time | None:
    """
    Parse time string to time object.
    
    Supports formats:
    - "9 AM", "09:00", "9:00 AM", "0900"
    - "2:30 PM", "14:30", "2:30 PM"
    
    Args:
        time_str: Time string to parse
    
    Returns:
        time object or None if parsing fails
    """
    if not time_str:
        return None

    try:
        # Handle HH:MM format
        if ":" in time_str:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1][:2])  # Take first 2 digits for minute
            return time(hour=hour, minute=minute)

        # Handle "HHMM" format
        if len(time_str) == 4 and time_str.isdigit():
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            return time(hour=hour, minute=minute)

        # Handle "H" or "HH" format (assume :00 minutes)
        if time_str.isdigit():
            hour = int(time_str)
            return time(hour=hour, minute=0)

        return None

    except (ValueError, IndexError):
        return None


def normalize_day_name(day: str) -> str | None:
    """
    Normalize day name to full capitalized format.
    
    Args:
        day: Day name (e.g., "mon", "Monday", "MONDAY")
    
    Returns:
        Normalized day name (e.g., "Monday") or None if invalid
    """
    if not day:
        return None

    day_lower = day.lower().strip()

    day_map = {
        "monday": "Monday",
        "mon": "Monday",
        "tuesday": "Tuesday",
        "tue": "Tuesday",
        "tues": "Tuesday",
        "wednesday": "Wednesday",
        "wed": "Wednesday",
        "thursday": "Thursday",
        "thu": "Thursday",
        "thur": "Thursday",
        "thurs": "Thursday",
        "friday": "Friday",
        "fri": "Friday",
        "saturday": "Saturday",
        "sat": "Saturday",
        "sunday": "Sunday",
        "sun": "Sunday",
    }

    return day_map.get(day_lower)


def validate_field_values(
    parameters: dict[str, Any],
) -> tuple[bool, str | None]:
    """
    Validate field-specific business rules for timetable parameters.
    
    Validation Rules:
    - day_of_week: Must be in valid days list (Monday-Sunday)
    - start_time < end_time: When both are present
    - semester: Must be 1-8
    - subject: Must be 1-100 characters
    - time format: Must be HH:MM (validated during parsing)
    
    Args:
        parameters: Dictionary of extracted parameters
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if all validations pass
        - error_message: Descriptive error message if validation fails, None otherwise
        
    Requirements: 9.1, 9.2, 9.3, 9.4
    """
    # Validate day_of_week
    if parameters.get("day_of_week"):
        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        day = parameters["day_of_week"]
        if day not in valid_days:
            return (
                False,
                f"Invalid day name. Please use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday."
            )
    
    # Validate semester range
    if parameters.get("semester") is not None:
        semester = parameters["semester"]
        if not isinstance(semester, int) or semester < 1 or semester > 8:
            return (False, "Semester must be between 1 and 8.")
    
    # Validate subject length
    if "subject" in parameters and parameters["subject"] is not None:
        subject = parameters["subject"]
        if not isinstance(subject, str) or len(subject) < 1:
            return (False, "Subject name is required.")
        if len(subject) > 100:
            return (False, "Subject name must be 100 characters or less.")
    
    # Validate time format (HH:MM) and start_time < end_time
    if parameters.get("start_time") and parameters.get("end_time"):
        start_time = parameters["start_time"]
        end_time = parameters["end_time"]
        
        # Validate HH:MM format
        time_pattern = r'^([01]\d|2[0-3]):([0-5]\d)$'
        if not re.match(time_pattern, start_time):
            return (False, f"Invalid start time format. Please use HH:MM format (e.g., 09:00, 14:30).")
        if not re.match(time_pattern, end_time):
            return (False, f"Invalid end time format. Please use HH:MM format (e.g., 09:00, 14:30).")
        
        # Validate start_time < end_time
        if start_time >= end_time:
            return (False, "Start time must be before end time. Please specify a valid time range.")
    
    # All validations passed
    return (True, None)


def validate_intent_parameters(
    intent: str,
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> tuple[bool, list[str], str | None]:
    """
    Validate parameters for the given intent and identify missing required fields.
    
    Performs two types of validation:
    1. Required field presence checking
    2. Field-specific business rule validation
    
    Args:
        intent: The extracted intent
        parameters: Extracted parameters
        context: Conversation context
    
    Returns:
        Tuple of (is_valid, missing_fields, error_message)
        - is_valid: True if all required fields present and valid
        - missing_fields: List of missing required field names
        - error_message: Descriptive error if field validation fails, None otherwise
    """
    missing = []

    # Merge context into parameters (context provides defaults)
    merged = {**context, **parameters}

    if intent == "add":
        # Required: day_of_week, start_time, subject, semester, department_id
        # end_time can be calculated from start_time
        if not merged.get("day_of_week"):
            missing.append("day_of_week")
        if not merged.get("start_time"):
            missing.append("start_time")
        if not merged.get("subject"):
            missing.append("subject")
        if not merged.get("semester"):
            missing.append("semester")
        if not merged.get("department_id"):
            missing.append("department_id")

    elif intent == "update":
        # Required: identifier (day + time + subject) + fields to change
        if not merged.get("day_of_week"):
            missing.append("day_of_week")
        if not merged.get("start_time"):
            missing.append("start_time")
        if not merged.get("subject"):
            missing.append("subject")
        if not merged.get("semester"):
            missing.append("semester")

    elif intent == "delete":
        # Required: identifier (day + time + subject)
        if not merged.get("day_of_week"):
            missing.append("day_of_week")
        if not merged.get("subject"):
            missing.append("subject")
        if not merged.get("semester"):
            missing.append("semester")

    elif intent == "replace":
        # Required: semester, department_id
        if not merged.get("semester"):
            missing.append("semester")
        if not merged.get("department_id"):
            missing.append("department_id")

    elif intent in ("query", "help", "unclear"):
        # No required fields
        pass

    # If we have missing required fields, return early
    if missing:
        return (False, missing, None)
    
    # Perform field-specific validation on merged parameters
    values_valid, error_message = validate_field_values(merged)
    
    return (values_valid, missing, error_message)


# ─── Time and Day Parsing Utilities (Task 3.3) ───────────────────────────────


def parse_time_expression(time_str: str) -> str:
    """
    Convert various time formats to HH:MM format.
    
    Supports formats:
    - "9 AM", "9AM", "09:00 AM" -> "09:00"
    - "2:30 PM", "2:30PM", "14:30" -> "14:30"
    - "09:00", "9:00" -> "09:00"
    - "0900" -> "09:00"
    
    Args:
        time_str: Time expression in various natural language formats
        
    Returns:
        Time string in HH:MM format (24-hour)
        
    Raises:
        ValueError: If time_str cannot be parsed
    
    Examples:
        >>> parse_time_expression("9 AM")
        "09:00"
        >>> parse_time_expression("2:30 PM")
        "14:30"
        >>> parse_time_expression("09:00")
        "09:00"
    
    Requirements: 4.4, 4.5
    """
    if not time_str or not isinstance(time_str, str):
        raise ValueError(f"Invalid time expression: {time_str}")
    
    # Clean up the input
    time_str = time_str.strip().upper()
    
    # Pattern 1: "9 AM", "9AM", "09:00 AM", "9:30 PM" etc.
    # Matches: optional hours:minutes followed by optional space and AM/PM
    am_pm_pattern = r'^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$'
    match = re.match(am_pm_pattern, time_str)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)
        
        # Validate hour and minute ranges
        if hour < 1 or hour > 12:
            raise ValueError(f"Invalid hour in 12-hour format: {hour}")
        if minute < 0 or minute > 59:
            raise ValueError(f"Invalid minute: {minute}")
        
        # Convert to 24-hour format
        if period == "AM":
            if hour == 12:
                hour = 0
        else:  # PM
            if hour != 12:
                hour += 12
        
        return f"{hour:02d}:{minute:02d}"
    
    # Pattern 2: "HH:MM" 24-hour format (e.g., "09:00", "14:30")
    hhmm_pattern = r'^(\d{1,2}):(\d{2})$'
    match = re.match(hhmm_pattern, time_str)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        # Validate ranges
        if hour < 0 or hour > 23:
            raise ValueError(f"Invalid hour in 24-hour format: {hour}")
        if minute < 0 or minute > 59:
            raise ValueError(f"Invalid minute: {minute}")
        
        return f"{hour:02d}:{minute:02d}"
    
    # Pattern 3: "HHMM" 4-digit format (e.g., "0900", "1430")
    hhmm_compact_pattern = r'^(\d{4})$'
    match = re.match(hhmm_compact_pattern, time_str)
    
    if match:
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        
        # Validate ranges
        if hour < 0 or hour > 23:
            raise ValueError(f"Invalid hour in 4-digit format: {hour}")
        if minute < 0 or minute > 59:
            raise ValueError(f"Invalid minute: {minute}")
        
        return f"{hour:02d}:{minute:02d}"
    
    # Pattern 4: Just hour number (e.g., "9", "14")
    hour_only_pattern = r'^(\d{1,2})$'
    match = re.match(hour_only_pattern, time_str)
    
    if match:
        hour = int(match.group(1))
        
        # Validate range (assume 24-hour format for single digits >= 0)
        if hour < 0 or hour > 23:
            raise ValueError(f"Invalid hour: {hour}")
        
        return f"{hour:02d}:00"
    
    raise ValueError(f"Unable to parse time expression: {time_str}")


def parse_day_name(day_str: str) -> str:
    """
    Normalize day names to standard format "Monday", "Tuesday", etc.
    
    Accepts various formats:
    - Full names: "monday", "Monday", "MONDAY"
    - Abbreviations: "Mon", "mon", "MON"
    
    Args:
        day_str: Day name in various formats
        
    Returns:
        Standardized day name with first letter capitalized
        
    Raises:
        ValueError: If day_str is not a valid day name
        
    Examples:
        >>> parse_day_name("mon")
        "Monday"
        >>> parse_day_name("MONDAY")
        "Monday"
        >>> parse_day_name("tuesday")
        "Tuesday"
        
    Requirements: 4.7
    """
    if not day_str or not isinstance(day_str, str):
        raise ValueError(f"Invalid day name: {day_str}")
    
    # Clean up the input
    day_str = day_str.strip().lower()
    
    # Mapping of abbreviations and full names to standard format
    day_mapping = {
        # Full names
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
        "saturday": "Saturday",
        "sunday": "Sunday",
        # Common abbreviations
        "mon": "Monday",
        "tue": "Tuesday",
        "tues": "Tuesday",
        "wed": "Wednesday",
        "thu": "Thursday",
        "thur": "Thursday",
        "thurs": "Thursday",
        "fri": "Friday",
        "sat": "Saturday",
        "sun": "Sunday",
    }
    
    if day_str in day_mapping:
        return day_mapping[day_str]
    
    raise ValueError(
        f"Invalid day name: {day_str}. "
        "Please use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, or Sunday."
    )


def calculate_end_time(start_time_str: str, duration_hours: int = 1) -> str:
    """
    Calculate end time by adding duration to start time.
    
    When end_time is not specified, this function assumes a default duration
    (typically 1 hour for class periods) and calculates the end time.
    
    Args:
        start_time_str: Start time in HH:MM format
        duration_hours: Duration to add in hours (default: 1)
        
    Returns:
        End time in HH:MM format
        
    Raises:
        ValueError: If start_time_str is not in valid HH:MM format
        
    Examples:
        >>> calculate_end_time("09:00")
        "10:00"
        >>> calculate_end_time("14:30", 2)
        "16:30"
        >>> calculate_end_time("23:00")
        "00:00"
        
    Requirements: 4.6
    """
    from datetime import datetime, timedelta
    
    if not start_time_str or not isinstance(start_time_str, str):
        raise ValueError(f"Invalid start time: {start_time_str}")
    
    # Validate HH:MM format
    hhmm_pattern = r'^(\d{1,2}):(\d{2})$'
    match = re.match(hhmm_pattern, start_time_str.strip())
    
    if not match:
        raise ValueError(f"Start time must be in HH:MM format: {start_time_str}")
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    
    # Validate ranges
    if hour < 0 or hour > 23:
        raise ValueError(f"Invalid hour: {hour}")
    if minute < 0 or minute > 59:
        raise ValueError(f"Invalid minute: {minute}")
    
    # Create a time object and add duration
    start_dt = datetime.combine(datetime.today(), time(hour, minute))
    end_dt = start_dt + timedelta(hours=duration_hours)
    
    # Extract time and format as HH:MM
    end_time = end_dt.time()
    return f"{end_time.hour:02d}:{end_time.minute:02d}"


# ─── Response Generation Functions (Task 3.5) ─────────────────────────────────


def generate_response(
    result: dict[str, Any],
    context: dict[str, Any],
) -> str:
    """
    Convert OperationResult to natural language response.
    
    Generates friendly, conversational messages based on the operation type
    and result status. Provides clear confirmation for successful operations
    and helpful guidance for errors.
    
    Args:
        result: OperationResult dict with keys:
            - operation_type: "add" | "update" | "delete" | "replace" | "query"
            - success: bool
            - affected_entries_count: int
            - entries: list of TimetableOut objects (optional)
            - error_message: str or None
        context: ConversationContext dict with optional department_id, semester
        
    Returns:
        Natural language response string
        
    Examples:
        >>> generate_response({
        ...     "operation_type": "add",
        ...     "success": True,
        ...     "affected_entries_count": 1,
        ...     "entries": [{"subject": "Mathematics", "day_of_week": "Monday", ...}]
        ... }, {})
        "✓ Added Mathematics class on Monday from 09:00 to 10:00."
        
    Requirements: 1.2, 10.2, 10.3, 10.4
    """
    operation_type = result.get("operation_type")
    success = result.get("success", False)
    error_message = result.get("error_message")
    affected_count = result.get("affected_entries_count", 0)
    entries = result.get("entries", [])
    
    # Handle errors first
    if not success:
        if error_message:
            return f"❌ {error_message}"
        return "❌ An error occurred while processing your request. Please try again."
    
    # Generate success messages based on operation type
    if operation_type == "add":
        if entries and len(entries) > 0:
            entry = entries[0]
            subject = entry.get("subject", "class")
            day = entry.get("day_of_week", "")
            start = entry.get("start_time", "")
            end = entry.get("end_time", "")
            room = entry.get("room")
            faculty = entry.get("faculty_name")
            
            # Build response with available details
            response = f"✓ Added {subject} class"
            if day:
                response += f" on {day}"
            if start and end:
                # Format time objects if they are time objects, otherwise use as strings
                if hasattr(start, 'strftime'):
                    start = start.strftime("%H:%M")
                if hasattr(end, 'strftime'):
                    end = end.strftime("%H:%M")
                response += f" from {start} to {end}"
            if room:
                response += f" in {room}"
            if faculty:
                response += f" with {faculty}"
            response += "."
            return response
        else:
            return "✓ Class added successfully."
    
    elif operation_type == "update":
        if entries and len(entries) > 0:
            entry = entries[0]
            subject = entry.get("subject", "class")
            day = entry.get("day_of_week", "")
            response = f"✓ Updated {subject} class"
            if day:
                response += f" on {day}"
            response += "."
            return response
        else:
            return "✓ Timetable entry updated successfully."
    
    elif operation_type == "delete":
        if affected_count > 0:
            return f"✓ Deleted {affected_count} timetable {'entry' if affected_count == 1 else 'entries'}."
        else:
            return "✓ Timetable entry deleted successfully."
    
    elif operation_type == "replace":
        if affected_count > 0:
            semester = context.get("semester", "")
            response = f"✓ Replaced timetable"
            if semester:
                response += f" for semester {semester}"
            response += f" with {affected_count} new {'entry' if affected_count == 1 else 'entries'}."
            return response
        else:
            return "✓ Timetable replaced successfully."
    
    elif operation_type == "query":
        if entries and len(entries) > 0:
            # Format query results
            semester = context.get("semester")
            day_filter = None
            
            # Try to determine if there's a day filter from the first entry
            if entries:
                first_day = entries[0].get("day_of_week")
                if all(e.get("day_of_week") == first_day for e in entries):
                    day_filter = first_day
            
            # Build header
            response = "Here's "
            if day_filter:
                response += f"{day_filter}'s schedule"
            else:
                response += "the schedule"
            if semester:
                response += f" for Semester {semester}"
            response += ":\n\n"
            
            # List entries (limit to 20 for readability)
            max_entries = 20
            for i, entry in enumerate(entries[:max_entries], 1):
                subject = entry.get("subject", "Unknown")
                day = entry.get("day_of_week", "")
                start = entry.get("start_time", "")
                end = entry.get("end_time", "")
                room = entry.get("room")
                faculty = entry.get("faculty_name")
                
                # Format time objects if they are time objects
                if hasattr(start, 'strftime'):
                    start = start.strftime("%H:%M")
                if hasattr(end, 'strftime'):
                    end = end.strftime("%H:%M")
                
                response += f"{i}. {subject}"
                if day and not day_filter:  # Only show day if not filtering by day
                    response += f" ({day})"
                if start and end:
                    response += f" {start}-{end}"
                if room:
                    response += f", Room {room}"
                if faculty:
                    response += f", {faculty}"
                response += "\n"
            
            # Add count
            total_count = len(entries)
            if total_count > max_entries:
                response += f"\n... and {total_count - max_entries} more entries."
            response += f"\n\nFound {total_count} {'class' if total_count == 1 else 'classes'} total."
            
            return response
        else:
            return "No classes found matching your query."
    
    # Fallback for unknown operation types
    return "✓ Operation completed successfully."


def generate_clarification(
    missing_fields: list[str],
    context: dict[str, Any],
    intent: str = "",
) -> str:
    """
    Generate clarifying question for missing required fields.
    
    Asks for ONE field at a time to maintain conversational flow.
    Prioritizes fields in order: department → semester → day → time → subject.
    
    Args:
        missing_fields: List of missing required field names
        context: ConversationContext dict with available context
        intent: The operation intent (add, update, delete, etc.)
        
    Returns:
        Natural language clarifying question
        
    Examples:
        >>> generate_clarification(["semester", "day_of_week"], {}, "add")
        "Which semester is this for?"
        >>> generate_clarification(["subject"], {"semester": 5}, "add")
        "What subject would you like to add?"
        
    Requirements: 3.5, 10.3
    """
    if not missing_fields:
        return "I have all the information I need. Proceeding..."
    
    # Priority order for asking questions
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
    
    # Find the highest priority missing field
    next_field = None
    for field in priority_order:
        if field in missing_fields:
            next_field = field
            break
    
    if not next_field:
        # If no field found in priority order, just take the first missing field
        next_field = missing_fields[0]
    
    # Generate appropriate question based on field and intent
    if next_field == "department_id":
        return "Which department is this for?"
    
    elif next_field == "semester":
        return "Which semester is this for? (Please provide a number between 1 and 8)"
    
    elif next_field == "day_of_week":
        if intent == "add":
            return "Which day of the week should this class be scheduled?"
        elif intent == "update":
            return "Which day is the class you want to update?"
        elif intent == "delete":
            return "Which day is the class you want to delete?"
        else:
            return "Which day of the week?"
    
    elif next_field == "start_time":
        if intent == "add":
            return "What time should the class start? (e.g., '9 AM', '09:00', '14:30')"
        elif intent == "update":
            return "What is the start time of the class you want to update?"
        else:
            return "What is the start time?"
    
    elif next_field == "end_time":
        return "What time should the class end? (e.g., '10 AM', '10:00', '15:30')"
    
    elif next_field == "subject":
        if intent == "add":
            return "What subject would you like to add?"
        elif intent == "update":
            return "Which subject is the class you want to update?"
        elif intent == "delete":
            return "Which subject is the class you want to delete?"
        else:
            return "What is the subject name?"
    
    elif next_field == "room":
        return "Which room should this class be in? (Optional - you can skip this)"
    
    elif next_field == "faculty_name":
        return "Who is the faculty member for this class? (Optional - you can skip this)"
    
    # Fallback
    return f"Please provide the {next_field.replace('_', ' ')}."


def generate_help_message() -> str:
    """
    Generate help message describing available operations.
    
    Provides a friendly introduction to the AI Assistant's capabilities
    with example phrases for each operation type.
    
    Returns:
        Natural language help message
        
    Examples:
        >>> help_msg = generate_help_message()
        >>> "add" in help_msg
        True
        >>> "example" in help_msg.lower()
        True
        
    Requirements: 10.2, 10.4
    """
    return """👋 Hi! I'm your AI Timetable Assistant. I can help you manage timetables through natural conversation.

**Here's what I can do:**

📝 **Add Classes**
   Add individual class entries to the timetable.
   Examples:
   • "Add Mathematics on Monday 9-10 AM"
   • "Schedule Physics on Tuesday at 2:30 PM in Room 301"
   • "Add Chemistry class Wednesday 11 AM with Dr. Smith"

✏️ **Update Classes**
   Modify existing timetable entries.
   Examples:
   • "Change Monday 9 AM class to room 202"
   • "Update Physics class to be with Dr. Johnson"
   • "Move the Tuesday Mathematics class to 10 AM"

🗑️ **Delete Classes**
   Remove classes from the timetable.
   Examples:
   • "Delete the Physics class on Tuesday"
   • "Remove Monday 9 AM Mathematics"
   • "Delete Chemistry from the schedule"

🔄 **Replace Timetable**
   Replace an entire semester's timetable at once.
   Examples:
   • "Replace semester 5 timetable"
   • "Upload new timetable for semester 3"

🔍 **View Schedule**
   Query and view timetable entries.
   Examples:
   • "Show me Monday's schedule"
   • "What classes are on Tuesday?"
   • "Show semester 5 timetable"

**Tips:**
• I'll remember your department and semester during our conversation
• I'll ask for clarification if I need more details
• You can use natural language - no need for specific formats
• Times can be written as "9 AM", "09:00", "14:30", etc.

Just tell me what you'd like to do, and I'll help you manage your timetable! 🎓"""


# ─── Operation Executor ───────────────────────────────────────────────────────


async def execute_add(
    parameters: dict[str, Any],
    admin,  # UserProfile from AcademicWrite dependency
    db,  # AsyncSession from get_db dependency
) -> dict[str, Any]:
    """
    Execute add operation by calling POST /academic/timetable.
    
    Creates a single timetable entry with validated parameters.
    
    Args:
        parameters: Dict with validated timetable entry fields:
            - department_id: UUID
            - semester: int (1-8)
            - day_of_week: str (Monday-Sunday)
            - start_time: str (HH:MM format)
            - end_time: str (HH:MM format)
            - subject: str (1-100 chars)
            - room: str | None (optional)
            - faculty_name: str | None (optional)
        admin: UserProfile with department_id and authentication
        db: AsyncSession for database operations
    
    Returns:
        OperationResult dict with keys:
        - operation_type: "add"
        - success: bool
        - affected_entries_count: int
        - entries: list[TimetableOut]
        - error_message: str | None
    
    Requirements: 4.1, 4.2, 4.8
    """
    from app.models.academic import Timetable
    from app.schemas.campus import TimetableOut
    
    structured_logger.info(
        "Executing add operation",
        user_id=str(admin.id),
        department_id=str(parameters.get("department_id")),
        semester=parameters.get("semester"),
        subject=parameters.get("subject"),
    )
    
    try:
        # Parse time strings to time objects
        start_time_obj = parse_time_string(parameters["start_time"])
        end_time_obj = parse_time_string(parameters["end_time"])
        
        if not start_time_obj or not end_time_obj:
            raise ValueError("Invalid time format")
        
        # Create timetable entry
        entry = Timetable(
            department_id=parameters["department_id"],
            semester=parameters["semester"],
            day_of_week=parameters["day_of_week"],
            start_time=start_time_obj,
            end_time=end_time_obj,
            subject=parameters["subject"],
            room=parameters.get("room"),
            faculty_name=parameters.get("faculty_name"),
        )
        
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        
        structured_logger.info(
            "Add operation completed successfully",
            user_id=str(admin.id),
            entry_id=entry.id,
            subject=entry.subject,
        )
        
        # Convert to TimetableOut with proper error handling
        try:
            entry_out = TimetableOut.model_validate(entry)
        except Exception as validation_error:
            # If validation fails, it means the entry object is incomplete
            # This can happen in tests or if database doesn't return expected fields
            raise ValueError(f"Failed to validate timetable entry: {str(validation_error)}")
        
        return {
            "operation_type": "add",
            "success": True,
            "affected_entries_count": 1,
            "entries": [entry_out],
            "error_message": None,
        }
        
    except ValueError as ve:
        structured_logger.error(
            "Add operation failed - validation error",
            user_id=str(admin.id),
            error_message=str(ve),
        )
        return {
            "operation_type": "add",
            "success": False,
            "affected_entries_count": 0,
            "entries": [],
            "error_message": f"Validation error: {str(ve)}",
        }
    
    except Exception as e:
        await db.rollback()
        structured_logger.error(
            "Add operation failed - database error",
            user_id=str(admin.id),
            error_type=type(e).__name__,
            error_message=str(e),
        )
        return {
            "operation_type": "add",
            "success": False,
            "affected_entries_count": 0,
            "entries": [],
            "error_message": f"Failed to add entry: {str(e)}",
        }


async def execute_query(
    parameters: dict[str, Any],
    admin,  # UserProfile from AcademicWrite dependency
    db,  # AsyncSession from get_db dependency
) -> dict[str, Any]:
    """
    Execute query operation by calling GET /academic/timetable with filters.
    
    Retrieves timetable entries matching the specified filters.
    
    Args:
        parameters: Dict with optional filter fields:
            - department_id: UUID (defaults to admin's department)
            - semester: int (1-8) - optional
            - day_of_week: str (Monday-Sunday) - optional
        admin: UserProfile with department_id and authentication
        db: AsyncSession for database operations
    
    Returns:
        OperationResult dict with keys:
        - operation_type: "query"
        - success: bool
        - affected_entries_count: int (number of entries found)
        - entries: list[TimetableOut]
        - error_message: str | None
    
    Requirements: 4.1, 4.2, 4.8
    """
    from sqlalchemy import select
    from app.models.academic import Timetable
    from app.schemas.campus import TimetableOut
    
    structured_logger.info(
        "Executing query operation",
        user_id=str(admin.id),
        department_id=str(parameters.get("department_id")),
        semester=parameters.get("semester"),
        day_of_week=parameters.get("day_of_week"),
    )
    
    try:
        # Build query with filters
        query = select(Timetable)
        
        # Filter by department (use admin's department if not specified)
        dept_id = parameters.get("department_id") or admin.department_id
        if dept_id:
            query = query.where(Timetable.department_id == dept_id)
        
        # Filter by semester if specified
        if parameters.get("semester"):
            query = query.where(Timetable.semester == parameters["semester"])
        
        # Filter by day if specified
        if parameters.get("day_of_week"):
            query = query.where(Timetable.day_of_week == parameters["day_of_week"])
        
        # Order by day and time
        query = query.order_by(Timetable.day_of_week, Timetable.start_time)
        
        # Execute query
        result = await db.execute(query)
        scalars_result = result.scalars()
        entries = scalars_result.all()
        
        structured_logger.info(
            "Query operation completed successfully",
            user_id=str(admin.id),
            entries_found=len(entries),
        )
        
        # Convert entries to TimetableOut
        try:
            entry_outputs = [TimetableOut.model_validate(entry) for entry in entries]
        except Exception as validation_error:
            raise ValueError(f"Failed to validate timetable entries: {str(validation_error)}")
        
        return {
            "operation_type": "query",
            "success": True,
            "affected_entries_count": len(entries),
            "entries": entry_outputs,
            "error_message": None,
        }
        
    except Exception as e:
        structured_logger.error(
            "Query operation failed",
            user_id=str(admin.id),
            error_type=type(e).__name__,
            error_message=str(e),
        )
        return {
            "operation_type": "query",
            "success": False,
            "affected_entries_count": 0,
            "entries": [],
            "error_message": f"Failed to query entries: {str(e)}",
        }
