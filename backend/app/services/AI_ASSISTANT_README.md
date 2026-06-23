# AI Assistant LLM Service

## Overview

The `ai_assistant.py` module provides LLM-based natural language processing for the AI Admin Assistant feature. It extracts structured intent and parameters from natural language messages about timetable operations.

## Features

### LLM Providers
- **Primary**: Groq LLM (Llama-3.1-70B-versatile)
  - Fast inference (~500ms typical)
  - Structured JSON output mode
  - Requires `GROQ_API_KEY` environment variable

- **Fallback**: Google Gemini (gemini-1.5-flash)
  - Used when Groq fails or is unavailable
  - Requires `GEMINI_API_KEY` environment variable

### Core Functions

#### `parse_intent(message: str, context: dict) -> dict`
Main function to extract intent and parameters from natural language.

**Returns:**
```python
{
  "intent": "add|update|delete|replace|query|help|unclear",
  "parameters": {
    "department_id": "uuid or null",
    "semester": "integer or null",
    "day_of_week": "Monday|Tuesday|...",
    "start_time": "HH:MM",
    "end_time": "HH:MM",
    "subject": "string",
    "room": "string or null",
    "faculty_name": "string or null"
  },
  "missing_fields": ["list", "of", "missing", "fields"],
  "confidence": 0.95
}
```

#### `call_groq_llm(message, context, timeout=10)`
Direct call to Groq LLM API with JSON mode.

**Features:**
- Structured JSON output
- Configurable timeout
- Automatic error handling
- Comprehensive logging

#### `call_gemini_llm(message, context, timeout=10)`
Fallback call to Google Gemini API.

**Features:**
- JSON extraction from response
- Configurable timeout
- Error handling with fallback logic

### Helper Functions

#### `parse_time_string(time_str: str) -> time | None`
Parses various time formats to Python `time` object:
- "09:30" → time(9, 30)
- "0930" → time(9, 30)
- "9" → time(9, 0)

#### `normalize_day_name(day: str) -> str | None`
Normalizes day names to capitalized full format:
- "mon", "Mon", "MONDAY" → "Monday"
- "tue", "Tuesday" → "Tuesday"

#### `validate_intent_parameters(intent, parameters, context) -> (bool, list)`
Validates parameters for the given intent and identifies missing required fields.

**Returns:** `(is_valid, missing_fields)`

## Configuration

Set in `backend/app/config.py`:

```python
# LLM provider: "groq" or "gemini"
AI_ASSISTANT_LLM_PROVIDER = "groq"

# Timeout for LLM requests in seconds
AI_ASSISTANT_LLM_TIMEOUT = 10

# API keys
GROQ_API_KEY = "your_groq_api_key"
GEMINI_API_KEY = "your_gemini_api_key"  # Optional fallback
```

## Usage Example

```python
from app.services.ai_assistant import parse_intent

# Parse user message
message = "Add Mathematics on Monday 9-10 AM"
context = {"department_id": "uuid", "semester": 5}

result = await parse_intent(message, context)

print(result["intent"])  # "add"
print(result["parameters"]["subject"])  # "Mathematics"
print(result["parameters"]["day_of_week"])  # "Monday"
print(result["parameters"]["start_time"])  # "09:00"
print(result["parameters"]["end_time"])  # "10:00"
```

## Error Handling

### Timeout Handling
- Configurable timeout (default: 10 seconds)
- Raises `TimeoutError` when timeout exceeded
- Automatic fallback to secondary provider

### API Error Handling
- HTTP errors raise exceptions with status codes
- JSON parsing errors trigger fallback logic
- All errors logged with structured logging

### Fallback Strategy
1. Try primary provider (Groq)
2. On failure, try fallback provider (Gemini)
3. If both fail, raise exception with user-friendly message

## Testing

Run unit tests:
```bash
python -m pytest tests/test_ai_assistant_service.py -v
```

**Test Coverage:**
- Time string parsing (6 tests)
- Day name normalization (9 tests)
- Parameter validation (8 tests)
- Groq LLM calls (3 tests)
- Gemini LLM calls (1 test)
- Intent parsing with fallback (3 tests)
- System prompt validation (3 tests)

**Total: 33 tests, all passing**

## LLM System Prompt

The system prompt instructs the LLM to:
1. Extract structured information from natural language
2. Identify intent (add, update, delete, replace, query, help)
3. Parse parameters with specific rules:
   - Day names: Full capitalized format
   - Times: 24-hour HH:MM format
   - Semester: Integer 1-8
4. Return valid JSON with intent, parameters, missing_fields, confidence

## Requirements Coverage

This module satisfies the following requirements from the AI Admin Assistant spec:

- **Requirement 11.1**: Supports Groq LLM as primary provider
- **Requirement 11.2**: Falls back to Google Gemini when Groq unavailable
- **Requirement 11.3**: System prompt defines role and capabilities
- **Requirement 11.6**: Extracts intent and parameters (department, semester, day, time, subject, room, faculty)

## Next Steps

Task 3.2 will implement the intent parsing function that uses this module to process user messages and extract structured data for operation execution.
