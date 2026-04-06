"""
Unit tests for orchestrator_agent._post_validate_decision
Coverage target: ~90%
Tests the deterministic routing logic only — no LLM calls made.
"""
import pytest
from unittest.mock import MagicMock
from backend.agents.orchestrator_agent import _post_validate_decision


def _make_decision(**kwargs):
    """Build a mock RoutingDecision with sensible defaults."""
    d = MagicMock()
    d.intent = kwargs.get("intent", "search_hotels")
    d.location = kwargs.get("location", None)
    d.hotel_id = kwargs.get("hotel_id", None)
    d.check_in = kwargs.get("check_in", None)
    d.check_out = kwargs.get("check_out", None)
    d.guests = kwargs.get("guests", None)
    d.room_type = kwargs.get("room_type", None)
    d.sort_by_price = kwargs.get("sort_by_price", False)
    d.missing_fields = kwargs.get("missing_fields", [])
    return d


class TestSearchHotelsRouting:
    def test_search_with_location_routes_correctly(self):
        # Location present routes to search agent
        decision = _make_decision(intent="search_hotels", location="London")
        result = _post_validate_decision({}, decision)
        assert result["intent"] == "search_hotels"
        assert result["selected_agent"] == "search_availability_agent"

    def test_search_without_location_becomes_ask_followup(self):
        # Missing location triggers ask_followup
        decision = _make_decision(intent="search_hotels", location=None)
        result = _post_validate_decision({}, decision)
        assert result["intent"] == "ask_followup"
        assert "location" in result["missing_fields"]

    def test_search_uses_location_from_state(self):
        # Location from session state used
        decision = _make_decision(intent="search_hotels", location=None)
        state = {"location": "Paris"}
        result = _post_validate_decision(state, decision)
        assert result["intent"] == "search_hotels"
        assert result["location"] == "Paris"

    def test_sort_by_price_passed_through(self):
        # sort_by_price flag flows through correctly
        decision = _make_decision(intent="search_hotels", location="Dubai", sort_by_price=True)
        result = _post_validate_decision({}, decision)
        assert result["sort_by_price"] is True


class TestCheckAvailabilityRouting:
    def test_all_fields_present_routes_correctly(self):
        # All fields present routes correctly
        decision = _make_decision(
            intent="check_availability",
            hotel_id=1, check_in="2026-05-01",
            check_out="2026-05-05", guests=2,
        )
        result = _post_validate_decision({}, decision)
        assert result["intent"] == "check_availability"
        assert result["selected_agent"] == "search_availability_agent"

    def test_missing_hotel_id_becomes_ask_followup(self):
        # Missing hotel_id triggers ask_followup
        decision = _make_decision(
            intent="check_availability",
            hotel_id=None, check_in="2026-05-01",
            check_out="2026-05-05", guests=2,
        )
        result = _post_validate_decision({}, decision)
        assert result["intent"] == "ask_followup"
        assert "hotel_id" in result["missing_fields"]

    def test_missing_dates_and_guests_all_flagged(self):
        # All missing fields flagged together
        decision = _make_decision(
            intent="check_availability",
            hotel_id=1, check_in=None, check_out=None, guests=None,
        )
        result = _post_validate_decision({}, decision)
        assert result["intent"] == "ask_followup"
        assert "check_in" in result["missing_fields"]
        assert "check_out" in result["missing_fields"]
        assert "guests" in result["missing_fields"]

    def test_fields_filled_from_state(self):
        # Session state fills missing fields
        decision = _make_decision(
            intent="check_availability",
            hotel_id=None, check_in=None, check_out=None, guests=None,
        )
        state = {"hotel_id": 2, "check_in": "2026-06-01", "check_out": "2026-06-05", "guests": 2}
        result = _post_validate_decision(state, decision)
        assert result["intent"] == "check_availability"


class TestCreateBookingRouting:
    def _full_state(self):
        return {
            "hotel_id": 1, "check_in": "2026-05-01", "check_out": "2026-05-05",
            "guests": 2, "room_type": "Standard",
            "user_name": "Alice", "user_email": "alice@test.com",
        }

    def test_all_fields_present_routes_to_booking_agent(self):
        # All fields present routes to booking agent
        decision = _make_decision(
            intent="create_booking",
            hotel_id=1, check_in="2026-05-01", check_out="2026-05-05",
            guests=2, room_type="Standard",
        )
        state = {"user_name": "Alice", "user_email": "alice@test.com"}
        result = _post_validate_decision(state, decision)
        assert result["intent"] == "create_booking"
        assert result["selected_agent"] == "booking_agent"

    def test_missing_user_name_flagged(self):
        # Missing user_name triggers ask_followup
        decision = _make_decision(
            intent="create_booking",
            hotel_id=1, check_in="2026-05-01", check_out="2026-05-05",
            guests=2, room_type="Standard",
        )
        state = {"user_email": "alice@test.com"}
        result = _post_validate_decision(state, decision)
        assert result["intent"] == "ask_followup"
        assert "user_name" in result["missing_fields"]

    def test_missing_email_flagged(self):
        # Missing user_email triggers ask_followup
        decision = _make_decision(
            intent="create_booking",
            hotel_id=1, check_in="2026-05-01", check_out="2026-05-05",
            guests=2, room_type="Standard",
        )
        state = {"user_name": "Alice"}
        result = _post_validate_decision(state, decision)
        assert result["intent"] == "ask_followup"
        assert "user_email" in result["missing_fields"]


class TestRejectAndFollowupRouting:
    def test_reject_routes_to_response_agent(self):
        # Rejected request goes to response agent
        decision = _make_decision(intent="reject_request")
        result = _post_validate_decision({}, decision)
        assert result["selected_agent"] == "response_agent"

    def test_ask_followup_routes_to_response_agent(self):
        # Followup request goes to response agent
        decision = _make_decision(intent="ask_followup")
        result = _post_validate_decision({}, decision)
        assert result["selected_agent"] == "response_agent"

    def test_confirm_booking_routes_to_response_agent(self):
        # Booking confirmation goes to response agent
        decision = _make_decision(intent="confirm_booking")
        result = _post_validate_decision({}, decision)
        assert result["selected_agent"] == "response_agent"
