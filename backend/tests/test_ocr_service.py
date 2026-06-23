"""Unit tests for OCR service."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ocr import parse_timetable_image, parse_time, _extract_json, _detect_mime, _VISION_MODEL
from datetime import time


class TestParseTime:
    """Test parse_time utility function."""

    def test_parse_valid_time(self):
        """Test parsing valid HH:MM format."""
        result = parse_time("09:30")
        assert result == time(9, 30)

    def test_parse_time_no_minutes(self):
        """Test parsing time with only hours."""
        result = parse_time("14:0")
        assert result == time(14, 0)

    def test_parse_invalid_time_returns_default(self):
        """Test that invalid time returns default 9:00."""
        result = parse_time("invalid")
        assert result == time(9, 0)

    def test_parse_time_object_returns_same(self):
        """Test that passing a time object returns it unchanged."""
        t = time(10, 30)
        result = parse_time(t)
        assert result == t

    def test_parse_hhmmss_format(self):
        """Test parsing HH:MM:SS format (as returned by the database)."""
        result = parse_time("14:30:00")
        assert result == time(14, 30)


class TestDetectMime:
    """Test MIME type detection from magic bytes."""

    def test_detect_png(self):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert _detect_mime(png_header) == "image/png"

    def test_detect_jpeg(self):
        jpeg_header = b"\xff\xd8\xff" + b"\x00" * 100
        assert _detect_mime(jpeg_header) == "image/jpeg"

    def test_detect_unknown_defaults_to_jpeg(self):
        assert _detect_mime(b"\x00\x00\x00\x00") == "image/jpeg"


class TestExtractJson:
    """Test robust JSON extraction helper."""

    def test_plain_json(self):
        text = '{"extracted_text": "hello", "entries": []}'
        result = _extract_json(text)
        assert result == {"extracted_text": "hello", "entries": []}

    def test_markdown_fenced_json(self):
        text = '```json\n{"extracted_text": "hi", "entries": []}\n```'
        result = _extract_json(text)
        assert result == {"extracted_text": "hi", "entries": []}

    def test_json_with_preamble(self):
        text = 'Here is the data:\n{"extracted_text": "ok", "entries": []}'
        result = _extract_json(text)
        assert result == {"extracted_text": "ok", "entries": []}

    def test_nested_json(self):
        text = '{"a": {"b": 1}, "c": [{"d": 2}]}'
        result = _extract_json(text)
        assert result == {"a": {"b": 1}, "c": [{"d": 2}]}

    def test_no_json_returns_none(self):
        result = _extract_json("No JSON here at all.")
        assert result is None


class TestParseTimetableImage:
    """Test parse_timetable_image function."""

    @pytest.mark.asyncio
    async def test_mock_response_when_no_api_key(self):
        """Test that mock response is returned when API key is not set."""
        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = None

            result = await parse_timetable_image(b"fake_image_data")

            assert result["success"] is True
            assert "Mock timetable" in result["extracted_text"]
            assert len(result["entries"]) > 0
            assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_successful_ocr_with_plain_json(self):
        """Test successful OCR extraction with plain JSON response."""
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": '{"extracted_text": "Sample timetable", "entries": [{"day_of_week": "Monday", "start_time": "09:00", "end_time": "10:00", "subject": "Math", "room": "A101", "faculty_name": "Dr. Smith", "semester": 1}]}'
                }
            }]
        }

        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            import httpx
            with patch.object(httpx, "AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()

                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                result = await parse_timetable_image(b"fake_image_data")

                assert result["success"] is True
                assert result["extracted_text"] == "Sample timetable"
                assert len(result["entries"]) == 1
                assert result["entries"][0]["subject"] == "Math"
                assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_successful_ocr_with_markdown_json(self):
        """Test successful OCR extraction with markdown-wrapped JSON response."""
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": '```json\n{"extracted_text": "Sample timetable", "entries": [{"day_of_week": "Tuesday", "start_time": "10:00", "end_time": "11:00", "subject": "Science", "room": "B202", "faculty_name": "Prof. Johnson", "semester": 1}]}\n```'
                }
            }]
        }

        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            import httpx
            with patch.object(httpx, "AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()

                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                result = await parse_timetable_image(b"fake_image_data")

                assert result["success"] is True
                assert result["extracted_text"] == "Sample timetable"
                assert len(result["entries"]) == 1
                assert result["entries"][0]["subject"] == "Science"
                assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_semester_string_coerced_to_int(self):
        """Test that semester returned as string by OCR is coerced to int."""
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": '{"extracted_text": "test", "entries": [{"day_of_week": "Monday", "start_time": "09:00", "end_time": "10:00", "subject": "Math", "semester": "3"}]}'
                }
            }]
        }

        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            import httpx
            with patch.object(httpx, "AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()

                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                result = await parse_timetable_image(b"fake_image_data")

                assert result["success"] is True
                assert result["entries"][0]["semester"] == 3
                assert isinstance(result["entries"][0]["semester"], int)

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test that timeout errors are properly handled and logged."""
        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            with patch("app.services.ocr._call_groq_timetable_api", new_callable=AsyncMock) as mock_call:
                mock_call.side_effect = TimeoutError("Request timed out")

                import asyncio
                with patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep:
                    result = await parse_timetable_image(b"fake_image_data", max_retries=1)

                    assert result["success"] is False
                    assert result["extracted_text"] == ""
                    assert result["entries"] == []
                    assert "timeout" in result["errors"][0].lower()
                    # Verify retry logic was called (1 retry = 1 sleep)
                    assert mock_sleep.call_count == 1
                    mock_sleep.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_general_exception_handling(self):
        """Test that general exceptions are properly handled and logged."""
        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            with patch("app.services.ocr._call_groq_timetable_api", new_callable=AsyncMock) as mock_call:
                mock_call.side_effect = Exception("API error occurred")

                import asyncio
                with patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep:
                    result = await parse_timetable_image(b"fake_image_data", max_retries=1)

                    assert result["success"] is False
                    assert result["extracted_text"] == ""
                    assert result["entries"] == []
                    assert "OCR parsing failed" in result["errors"][0]
                    # Verify retry logic was called (1 retry)
                    assert mock_sleep.call_count == 1

    @pytest.mark.asyncio
    async def test_correct_model_name_used(self):
        """Test that the correct Groq model name is used in the API call."""
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": '{"extracted_text": "test", "entries": []}'
                }
            }]
        }

        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            import httpx
            with patch.object(httpx, "AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()

                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                await parse_timetable_image(b"fake_image_data")

                # Verify the correct model name was used
                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                assert payload["model"] == _VISION_MODEL
                assert payload["model"] == "meta-llama/llama-4-scout-17b-16e-instruct"

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_initial_failure(self):
        """Test that retry logic succeeds after initial failure."""
        successful_response = {
            "choices": [{
                "message": {
                    "content": '{"extracted_text": "Retry success", "entries": []}'
                }
            }]
        }

        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            with patch("app.services.ocr._call_groq_timetable_api", new_callable=AsyncMock) as mock_call:
                mock_call.side_effect = [
                    Exception("First attempt failed"),
                    {
                        "success": True,
                        "extracted_text": "Retry success",
                        "entries": [],
                        "errors": []
                    }
                ]

                import asyncio
                with patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep:
                    result = await parse_timetable_image(b"fake_image_data", max_retries=1)

                    assert result["success"] is True
                    assert result["extracted_text"] == "Retry success"
                    assert result["errors"] == []
                    # Verify one retry happened with 1 second backoff
                    assert mock_sleep.call_count == 1
                    mock_sleep.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_temperature_lowered_for_deterministic_parsing(self):
        """Test that temperature is set low for deterministic JSON output."""
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": '{"extracted_text": "test", "entries": []}'
                }
            }]
        }

        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            import httpx
            with patch.object(httpx, "AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()

                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                await parse_timetable_image(b"fake_image_data")

                # Verify temperature is low (0.1)
                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                assert payload["temperature"] <= 0.3

    @pytest.mark.asyncio
    async def test_correct_mime_type_in_request(self):
        """Test that the correct MIME type is detected and sent to the API."""
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": '{"extracted_text": "test", "entries": []}'
                }
            }]
        }

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        with patch("app.services.ocr.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "test_key"

            import httpx
            with patch.object(httpx, "AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()

                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                await parse_timetable_image(png_data)

                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                image_url = payload["messages"][0]["content"][0]["image_url"]["url"]
                assert image_url.startswith("data:image/png;base64,")
