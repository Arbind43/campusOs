"""Unit tests for AI Assistant schemas in campus.py"""
import uuid
import pytest
from pydantic import ValidationError

from app.schemas.campus import (
    ConversationContext,
    ChatRequest,
    ChatResponse,
    OperationResult,
    ParsedIntent,
    TimetableOut,
)
from datetime import datetime, time


class TestConversationContext:
    """Test ConversationContext schema."""

    def test_empty_context(self):
        """Test creating an empty context."""
        context = ConversationContext()
        assert context.department_id is None
        assert context.semester is None
        assert context.pending_operation is None

    def test_context_with_department(self):
        """Test context with department_id."""
        dept_id = uuid.uuid4()
        context = ConversationContext(department_id=dept_id)
        assert context.department_id == dept_id

    def test_context_with_valid_semester(self):
        """Test context with valid semester values."""
        for semester in range(1, 9):
            context = ConversationContext(semester=semester)
            assert context.semester == semester

    def test_context_with_invalid_semester_low(self):
        """Test context rejects semester < 1."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationContext(semester=0)
        assert "semester" in str(exc_info.value).lower()

    def test_context_with_invalid_semester_high(self):
        """Test context rejects semester > 8."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationContext(semester=9)
        assert "semester" in str(exc_info.value).lower()

    def test_context_with_pending_operation(self):
        """Test context with pending operation."""
        pending = {"intent": "add", "partial_params": {"subject": "Math"}}
        context = ConversationContext(pending_operation=pending)
        assert context.pending_operation == pending


