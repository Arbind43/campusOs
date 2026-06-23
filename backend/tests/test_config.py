"""
Tests for configuration settings.
"""
import pytest
from app.config import settings


def test_config_loads():
    """Test that configuration loads without errors."""
    assert settings is not None


def test_ai_assistant_config_exists():
    """Test that AI Assistant configuration settings exist."""
    # Verify all AI Assistant settings are present
    assert hasattr(settings, "AI_ASSISTANT_LLM_PROVIDER")
    assert hasattr(settings, "AI_ASSISTANT_LLM_TIMEOUT")
    assert hasattr(settings, "AI_ASSISTANT_MAX_CONTEXT_LENGTH")
    assert hasattr(settings, "GROQ_API_KEY")
    assert hasattr(settings, "GEMINI_API_KEY")


def test_ai_assistant_default_values():
    """Test that AI Assistant settings have correct default values."""
    # Default provider should be groq
    assert settings.AI_ASSISTANT_LLM_PROVIDER == "groq"
    
    # Default timeout should be 10 seconds
    assert settings.AI_ASSISTANT_LLM_TIMEOUT == 10
    
    # Default max context length should be 10 messages
    assert settings.AI_ASSISTANT_MAX_CONTEXT_LENGTH == 10


def test_ai_assistant_timeout_is_positive():
    """Test that timeout is a positive integer."""
    assert isinstance(settings.AI_ASSISTANT_LLM_TIMEOUT, int)
    assert settings.AI_ASSISTANT_LLM_TIMEOUT > 0


def test_ai_assistant_max_context_is_positive():
    """Test that max context length is a positive integer."""
    assert isinstance(settings.AI_ASSISTANT_MAX_CONTEXT_LENGTH, int)
    assert settings.AI_ASSISTANT_MAX_CONTEXT_LENGTH > 0


def test_ai_assistant_provider_is_valid():
    """Test that LLM provider is a valid choice."""
    valid_providers = ["groq", "gemini"]
    assert settings.AI_ASSISTANT_LLM_PROVIDER in valid_providers


def test_groq_api_key_exists():
    """Test that GROQ_API_KEY setting exists (may be empty)."""
    assert hasattr(settings, "GROQ_API_KEY")
    assert isinstance(settings.GROQ_API_KEY, str)


def test_gemini_api_key_exists():
    """Test that GEMINI_API_KEY setting exists (may be empty)."""
    assert hasattr(settings, "GEMINI_API_KEY")
    assert isinstance(settings.GEMINI_API_KEY, str)
