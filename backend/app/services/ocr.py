"""OCR and timetable parsing service using Groq API.
Falls back to mock parsing if API key is not configured.
"""
import base64
import json
import logging
import re
import time as time_module
import traceback
from datetime import time

from app.config import settings
from app.core.logging_config import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)

# ── Correct Groq vision model (instruct, not preview) ─────────────────────── #
_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ── Timeout & retry settings ──────────────────────────────────────────────── #
_OCR_TIMEOUT = 60   # seconds — vision models can be slow
_MAX_RETRIES = 1    # 1 retry = 2 total attempts


def _detect_mime(data: bytes) -> str:
    """Detect image MIME type from magic bytes so we always send the correct type."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # Default to JPEG as a safe fallback
    return "image/jpeg"


def _extract_json(text: str) -> dict | None:
    """
    Robustly extract the first JSON object from a string.
    Handles markdown code fences and bare JSON.
    Uses a balanced-brace walk so nested objects don't trip the regex.
    """
    # 1. Strip markdown code fence if present
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence_match:
        candidate = fence_match.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass  # fall through to balanced walk

    # 2. Find the first '{' and walk to find balanced closing '}'
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False
    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return None

    return None


async def parse_timetable_image(file_content: bytes, max_retries: int = _MAX_RETRIES) -> dict:
    """
    Parse a timetable image using Groq API with vision capability.
    Returns extracted text and parsed entries.

    Args:
        file_content: Image bytes to parse
        max_retries: Maximum number of retry attempts (default: 1)

    Returns:
        dict with keys: success, extracted_text, entries, errors
    """
    import asyncio

    start_time = time_module.time()

    # Log OCR request start
    structured_logger.info(
        "OCR parsing started",
        file_size_bytes=len(file_content),
        api_provider="Groq",
        model=_VISION_MODEL,
    )

    # Encode image to base64 and detect MIME type
    image_base64 = base64.standard_b64encode(file_content).decode("utf-8")
    mime_type = _detect_mime(file_content)

    if not settings.GROQ_API_KEY:
        structured_logger.info(
            "Using mock OCR parsing (API key not configured)",
            file_size_bytes=len(file_content),
        )
        return _mock_parse_response(image_base64)

    # Retry logic with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            result = await _call_groq_timetable_api(image_base64, mime_type, start_time)
            return result
        except TimeoutError as e:
            total_duration = time_module.time() - start_time
            structured_logger.error(
                f"OCR extraction timeout (attempt {attempt + 1}/{max_retries + 1})",
                exception_type=type(e).__name__,
                exception_message=str(e),
                total_duration_seconds=round(total_duration, 3),
                timeout_limit_seconds=_OCR_TIMEOUT,
                stack_trace=traceback.format_exc(),
            )
            if attempt < max_retries:
                backoff_time = 2 ** attempt
                structured_logger.info(f"Retrying after {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)
            else:
                return {
                    "success": False,
                    "extracted_text": "",
                    "entries": [],
                    "errors": [
                        f"OCR extraction timeout after {max_retries + 1} attempts: "
                        f"The request exceeded {_OCR_TIMEOUT} seconds"
                    ],
                }
        except Exception as e:
            total_duration = time_module.time() - start_time
            structured_logger.error(
                f"OCR parsing failed (attempt {attempt + 1}/{max_retries + 1})",
                exception_type=type(e).__name__,
                exception_message=str(e),
                total_duration_seconds=round(total_duration, 3),
                stack_trace=traceback.format_exc(),
            )
            if attempt < max_retries:
                backoff_time = 2 ** attempt
                structured_logger.info(f"Retrying after {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)
            else:
                return {
                    "success": False,
                    "extracted_text": "",
                    "entries": [],
                    "errors": [f"OCR parsing failed after {max_retries + 1} attempts: {str(e)}"],
                }


async def _call_groq_timetable_api(image_base64: str, mime_type: str, start_time: float) -> dict:
    """
    Internal function to call Groq API for timetable OCR parsing.
    Raises exceptions on failure for retry logic.
    """
    import httpx

    api_start_time = time_module.time()

    structured_logger.info(
        "Sending request to Groq API",
        api_endpoint="https://api.groq.com/openai/v1/chat/completions",
        model=_VISION_MODEL,
    )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # Optimized prompt with explicit JSON structure, examples, and edge case handling
    prompt = """You are a timetable extraction expert. Extract ALL class schedule information from this image.