class TestChatRequest:
    """Test ChatRequest schema."""

    def test_minimal_request(self):
        """Test creating a minimal chat request."""
        request = ChatRequest(message="Add a class")
        assert request.message == "Add a class"
        assert request.context.department_id is None

    def test_request_with_context(self):
        """Test request with conversation context."""
        dept_id = uuid.uuid4()
        context = ConversationContext(department_id=dept_id, semester=5)
        request = ChatRequest(message="Add Math", context=context)
        assert request.message == "Add Math"
        assert request.context.department_id == dept_id
        assert request.context.semester == 5

    def test_request_message_too_short(self):
        """Test request rejects empty message."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="")
        assert "message" in str(exc_info.value).lower()

    def test_request_message_too_long(self):
        """Test request rejects message > 500 chars."""
        long_message = "x" * 501
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message=long_message)
        assert "message" in str(exc_info.value).lower()

    def test_request_message_at_boundary(self):
        """Test request accepts message at 500 char boundary."""
        boundary_message = "x" * 500
        request = ChatRequest(message=boundary_message)
        assert len(request.message) == 500


class TestOperationResult:
    """Test OperationResult schema."""

    def test_successful_add_operation(self):
        """Test successful add operation result."""
        result = OperationResult(
            operation_type="add",
            success=True,
            affected_entries_count=1
        )
        assert result.operation_type == "add"
        assert result.success is True
        assert result.affected_entries_count == 1
        assert result.entries == []
        assert result.error_message is None

    def test_failed_operation_with_error(self):
        """Test failed operation with error message."""
        result = OperationResult(
            operation_type="delete",
            success=False,
            error_message="Entry not found"
        )
        assert result.success is False
        assert result.error_message == "Entry not found"

    def test_query_operation_with_entries(self):
        """Test query operation with returned entries."""
        # Create mock timetable entries
        entry = TimetableOut(
            id=1,
            department_id=uuid.uuid4(),
            semester=5,
            day_of_week="Monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
            subject="Mathematics",
            created_at=datetime.now()
        )
        
        result = OperationResult(
            operation_type="query",
            success=True,
            affected_entries_count=1,
            entries=[entry]
        )
        assert result.operation_type == "query"
        assert len(result.entries) == 1
        assert result.entries[0].subject == "Mathematics"

    def test_all_operation_types_valid(self):
        """Test all valid operation types."""
        valid_types = ["add", "update", "delete", "replace", "query"]
        for op_type in valid_types:
            result = OperationResult(operation_type=op_type, success=True)
            assert result.operation_type == op_type


class TestChatResponse:
    """Test ChatResponse schema."""

    def test_minimal_response(self):
        """Test creating a minimal chat response."""
        context = ConversationContext()
        response = ChatResponse(
            reply="What subject would you like to add?",
            context=context
        )
        assert response.reply == "What subject would you like to add?"
        assert response.action_taken is None
        assert response.requires_confirmation is False

    def test_response_with_action(self):
        """Test response with operation result."""
        context = ConversationContext(semester=5)
        action = OperationResult(
            operation_type="add",
            success=True,
            affected_entries_count=1
        )
        response = ChatResponse(
            reply="Successfully added Mathematics class.",
            context=context,
            action_taken=action
        )
        assert response.action_taken is not None
        assert response.action_taken.success is True

    def test_response_requiring_confirmation(self):
        """Test response requiring confirmation."""
        context = ConversationContext()
        response = ChatResponse(
            reply="Are you sure you want to delete this entry?",
            context=context,
            requires_confirmation=True
        )
        assert response.requires_confirmation is True

    def test_response_with_updated_context(self):
        """Test response updates context."""
        dept_id = uuid.uuid4()
        old_context = ConversationContext(semester=5)
        new_context = ConversationContext(department_id=dept_id, semester=5)
        
        response = ChatResponse(
            reply="Understood, using CSE department.",
            context=new_context
        )
        assert response.context.department_id == dept_id
        assert response.context.semester == 5


class TestParsedIntent:
    """Test ParsedIntent schema."""

    def test_add_intent_with_parameters(self):
        """Test parsed add intent."""
        intent = ParsedIntent(
            intent="add",
            parameters={
                "day_of_week": "Monday",
                "start_time": "09:00",
                "end_time": "10:00",
                "subject": "Mathematics"
            },
            missing_fields=[],
            confidence=0.95
        )
        assert intent.intent == "add"
        assert intent.parameters["subject"] == "Mathematics"
        assert len(intent.missing_fields) == 0
        assert intent.confidence == 0.95

    def test_intent_with_missing_fields(self):
        """Test intent with missing required fields."""
        intent = ParsedIntent(
            intent="add",
            parameters={"subject": "Physics"},
            missing_fields=["day_of_week", "start_time", "end_time"],
            confidence=0.8
        )
        assert len(intent.missing_fields) == 3
        assert "day_of_week" in intent.missing_fields

    def test_unclear_intent(self):
        """Test unclear intent classification."""
        intent = ParsedIntent(
            intent="unclear",
            parameters={},
            missing_fields=[],
            confidence=0.2
        )
        assert intent.intent == "unclear"
        assert intent.confidence == 0.2

    def test_confidence_boundary_values(self):
        """Test confidence value boundaries."""
        # Valid confidence values
        for conf in [0.0, 0.5, 1.0]:
            intent = ParsedIntent(
                intent="help",
                parameters={},
                missing_fields=[],
                confidence=conf
            )
            assert intent.confidence == conf

    def test_confidence_out_of_range_low(self):
        """Test confidence < 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ParsedIntent(
                intent="help",
                parameters={},
                missing_fields=[],
                confidence=-0.1
            )
        assert "confidence" in str(exc_info.value).lower()

    def test_confidence_out_of_range_high(self):
        """Test confidence > 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ParsedIntent(
                intent="help",
                parameters={},
                missing_fields=[],
                confidence=1.1
            )
        assert "confidence" in str(exc_info.value).lower()

    def test_all_intent_types_valid(self):
        """Test all valid intent types."""
        valid_intents = ["add", "update", "delete", "replace", "query", "help", "unclear"]
        for intent_type in valid_intents:
            intent = ParsedIntent(
                intent=intent_type,
                parameters={},
                missing_fields=[],
                confidence=0.9
            )
            assert intent.intent == intent_type
