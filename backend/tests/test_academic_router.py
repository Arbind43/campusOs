"""Unit tests for academic router - timetable endpoints including authentication/authorization."""
import uuid
import pytest
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.routers.academic import confirm_timetable, upload_timetable_image
from app.models.academic import Timetable
from app.schemas.campus import TimetableConfirmRequest, TimetableUploadResponse


class TestConfirmTimetable:
    """Test confirm_timetable endpoint."""

    @pytest.fixture
    def mock_admin(self):
        """Create a mock admin user with department."""
        admin = MagicMock()
        admin.department_id = uuid.uuid4()
        admin.role = "ACADEMIC_ADMIN"
        return admin

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock(spec=AsyncSession)
        
        # Create a proper async context manager mock for begin_nested
        context_manager = AsyncMock()
        context_manager.__aenter__ = AsyncMock(return_value=None)
        context_manager.__aexit__ = AsyncMock(return_value=None)
        db.begin_nested = MagicMock(return_value=context_manager)
        
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def valid_entries(self):
        """Create valid timetable entries."""
        return [
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
                "day_of_week": "Tuesday",
                "start_time": "11:00",
                "end_time": "12:30",
                "subject": "Web Development",
                "room": "B202",
                "faculty_name": "Prof. Johnson",
                "semester": 1,
            },
        ]

    @pytest.mark.asyncio
    async def test_confirm_without_department_id_raises_error(self, mock_db):
        """Test that confirming without department_id raises 400 error."""
        admin = MagicMock()
        admin.department_id = None  # No department assigned
        
        body = TimetableConfirmRequest(entries=[{"day_of_week": "Monday", "start_time": "09:00", "end_time": "10:00", "subject": "Test"}])
        
        with pytest.raises(HTTPException) as exc_info:
            await confirm_timetable(body, admin, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "assigned to a department" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_confirm_with_empty_entries_raises_error(self, mock_admin, mock_db):
        """Test that confirming with empty entries raises validation error."""
        from pydantic import ValidationError
        
        # Pydantic schema validation should catch empty entries before endpoint code runs
        with pytest.raises(ValidationError) as exc_info:
            body = TimetableConfirmRequest(entries=[])
        
        assert "at least 1 item" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_confirm_successful_atomic_replacement(self, mock_admin, mock_db, valid_entries):
        """Test successful atomic replacement of timetable entries."""
        body = TimetableConfirmRequest(entries=valid_entries)
        
        # Mock the database operations
        created_entries = []
        def mock_add(entry):
            # Simulate database ID assignment
            entry.id = len(created_entries) + 1
            entry.created_at = datetime.now()
            created_entries.append(entry)
        
        mock_db.add.side_effect = mock_add
        
        result = await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify transaction was started
        mock_db.begin_nested.assert_called_once()
        
        # Verify timeout was set
        assert mock_db.execute.call_count >= 1
        first_call_args = mock_db.execute.call_args_list[0][0][0]
        assert "statement_timeout" in first_call_args.lower()
        assert "60s" in first_call_args
        
        # Verify DELETE was executed
        delete_call_found = False
        for call in mock_db.execute.call_args_list:
            arg = str(call[0][0])
            if "delete" in arg.lower():
                delete_call_found = True
                break
        assert delete_call_found, "DELETE statement should be executed"
        
        # Verify entries were added
        assert mock_db.add.call_count == len(valid_entries)
        
        # Verify flush and commit were called
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert isinstance(result, TimetableUploadResponse)
        assert result.success is True
        assert result.entries_created == len(valid_entries)
        assert len(result.entries) == len(valid_entries)
        assert "Successfully saved" in result.message

    @pytest.mark.asyncio
    async def test_confirm_skips_invalid_time_order(self, mock_admin, mock_db):
        """Test that entries with invalid time order (start >= end) are skipped."""
        invalid_entries = [
            {
                "day_of_week": "Monday",
                "start_time": "10:30",
                "end_time": "09:00",  # Invalid: end before start
                "subject": "Invalid Entry",
                "semester": 1,
            },
            {
                "day_of_week": "Tuesday",
                "start_time": "09:00",
                "end_time": "10:30",  # Valid entry
                "subject": "Valid Entry",
                "semester": 1,
            },
        ]
        
        body = TimetableConfirmRequest(entries=invalid_entries)
        
        created_entries = []
        def mock_add(entry):
            entry.id = len(created_entries) + 1
            entry.created_at = datetime.now()
            created_entries.append(entry)
        
        mock_db.add.side_effect = mock_add
        
        result = await confirm_timetable(body, mock_admin, mock_db)
        
        # Only one valid entry should be added
        assert mock_db.add.call_count == 1
        assert result.entries_created == 1
        assert result.entries[0].subject == "Valid Entry"

    @pytest.mark.asyncio
    async def test_confirm_handles_database_error_with_rollback(self, mock_admin, mock_db, valid_entries):
        """Test that database errors trigger rollback and return proper error message."""
        body = TimetableConfirmRequest(entries=valid_entries)
        
        # Simulate database error during commit
        mock_db.commit.side_effect = Exception("Database connection lost")
        
        with pytest.raises(HTTPException) as exc_info:
            await confirm_timetable(body, mock_admin, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Database transaction failed. No changes were saved."
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_includes_skipped_count_in_success_message(self, mock_admin, mock_db):
        """Test that success message includes skipped entry count when entries are skipped."""
        entries_with_invalid = [
            {
                "day_of_week": "Monday",
                "start_time": "09:00",
                "end_time": "10:30",
                "subject": "Valid Entry 1",
                "semester": 1,
            },
            {
                "day_of_week": "Tuesday",
                "start_time": "11:00",
                "end_time": "10:00",  # Invalid: end before start
                "subject": "Invalid Entry",
                "semester": 1,
            },
            {
                "day_of_week": "Wednesday",
                "start_time": "14:00",
                "end_time": "15:30",
                "subject": "Valid Entry 2",
                "semester": 1,
            },
            {
                "day_of_week": "Thursday",
                "start_time": "16:00",
                "end_time": "16:00",  # Invalid: start equals end
                "subject": "Invalid Entry 2",
                "semester": 1,
            },
        ]
        
        body = TimetableConfirmRequest(entries=entries_with_invalid)
        
        created_entries = []
        def mock_add(entry):
            entry.id = len(created_entries) + 1
            entry.created_at = datetime.now()
            created_entries.append(entry)
        
        mock_db.add.side_effect = mock_add
        
        result = await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify 2 valid entries were created and 2 were skipped
        assert result.entries_created == 2
        assert result.success is True
        assert "Successfully saved 2 timetable entries" in result.message
        assert "2 entries were skipped due to validation failures" in result.message

    @pytest.mark.asyncio
    async def test_confirm_success_message_without_skipped_entries(self, mock_admin, mock_db, valid_entries):
        """Test that success message does not mention skipped count when all entries are valid."""
        body = TimetableConfirmRequest(entries=valid_entries)
        
        created_entries = []
        def mock_add(entry):
            entry.id = len(created_entries) + 1
            entry.created_at = datetime.now()
            created_entries.append(entry)
        
        mock_db.add.side_effect = mock_add
        
        result = await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify success message does not mention skipped entries
        assert result.success is True
        assert "Successfully saved" in result.message
        assert "skipped" not in result.message.lower()

    @pytest.mark.asyncio
    async def test_confirm_parses_time_strings_correctly(self, mock_admin, mock_db):
        """Test that time strings are correctly parsed to time objects."""
        entries = [
            {
                "day_of_week": "Wednesday",
                "start_time": "14:45",
                "end_time": "16:15",
                "subject": "Advanced Programming",
                "semester": 2,
            }
        ]
        
        body = TimetableConfirmRequest(entries=entries)
        
        added_entry = None
        def mock_add(entry):
            nonlocal added_entry
            added_entry = entry
            entry.id = 1
            entry.created_at = datetime.now()
        
        mock_db.add.side_effect = mock_add
        
        await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify the added entry has correct time objects
        assert added_entry is not None
        assert added_entry.start_time == time(14, 45)
        assert added_entry.end_time == time(16, 15)

    @pytest.mark.asyncio
    async def test_confirm_assigns_department_id_to_entries(self, mock_admin, mock_db, valid_entries):
        """Test that all entries are assigned the admin's department_id."""
        body = TimetableConfirmRequest(entries=valid_entries)
        
        added_entries = []
        def mock_add(entry):
            entry.id = len(added_entries) + 1
            entry.created_at = datetime.now()
            added_entries.append(entry)
        
        mock_db.add.side_effect = mock_add
        
        await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify all entries have the admin's department_id
        for entry in added_entries:
            assert entry.department_id == mock_admin.department_id

    @pytest.mark.asyncio
    async def test_confirm_uses_default_semester_when_not_provided(self, mock_admin, mock_db):
        """Test that semester defaults to 1 when not provided."""
        entries = [
            {
                "day_of_week": "Friday",
                "start_time": "10:00",
                "end_time": "11:30",
                "subject": "Database Systems",
                # semester not provided
            }
        ]
        
        body = TimetableConfirmRequest(entries=entries)
        
        added_entry = None
        def mock_add(entry):
            nonlocal added_entry
            added_entry = entry
            entry.id = 1
            entry.created_at = datetime.now()
        
        mock_db.add.side_effect = mock_add
        
        await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify default semester is 1
        assert added_entry.semester == 1

    @pytest.mark.asyncio
    async def test_confirm_preserves_optional_fields(self, mock_admin, mock_db):
        """Test that optional fields (room, faculty_name) are preserved."""
        entries = [
            {
                "day_of_week": "Thursday",
                "start_time": "13:00",
                "end_time": "14:30",
                "subject": "Software Engineering",
                "room": "Lab-305",
                "faculty_name": "Dr. Kumar",
                "semester": 3,
            }
        ]
        
        body = TimetableConfirmRequest(entries=entries)
        
        added_entry = None
        def mock_add(entry):
            nonlocal added_entry
            added_entry = entry
            entry.id = 1
            entry.created_at = datetime.now()
        
        mock_db.add.side_effect = mock_add
        
        await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify optional fields are preserved
        assert added_entry.room == "Lab-305"
        assert added_entry.faculty_name == "Dr. Kumar"

    @pytest.mark.asyncio
    async def test_confirm_handles_missing_optional_fields(self, mock_admin, mock_db):
        """Test that missing optional fields are handled gracefully."""
        entries = [
            {
                "day_of_week": "Monday",
                "start_time": "08:00",
                "end_time": "09:30",
                "subject": "Mathematics",
                "semester": 1,
                # room and faculty_name not provided
            }
        ]
        
        body = TimetableConfirmRequest(entries=entries)
        
        added_entry = None
        def mock_add(entry):
            nonlocal added_entry
            added_entry = entry
            entry.id = 1
            entry.created_at = datetime.now()
        
        mock_db.add.side_effect = mock_add
        
        await confirm_timetable(body, mock_admin, mock_db)
        
        # Verify optional fields are None
        assert added_entry.room is None
        assert added_entry.faculty_name is None


class TestUploadTimetableImage:
    """Test upload_timetable_image endpoint - validation and error messages."""

    @pytest.fixture
    def mock_admin(self):
        """Create a mock admin user with department."""
        admin = MagicMock()
        admin.department_id = uuid.uuid4()
        admin.role = "ACADEMIC_ADMIN"
        return admin

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock(spec=AsyncSession)
        return db

    def create_upload_file(self, content: bytes, content_type: str, filename: str = "test.jpg"):
        """Helper to create a mock UploadFile."""
        file = MagicMock(spec=UploadFile)
        file.content_type = content_type
        file.filename = filename
        file.read = AsyncMock(return_value=content)
        return file

    @pytest.mark.asyncio
    async def test_upload_unsupported_file_format_returns_error(self, mock_admin, mock_db):
        """Test that unsupported file formats return the correct error message."""
        # Create a file with unsupported MIME type
        file = self.create_upload_file(b"fake image content", "image/gif", "test.gif")
        
        result = await upload_timetable_image(mock_admin, mock_db, file)
        
        assert result.success is False
        assert result.message == "Unsupported file format. Only JPEG and PNG images are allowed."
        assert "Unsupported file format. Only JPEG and PNG images are allowed." in result.errors

    @pytest.mark.asyncio
    async def test_upload_bmp_format_returns_error(self, mock_admin, mock_db):
        """Test that BMP format is rejected with correct error message."""
        file = self.create_upload_file(b"fake bmp content", "image/bmp", "test.bmp")
        
        result = await upload_timetable_image(mock_admin, mock_db, file)
        
        assert result.success is False
        assert result.message == "Unsupported file format. Only JPEG and PNG images are allowed."
        assert "Unsupported file format. Only JPEG and PNG images are allowed." in result.errors

    @pytest.mark.asyncio
    async def test_upload_oversized_file_returns_error(self, mock_admin, mock_db):
        """Test that files exceeding 10 MB return the correct error message."""
        # Create a file larger than 10 MB
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # 10 MB + 1 byte
        file = self.create_upload_file(large_content, "image/jpeg", "large.jpg")
        
        result = await upload_timetable_image(mock_admin, mock_db, file)
        
        assert result.success is False
        assert result.message == "File size exceeds the maximum limit of 10 MB"
        assert "File size exceeds the maximum limit of 10 MB" in result.errors

    @pytest.mark.asyncio
    async def test_upload_empty_file_returns_error(self, mock_admin, mock_db):
        """Test that empty files (0 bytes) return the correct error message."""
        file = self.create_upload_file(b"", "image/jpeg", "empty.jpg")
        
        result = await upload_timetable_image(mock_admin, mock_db, file)
        
        assert result.success is False
        assert result.message == "Uploaded file is empty"
        assert "Uploaded file is empty" in result.errors

    @pytest.mark.asyncio
    async def test_upload_without_department_id_returns_error(self, mock_db):
        """Test that admin without department_id returns the correct error message."""
        # Create admin without department
        admin = MagicMock()
        admin.department_id = None
        admin.role = "ACADEMIC_ADMIN"
        
        file = self.create_upload_file(b"valid jpeg content", "image/jpeg", "test.jpg")
        
        result = await upload_timetable_image(admin, mock_db, file)
        
        assert result.success is False
        assert result.message == "Department assignment is required for timetable upload"
        assert "Department assignment is required for timetable upload" in result.errors

    @pytest.mark.asyncio
    async def test_upload_jpeg_passes_validation(self, mock_admin, mock_db):
        """Test that JPEG files pass initial validation."""
        file = self.create_upload_file(b"valid jpeg content", "image/jpeg", "test.jpg")
        
        with patch('app.routers.academic.parse_timetable_image', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {
                "success": True,
                "extracted_text": "Sample timetable",
                "entries": [],
                "errors": []
            }
            
            result = await upload_timetable_image(mock_admin, mock_db, file)
            
            # Should not fail validation, should call OCR service
            mock_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_png_passes_validation(self, mock_admin, mock_db):
        """Test that PNG files pass initial validation."""
        file = self.create_upload_file(b"valid png content", "image/png", "test.png")
        
        with patch('app.routers.academic.parse_timetable_image', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {
                "success": True,
                "extracted_text": "Sample timetable",
                "entries": [],
                "errors": []
            }
            
            result = await upload_timetable_image(mock_admin, mock_db, file)
            
            # Should not fail validation, should call OCR service
            mock_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_max_size_file_passes_validation(self, mock_admin, mock_db):
        """Test that files exactly at 10 MB limit pass validation."""
        # Create a file exactly 10 MB
        max_content = b"x" * (10 * 1024 * 1024)
        file = self.create_upload_file(max_content, "image/jpeg", "max_size.jpg")
        
        with patch('app.routers.academic.parse_timetable_image', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {
                "success": True,
                "extracted_text": "Sample timetable",
                "entries": [],
                "errors": []
            }
            
            result = await upload_timetable_image(mock_admin, mock_db, file)
            
            # Should not fail validation
            mock_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_messages_are_consistent(self, mock_admin, mock_db):
        """Test that error messages in 'message' field match those in 'errors' array."""
        # Test unsupported format
        file = self.create_upload_file(b"content", "image/webp", "test.webp")
        result = await upload_timetable_image(mock_admin, mock_db, file)
        assert result.message in result.errors[0]
        
        # Test oversized file
        large_file = self.create_upload_file(b"x" * (11 * 1024 * 1024), "image/jpeg", "large.jpg")
        result = await upload_timetable_image(mock_admin, mock_db, large_file)
        assert result.message in result.errors[0]
        
        # Test empty file
        empty_file = self.create_upload_file(b"", "image/jpeg", "empty.jpg")
        result = await upload_timetable_image(mock_admin, mock_db, empty_file)
        assert result.message in result.errors[0]


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization for timetable endpoints."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock upload file."""
        file = MagicMock()
        file.content_type = "image/jpeg"
        file.read = AsyncMock(return_value=b"fake image data")
        return file
    
    @pytest.fixture
    def mock_admin_user(self):
        """Create a mock admin user with ACADEMIC_ADMIN role."""
        admin = MagicMock()
        admin.id = uuid.uuid4()
        admin.department_id = uuid.uuid4()
        admin.role = "ACADEMIC_ADMIN"
        admin.user_roles = []
        role_mock = MagicMock()
        role_mock.role.name = "ACADEMIC_ADMIN"
        admin.user_roles.append(role_mock)
        return admin
    
    @pytest.fixture
    def mock_super_admin_user(self):
        """Create a mock user with SUPER_ADMIN role."""
        admin = MagicMock()
        admin.id = uuid.uuid4()
        admin.department_id = uuid.uuid4()
        admin.role = "SUPER_ADMIN"
        admin.user_roles = []
        role_mock = MagicMock()
        role_mock.role.name = "SUPER_ADMIN"
        admin.user_roles.append(role_mock)
        return admin
    
    @pytest.fixture
    def mock_regular_user(self):
        """Create a mock regular user without admin roles."""
        user = MagicMock()
        user.id = uuid.uuid4()
        user.department_id = uuid.uuid4()
        user.role = "STUDENT"
        user.user_roles = []
        role_mock = MagicMock()
        role_mock.role.name = "STUDENT"
        user.user_roles.append(role_mock)
        return user
    
    @pytest.fixture
    def valid_entries(self):
        """Create valid timetable entries for confirm endpoint."""
        return [
            {
                "day_of_week": "Monday",
                "start_time": "09:00",
                "end_time": "10:30",
                "subject": "Data Structures",
                "semester": 1,
            }
        ]
    
    @pytest.mark.asyncio
    async def test_upload_endpoint_accepts_academic_admin(self, mock_admin_user, mock_db, mock_upload_file):
        """Test that upload endpoint accepts ACADEMIC_ADMIN role."""
        with patch('app.routers.academic.parse_timetable_image') as mock_parse:
            mock_parse.return_value = {
                "success": True,
                "extracted_text": "Sample text",
                "entries": [],
                "errors": []
            }
            
            # This should not raise an exception
            result = await upload_timetable_image(mock_admin_user, mock_db, mock_upload_file)
            
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_upload_endpoint_accepts_super_admin(self, mock_super_admin_user, mock_db, mock_upload_file):
        """Test that upload endpoint accepts SUPER_ADMIN role."""
        with patch('app.routers.academic.parse_timetable_image') as mock_parse:
            mock_parse.return_value = {
                "success": True,
                "extracted_text": "Sample text",
                "entries": [],
                "errors": []
            }
            
            # This should not raise an exception
            result = await upload_timetable_image(mock_super_admin_user, mock_db, mock_upload_file)
            
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_confirm_endpoint_accepts_academic_admin(self, mock_admin_user, valid_entries):
        """Test that confirm endpoint accepts ACADEMIC_ADMIN role."""
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Create async context manager mock
        context_manager = AsyncMock()
        context_manager.__aenter__ = AsyncMock(return_value=None)
        context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin_nested = MagicMock(return_value=context_manager)
        
        mock_db.execute = AsyncMock()
        
        created_entries = []
        def mock_add(entry):
            entry.id = len(created_entries) + 1
            entry.created_at = datetime.now()
            created_entries.append(entry)
        
        mock_db.add = mock_add
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        body = TimetableConfirmRequest(entries=valid_entries)
        
        # This should not raise an exception
        result = await confirm_timetable(body, mock_admin_user, mock_db)
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_confirm_endpoint_accepts_super_admin(self, mock_super_admin_user, valid_entries):
        """Test that confirm endpoint accepts SUPER_ADMIN role."""
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Create async context manager mock
        context_manager = AsyncMock()
        context_manager.__aenter__ = AsyncMock(return_value=None)
        context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin_nested = MagicMock(return_value=context_manager)
        
        mock_db.execute = AsyncMock()
        
        created_entries = []
        def mock_add(entry):
            entry.id = len(created_entries) + 1
            entry.created_at = datetime.now()
            created_entries.append(entry)
        
        mock_db.add = mock_add
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        body = TimetableConfirmRequest(entries=valid_entries)
        
        # This should not raise an exception
        result = await confirm_timetable(body, mock_super_admin_user, mock_db)
        
        assert result.success is True


class TestAuthenticationDependencies:
    """Test authentication and authorization at the dependency level.
    
    These tests verify that the dependencies correctly enforce authentication
    and authorization requirements per Requirements 1.5-1.7.
    """
    
    @pytest.mark.asyncio
    async def test_get_current_user_rejects_missing_credentials(self):
        """Test that get_current_user raises 401 when credentials are missing."""
        from app.dependencies import get_current_user
        
        mock_db = AsyncMock(spec=AsyncSession)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_rejects_invalid_token(self):
        """Test that get_current_user raises 401 when token is invalid."""
        from app.dependencies import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from jwt import PyJWTError
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.here"
        )
        
        with patch('app.dependencies.verify_supabase_token') as mock_verify:
            # Raise PyJWTError as expected by the code
            mock_verify.side_effect = PyJWTError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_require_role_rejects_insufficient_permissions(self):
        """Test that require_role raises 403 when user lacks required role."""
        from app.dependencies import require_role, get_user_role_names
        
        # Create a mock user with STUDENT role
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.role = "STUDENT"
        mock_user.user_roles = []
        role_mock = MagicMock()
        role_mock.role.name = "STUDENT"
        mock_user.user_roles.append(role_mock)
        
        # Get the dependency function for SUPER_ADMIN or ACADEMIC_ADMIN
        check_function = require_role("SUPER_ADMIN", "ACADEMIC_ADMIN")
        
        with pytest.raises(HTTPException) as exc_info:
            await check_function(mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "SUPER_ADMIN" in exc_info.value.detail or "ACADEMIC_ADMIN" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_role_accepts_matching_role(self):
        """Test that require_role accepts user with matching role."""
        from app.dependencies import require_role
        
        # Create a mock user with ACADEMIC_ADMIN role
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.role = "ACADEMIC_ADMIN"
        mock_user.user_roles = []
        role_mock = MagicMock()
        role_mock.role.name = "ACADEMIC_ADMIN"
        mock_user.user_roles.append(role_mock)
        
        # Get the dependency function
        check_function = require_role("SUPER_ADMIN", "ACADEMIC_ADMIN")
        
        # This should not raise an exception
        result = await check_function(mock_user)
        
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_academic_write_dependency_enforces_correct_roles(self):
        """Test that AcademicWrite dependency only accepts SUPER_ADMIN or ACADEMIC_ADMIN.
        
        This verifies Requirement 1.5: Upload_Endpoint SHALL require authentication 
        with role SUPER_ADMIN or role ACADEMIC_ADMIN.
        """
        from app.dependencies import require_role
        
        # Test with SUPER_ADMIN - should pass
        super_admin = MagicMock()
        super_admin.role = "SUPER_ADMIN"
        super_admin.user_roles = []
        role_mock = MagicMock()
        role_mock.role.name = "SUPER_ADMIN"
        super_admin.user_roles.append(role_mock)
        
        check_function = require_role("SUPER_ADMIN", "ACADEMIC_ADMIN")
        result = await check_function(super_admin)
        assert result == super_admin
        
        # Test with ACADEMIC_ADMIN - should pass
        academic_admin = MagicMock()
        academic_admin.role = "ACADEMIC_ADMIN"
        academic_admin.user_roles = []
        role_mock = MagicMock()
        role_mock.role.name = "ACADEMIC_ADMIN"
        academic_admin.user_roles.append(role_mock)
        
        result = await check_function(academic_admin)
        assert result == academic_admin
        
        # Test with other roles - should fail with 403
        for role_name in ["STUDENT", "FACULTY", "HOSTEL_ADMIN", "PLACEMENT_ADMIN"]:
            user = MagicMock()
            user.role = role_name
            user.user_roles = []
            role_mock = MagicMock()
            role_mock.role.name = role_name
            user.user_roles.append(role_mock)
            
            with pytest.raises(HTTPException) as exc_info:
                await check_function(user)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN, \
                f"Role {role_name} should be rejected with 403"