**CRITICAL RULES:**
1. Return ONLY a valid JSON object - NO markdown, NO explanations
2. Extract EVERY class you can find, even if some information is missing
3. If you can see ANY schedule-related text (times, subjects, days), extract it
4. Be flexible with formats - handle tables, lists, handwritten text, photos of whiteboards
5. If text is unclear, make your best guess based on context

**JSON FORMAT (required):**
{
    "extracted_text": "ALL text you can see in the image",
    "entries": [
        {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:30",
            "subject": "Subject Name",
            "room": "Room",
            "faculty_name": "Teacher",
            "semester": 1
        }
    ]
}

**EXTRACTION RULES:**
- Days: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
- Times: Use 24-hour format (09:00, 14:30). Convert AM/PM if needed
- If only start time visible, estimate end time (+1.5 hours)
- If day spans multiple classes (Mon-Fri), create separate entries
- Extract partial data even if some fields are missing
- Semester: must be an INTEGER (1-8), default to 1 if not specified

**WHAT TO LOOK FOR:**
- Tables with days across top or side
- Lists like "Monday 9-10 Math Room 101"
- Handwritten schedules
- Whiteboard photos with class times
- ANY text containing days + times + subjects

**IF YOU FIND NOTHING:**
Return: {"extracted_text": "text in image", "entries": []}

Now extract from the image and return ONLY the JSON:"""

    payload = {
        "model": _VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}",
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
        "temperature": 0.1,  # Very low for deterministic JSON output
        "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=_OCR_TIMEOUT) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        api_duration = time_module.time() - api_start_time

        # Log API response timing
        structured_logger.info(
            "Groq API response received",
            api_response_time_seconds=round(api_duration, 3),
            status_code=response.status_code,
        )

        # Extract the text response
        text_content = result["choices"][0]["message"]["content"]

        # Try to parse JSON from response using robust extractor
        parsed = _extract_json(text_content)

        if parsed:
            extracted_text = parsed.get("extracted_text", "")
            entries = parsed.get("entries", [])

            # Coerce semester to int if the model returned it as a string
            for entry in entries:
                sem = entry.get("semester", 1)
                try:
                    entry["semester"] = int(sem)
                except (TypeError, ValueError):
                    entry["semester"] = 1

            total_duration = time_module.time() - start_time

            structured_logger.info(
                "OCR parsing completed successfully",
                total_duration_seconds=round(total_duration, 3),
                entries_extracted=len(entries),
                extracted_text_length=len(extracted_text),
            )

            return {
                "success": True,
                "extracted_text": extracted_text,
                "entries": entries,
                "errors": [],
            }

        # Fallback: return raw text if JSON could not be parsed
        total_duration = time_module.time() - start_time

        structured_logger.warning(
            "OCR completed but could not parse structured data",
            total_duration_seconds=round(total_duration, 3),
            extracted_text_length=len(text_content),
            raw_response_preview=text_content[:300],
        )

        return {
            "success": True,
            "extracted_text": text_content,
            "entries": [],
            "errors": ["Could not parse structured data from response — please add entries manually"],
        }


def _mock_parse_response(image_b64: str) -> dict:
    """Mock response for demo without Groq API key."""
    return {
        "success": True,
        "extracted_text": "Mock timetable: Classes from Monday to Friday, 9am to 5pm",
        "entries": [
            {
                "day_of_week": "Monday",
                "start_time": "09:00",
                "end_time": "10:30",
                "subject": "Data Structures",
                "room": "A101",
                "faculty_name": "Dr. Smith",
                "semester": 1,
            },
            {
                "day_of_week": "Monday",
                "start_time": "11:00",
                "end_time": "12:30",
                "subject": "Web Development",
                "room": "B202",
                "faculty_name": "Prof. Johnson",
                "semester": 1,
            },
            {
                "day_of_week": "Tuesday",
                "start_time": "09:00",
                "end_time": "10:30",
                "subject": "Database Design",
                "room": "A101",
                "faculty_name": "Dr. Smith",
                "semester": 1,
            },
            {
                "day_of_week": "Wednesday",
                "start_time": "14:00",
                "end_time": "15:30",
                "subject": "AI & Machine Learning",
                "room": "C303",
                "faculty_name": "Dr. Patel",
                "semester": 1,
            },
            {
                "day_of_week": "Friday",
                "start_time": "10:00",
                "end_time": "11:30",
                "subject": "Software Engineering",
                "room": "D404",
                "faculty_name": "Prof. Chen",
                "semester": 1,
            },
        ],
        "errors": [],
    }


def parse_time(time_str: str) -> time:
    """Parse time string to time object."""
    if isinstance(time_str, time):
        return time_str
    try:
        # Handle HH:MM or HH:MM:SS format
        parts = str(time_str).strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return time(hour=hour, minute=minute)
    except (ValueError, IndexError):
        return time(9, 0)  # Default to 9 AM


# ── Mess menu parsing ─────────────────────────────────────────────────────── #

async def parse_mess_image(file_content: bytes, max_retries: int = _MAX_RETRIES) -> dict:
    """
    Parse a mess menu image into structured meal entries using Groq Vision.
    Falls back to a mock weekly menu when GROQ_API_KEY is not configured.

    Returns dict: success, extracted_text, entries, errors
    Each entry: day_of_week, meal_type, start_time, end_time, items, is_special
    """
    import asyncio
    import httpx

    image_base64 = base64.standard_b64encode(file_content).decode("utf-8")
    mime_type = _detect_mime(file_content)

    if not settings.GROQ_API_KEY:
        return _mock_mess_response()

    prompt = """You are a mess/canteen menu extraction expert. Extract the weekly mess menu from this image.

