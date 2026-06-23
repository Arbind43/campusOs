"""
Unit tests for AI Assistant operation executor functions.

Tests the execute_add() and execute_query() functions that bridge
the AI assistant to the academic router endpoints.
"""
import uuid
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.services.ai_assistant import execute_add, execute_query


class TestExecuteAdd:
    """Test execute_add operation."""

    @pytest.mark.asyncio
    async def test_add_with_all_required_fields(self):
        """Test adding entry with all required fields."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        # Mock the database operations
        db.add = Mock()
        db.commit = AsyncMock()
        
        # Mock refresh to set id and created_at on the entry
        async def mock_refresh(entry):
            entry.id = 1
            entry.created_at = datetime.now()
        
        db.refresh = AsyncMock(side_effect=mock_refresh)
        
        parameters = {
            "department_id": dept_id,
            "semester": 5,
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        # Act
        result = await execute_add(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        assert result["operation_type"] == "add"
        assert result["affected_entries_count"] == 1
        assert len(result["entries"]) == 1
        assert result["error_message"] is None
        
        # Verify database operations were called
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_with_optional_fields(self):
        """Test adding entry with optional room and faculty fields."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        db.add = Mock()
        db.commit = AsyncMock()
        
        # Mock refresh to set id and created_at
        async def mock_refresh(entry):
            entry.id = 1
            entry.created_at = datetime.now()
        
        db.refresh = AsyncMock(side_effect=mock_refresh)
        
        parameters = {
            "department_id": dept_id,
            "semester": 5,
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
            "room": "101",
            "faculty_name": "Dr. Smith",
        }
        
        # Act
        result = await execute_add(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        assert result["affected_entries_count"] == 1
        db.add.assert_called_once()
        
        # Check that the timetable object has optional fields
        timetable_entry = db.add.call_args[0][0]
        assert timetable_entry.room == "101"
        assert timetable_entry.faculty_name == "Dr. Smith"

    @pytest.mark.asyncio
    async def test_add_with_invalid_time_format(self):
        """Test add operation fails with invalid time format."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        parameters = {
            "department_id": dept_id,
            "semester": 5,
            "day_of_week": "Monday",
            "start_time": "invalid",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        # Act
        result = await execute_add(parameters, admin, db)
        
        # Assert
        assert result["success"] is False
        assert result["affected_entries_count"] == 0
        assert "Validation error" in result["error_message"]
        assert len(result["entries"]) == 0

    @pytest.mark.asyncio
    async def test_add_with_database_error(self):
        """Test add operation handles database errors gracefully."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        db.add = Mock()
        db.commit = AsyncMock(side_effect=Exception("Database error"))
        db.rollback = AsyncMock()
        
        parameters = {
            "department_id": dept_id,
            "semester": 5,
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "subject": "Mathematics",
        }
        
        # Act
        result = await execute_add(parameters, admin, db)
        
        # Assert
        assert result["success"] is False
        assert result["affected_entries_count"] == 0
        assert "Failed to add entry" in result["error_message"]
        db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_parses_various_time_formats(self):
        """Test add operation parses different time string formats."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        db.add = Mock()
        db.commit = AsyncMock()
        
        # Mock refresh to set id and created_at
        async def mock_refresh(entry):
            entry.id = 1
            entry.created_at = datetime.now()
        
        db.refresh = AsyncMock(side_effect=mock_refresh)
        
        # Test different time formats
        test_cases = [
            ("09:00", "10:00"),  # HH:MM format
            ("9:00", "10:00"),   # H:MM format
            ("0900", "1000"),    # HHMM format
            ("9", "10"),         # H format
        ]
        
        for start_str, end_str in test_cases:
            parameters = {
                "department_id": dept_id,
                "semester": 5,
                "day_of_week": "Monday",
                "start_time": start_str,
                "end_time": end_str,
                "subject": "Mathematics",
            }
            
            # Act
            result = await execute_add(parameters, admin, db)
            
            # Assert
            assert result["success"] is True, f"Failed for time format: {start_str}-{end_str}"


class TestExecuteQuery:
    """Test execute_query operation."""

    @pytest.mark.asyncio
    async def test_query_with_no_filters(self):
        """Test querying all entries for admin's department."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        # Mock query execution
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        
        db.execute = AsyncMock(return_value=mock_result)
        
        parameters = {}
        
        # Act
        result = await execute_query(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        assert result["operation_type"] == "query"
        assert result["affected_entries_count"] == 0
        assert result["error_message"] is None
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_semester_filter(self):
        """Test querying entries filtered by semester."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        # Create mock timetable entries
        mock_entry_1 = Mock(
            id=1,
            department_id=dept_id,
            semester=5,
            day_of_week="Monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
            subject="Mathematics",
            room="101",
            faculty_name="Dr. Smith",
            created_at=datetime.now(),
        )
        mock_entry_2 = Mock(
            id=2,
            department_id=dept_id,
            semester=5,
            day_of_week="Tuesday",
            start_time=time(10, 0),
            end_time=time(11, 0),
            subject="Physics",
            room="102",
            faculty_name="Dr. Jones",
            created_at=datetime.now(),
        )
        
        # Mock query execution
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_entry_1, mock_entry_2]
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        
        db.execute = AsyncMock(return_value=mock_result)
        
        parameters = {
            "department_id": dept_id,
            "semester": 5,
        }
        
        # Act
        result = await execute_query(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        assert result["affected_entries_count"] == 2
        assert len(result["entries"]) == 2
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_day_filter(self):
        """Test querying entries filtered by day of week."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        mock_entry = Mock(
            id=1,
            department_id=dept_id,
            semester=5,
            day_of_week="Monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
            subject="Mathematics",
            room=None,
            faculty_name=None,
            created_at=datetime.now(),
        )
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_entry]
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        
        db.execute = AsyncMock(return_value=mock_result)
        
        parameters = {
            "day_of_week": "Monday",
        }
        
        # Act
        result = await execute_query(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        assert result["affected_entries_count"] == 1
        assert len(result["entries"]) == 1

    @pytest.mark.asyncio
    async def test_query_with_multiple_filters(self):
        """Test querying with semester and day filters combined."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        
        db.execute = AsyncMock(return_value=mock_result)
        
        parameters = {
            "semester": 5,
            "day_of_week": "Monday",
        }
        
        # Act
        result = await execute_query(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        assert result["operation_type"] == "query"
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_uses_admin_department_by_default(self):
        """Test query uses admin's department when not specified in parameters."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        
        db.execute = AsyncMock(return_value=mock_result)
        
        parameters = {}  # No department_id specified
        
        # Act
        result = await execute_query(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_database_error(self):
        """Test query operation handles database errors gracefully."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        db.execute = AsyncMock(side_effect=Exception("Database error"))
        
        parameters = {}
        
        # Act
        result = await execute_query(parameters, admin, db)
        
        # Assert
        assert result["success"] is False
        assert result["affected_entries_count"] == 0
        assert "Failed to query entries" in result["error_message"]

    @pytest.mark.asyncio
    async def test_query_returns_empty_list_when_no_matches(self):
        """Test query returns empty list when no entries match filters."""
        # Arrange
        dept_id = uuid.uuid4()
        admin = Mock(id=uuid.uuid4(), department_id=dept_id)
        db = AsyncMock()
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        
        db.execute = AsyncMock(return_value=mock_result)
        
        parameters = {
            "semester": 5,
            "day_of_week": "Sunday",  # Unlikely to have classes
        }
        
        # Act
        result = await execute_query(parameters, admin, db)
        
        # Assert
        assert result["success"] is True
        assert result["affected_entries_count"] == 0
        assert len(result["entries"]) == 0
        assert result["error_message"] is None
