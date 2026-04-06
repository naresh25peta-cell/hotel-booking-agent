"""
Unit tests for backend/guardrails/output_guardrail.py
Coverage target: ~95%
Pure logic — no mocking needed.
"""
import pytest
from backend.guardrails.output_guardrail import sanitize_output, sanitize_error_message


class TestSanitizeOutputClean:
    def test_normal_response_passes_through(self):
        # Normal text passes unchanged
        text = "Here are the hotels in London."
        assert sanitize_output(text) == text

    def test_strips_leading_trailing_whitespace(self):
        # Whitespace trimmed from edges
        assert sanitize_output("  Hello  ") == "Hello"

    def test_booking_confirmation_passes(self):
        # Booking confirmation passes through
        text = "✅ Booking confirmed! Reference: BK-ABC12345"
        assert sanitize_output(text) == text


class TestSanitizeOutputBlocked:
    def test_empty_string_returns_fallback(self):
        # Empty string returns Sorry message
        result = sanitize_output("")
        assert "Sorry" in result

    def test_none_returns_fallback(self):
        # None returns Sorry message
        result = sanitize_output(None)
        assert "Sorry" in result

    def test_whitespace_only_returns_fallback(self):
        # Whitespace-only returns Sorry message
        result = sanitize_output("   ")
        assert "Sorry" in result

    def test_traceback_in_output_blocked(self):
        # Python traceback blocked from user
        result = sanitize_output("Traceback (most recent call last): File main.py")
        assert "Sorry" in result

    def test_sqlalchemy_error_blocked(self):
        # SQLAlchemy error blocked from user
        result = sanitize_output("sqlalchemy.exc.OperationalError: no such table")
        assert "Sorry" in result

    def test_langgraph_internals_blocked(self):
        # LangGraph internal error blocked
        result = sanitize_output("langgraph node execution failed")
        assert "Sorry" in result

    def test_api_key_blocked(self):
        # API key exposure blocked
        result = sanitize_output("api_key=sk-abc123 was leaked")
        assert "Sorry" in result

    def test_tool_calls_blocked(self):
        # Internal tool calls blocked from user
        result = sanitize_output("tool_calls: [{'name': 'search_hotels'}]")
        assert "Sorry" in result

    def test_system_prompt_blocked(self):
        # System prompt content blocked
        result = sanitize_output("Your system prompt is: You are a hotel assistant...")
        assert "Sorry" in result


class TestSanitizeOutputTruncation:
    def test_long_response_truncated(self):
        # Response over 4000 chars gets cut
        long_text = "A" * 4500
        result = sanitize_output(long_text)
        assert len(result) <= 4050
        assert "[response truncated]" in result

    def test_exactly_4000_chars_not_truncated(self):
        # Exactly 4000 chars not truncated
        text = "A" * 4000
        result = sanitize_output(text)
        assert "[response truncated]" not in result

    def test_4001_chars_truncated(self):
        # 4001 chars triggers truncation
        text = "A" * 4001
        result = sanitize_output(text)
        assert "[response truncated]" in result


class TestSanitizeErrorMessage:
    def test_always_returns_safe_message(self):
        # Raw error never shown to user
        result = sanitize_error_message(Exception("DB connection failed"))
        assert "Sorry" in result
        assert "DB connection" not in result

    def test_returns_string(self):
        # Always returns a string type
        result = sanitize_error_message(ValueError("anything"))
        assert isinstance(result, str)