**RULES:**
1. Return ONLY a valid JSON object - NO markdown, NO explanations.
2. meal_type must be one of: breakfast, lunch, snacks, dinner
3. day_of_week: Monday..Sunday, or "Daily" if a meal is the same every day
4. Times in 24-hour HH:MM. If timings are not in the image, use null.
5. items = comma-separated dishes for that meal.
6. is_special = true only if explicitly marked as special/festive.

**JSON FORMAT:**
{
  "extracted_text": "all text seen",
  "entries": [
    {"day_of_week":"Monday","meal_type":"breakfast","start_time":"07:30","end_time":"09:00","items":"Idli, Sambar, Tea","is_special":false}
  ]
}

Return ONLY the JSON:"""

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=_OCR_TIMEOUT) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                text_content = response.json()["choices"][0]["message"]["content"]

            parsed = _extract_json(text_content)
            if not parsed:
                return {
                    "success": True,
                    "extracted_text": text_content,
                    "entries": [],
                    "errors": ["Could not parse menu from response — please add meals manually"],
                }

            return {
                "success": True,
                "extracted_text": parsed.get("extracted_text", ""),
                "entries": parsed.get("entries", []),
                "errors": [],
            }

        except Exception as e:  # noqa: BLE001
            last_error = e
            structured_logger.error(
                f"Mess OCR failed (attempt {attempt + 1}/{max_retries + 1})",
                exception_type=type(e).__name__,
                exception_message=str(e),
                stack_trace=traceback.format_exc(),
            )
            if attempt < max_retries:
                backoff_time = 2 ** attempt
                structured_logger.info(f"Retrying mess OCR after {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)

    return {
        "success": False,
        "extracted_text": "",
        "entries": [],
        "errors": [str(last_error) if last_error else "Unknown error"],
    }


def _mock_mess_response() -> dict:
    """Mock weekly mess menu for demos without an API key."""
    meals = [
        ("breakfast", "07:30", "09:00", "Idli, Sambar, Bread, Butter, Tea, Coffee"),
        ("lunch", "12:30", "14:00", "Rice, Dal, Roti, Mixed Veg, Curd, Salad"),
        ("snacks", "16:30", "17:30", "Samosa, Tea, Biscuits"),
        ("dinner", "19:30", "21:00", "Roti, Paneer Curry, Rice, Dal, Sweet"),
    ]
    entries = []
    for meal_type, start, end, items in meals:
        entries.append({
            "day_of_week": "Daily",
            "meal_type": meal_type,
            "start_time": start,
            "end_time": end,
            "items": items,
            "is_special": False,
        })
    return {
        "success": True,
        "extracted_text": "Mock weekly mess menu (no API key configured)",
        "entries": entries,
        "errors": [],
    }
