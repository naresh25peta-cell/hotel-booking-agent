"""
Integration tests for the /chat endpoint — full booking flow.
Simulates the multi-turn conversation: confirm → price → payment → booking done.
LLM and Langfuse are mocked; DB uses in-memory SQLite from conftest.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, ToolMessage

from backend.api.main import app
from backend.db.database import get_db


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ai(text: str) -> AIMessage:
    return AIMessage(content=text)


def _tool(text: str) -> ToolMessage:
    return ToolMessage(content=text, tool_call_id="mock-id")


def _base_result(**overrides) -> dict:
    base = {
        "messages": [],
        "intent": None,
        "selected_agent": None,
        "location": "London",
        "hotel_id": 1,
        "check_in": "2026-05-01",
        "check_out": "2026-05-04",
        "guests": 2,
        "room_type": "Standard",
        "sort_by_price": False,
        "missing_fields": [],
        "booking_step": "",
    }
    base.update(overrides)
    return base


@pytest.fixture
def client(db_with_hotel):
    def override_get_db():
        yield db_with_hotel

    app.dependency_overrides[get_db] = override_get_db

    with patch("backend.api.main.evaluate_response"), \
         patch("backend.api.main.trace_all"), \
         patch("backend.api.main.langfuse_context"), \
         patch("backend.api.main.propagate_attributes") as mock_prop:

        mock_prop.return_value.__enter__ = lambda s: s
        mock_prop.return_value.__exit__ = MagicMock(return_value=False)

        yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


# ── Confirm Booking (summary shown, awaiting yes/no) ──────────────────────────

class TestConfirmBookingIntent:
    def test_confirm_booking_shows_summary(self, client):
        # Booking intent shows confirm summary
        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[],
                intent="confirm_booking",
                selected_agent="response_agent",
            )
            response = client.post("/chat", json={
                "message": "I want to book hotel 1 from 2026-05-01 to 2026-05-04 for 2 guests",
                "user_name": "Alice Smith",
                "user_email": "alice@test.com",
                "session_id": "",
            })

        assert response.status_code == 200
        reply = response.json()["response"]
        assert "Hotel ID" in reply or "confirm" in reply.lower()
        assert "yes" in reply.lower() or "confirm" in reply.lower()

    def test_confirm_booking_summary_contains_dates(self, client):
        # Summary includes check-in check-out dates
        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[],
                intent="confirm_booking",
                selected_agent="response_agent",
            )
            response = client.post("/chat", json={
                "message": "book hotel 1 standard room 2026-05-01 to 2026-05-04 2 guests",
                "user_name": "Alice", "user_email": "alice@test.com", "session_id": "",
            })

        reply = response.json()["response"]
        assert "2026-05-01" in reply
        assert "2026-05-04" in reply

    def test_missing_hotel_id_asks_followup(self, client):
        # Missing hotel ID triggers followup
        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_ai("Which hotel would you like to book?")],
                intent="ask_followup",
                missing_fields=["hotel_id"],
                hotel_id=None,
                selected_agent="response_agent",
            )
            response = client.post("/chat", json={
                "message": "I want to book a room",
                "user_name": "Alice", "user_email": "alice@test.com", "session_id": "",
            })

        reply = response.json()["response"].lower()
        assert "hotel" in reply


# ── Booking State Machine Steps ────────────────────────────────────────────────

class TestBookingStateMachine:
    """
    Each test seeds the session's booking_step to simulate mid-flow state,
    then verifies the agent is called and the response is correct.
    """

    def _post(self, client, message: str, session_id: str) -> dict:
        return client.post("/chat", json={
            "message": message,
            "user_name": "Alice Smith",
            "user_email": "alice@test.com",
            "session_id": session_id,
        }).json()

    def test_step1_price_calculation(self, client):
        # Price calculated and step advances
        price_msg = (
            "💰 Price Breakdown:\n"
            "  Hotel      : Test Grand Hotel\n"
            "  Room       : Standard\n"
            "  Nights     : 3\n"
            "  Per night  : £100.00\n"
            "  Total      : £300.00 GBP\n"
        )
        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_ai(price_msg)],
                booking_step="price_shown",
                intent="create_booking",
            )
            response = client.post("/chat", json={
                "message": "yes",
                "user_name": "Alice Smith",
                "user_email": "alice@test.com",
                "session_id": "",
            })

        assert response.status_code == 200
        session_id = response.json()["session_id"]
        from backend.api.main import SESSION_STORE
        assert SESSION_STORE.get(session_id, {}).get("booking_step") == "price_shown"

    def test_step3_payment_processing(self, client):
        # Payment processed from awaiting_payment step
        payment_confirm = (
            "✅ Payment approved!\n"
            "  Transaction ID : TXN-ABC123456789\n"
            "  Amount charged : £300.00 GBP\n"
            "  Card ending    : ****1111\n"
            "  Cardholder     : Alice Smith"
        )
        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_ai(payment_confirm)],
                booking_step="payment_done",
            )
            import uuid
            session_id = str(uuid.uuid4())
            from backend.api.main import SESSION_STORE
            SESSION_STORE[session_id] = {
                "messages": [],
                "user_name": "Alice Smith",
                "user_email": "alice@test.com",
                "hotel_id": 1,
                "check_in": "2026-05-01",
                "check_out": "2026-05-04",
                "guests": 2,
                "room_type": "Standard",
                "location": "London",
                "booking_step": "awaiting_payment",
                "intent": None,
                "selected_agent": None,
                "missing_fields": [],
                "room_type_id": None,
                "payment_transaction_id": None,
                "sort_by_price": False,
            }
            response = client.post("/chat", json={
                "message": "4111 1111 1111 1111 Alice Smith",
                "user_name": "Alice Smith",
                "user_email": "alice@test.com",
                "session_id": session_id,
            })

        assert response.status_code == 200
        reply = response.json()["response"]
        assert reply != ""

    def test_step5_booking_confirmation(self, client):
        # Final confirmation shown after done step
        confirmation = (
            "🎉 Your booking is confirmed!\n"
            "  Booking Ref : BK-ABCD1234\n"
            "  Hotel       : Test Grand Hotel\n"
            "  Room        : Standard\n"
            "  Check-in    : 2026-05-01\n"
            "  Check-out   : 2026-05-04\n"
            "  Total       : £300.00 GBP\n"
            "  Transaction : TXN-ABC123456789\n"
        )
        import uuid
        session_id = str(uuid.uuid4())
        from backend.api.main import SESSION_STORE
        SESSION_STORE[session_id] = {
            "messages": [],
            "user_name": "Alice Smith",
            "user_email": "alice@test.com",
            "hotel_id": 1,
            "check_in": "2026-05-01",
            "check_out": "2026-05-04",
            "guests": 2,
            "room_type": "Standard",
            "location": "London",
            "booking_step": "done",
            "intent": None,
            "selected_agent": None,
            "missing_fields": [],
            "room_type_id": None,
            "payment_transaction_id": "TXN-ABC123456789",
            "sort_by_price": False,
        }
        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_ai(confirmation)],
                booking_step="",
            )
            response = client.post("/chat", json={
                "message": "confirm",
                "user_name": "Alice Smith",
                "user_email": "alice@test.com",
                "session_id": session_id,
            })

        assert response.status_code == 200
        reply = response.json()["response"]
        assert "BK-" in reply or "booking" in reply.lower() or "confirmed" in reply.lower()


# ── Session State Persistence ──────────────────────────────────────────────────

class TestSessionStatePersistence:
    def test_location_persists_across_turns(self, client):
        # Location saved in session store
        import uuid
        session_id = str(uuid.uuid4())

        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_tool("Hotels in London: ...")],
                intent="search_hotels",
                location="London",
            )
            client.post("/chat", json={
                "message": "find hotels in London",
                "user_name": "Alice", "user_email": "alice@test.com",
                "session_id": session_id,
            })

        from backend.api.main import SESSION_STORE
        assert SESSION_STORE[session_id]["location"] == "London"

    def test_hotel_id_persists_across_turns(self, client):
        # Hotel ID saved in session store
        import uuid
        session_id = str(uuid.uuid4())

        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_tool("Availability: Standard room available")],
                intent="check_availability",
                hotel_id=1,
            )
            client.post("/chat", json={
                "message": "check availability for hotel 1 from 2026-05-01 to 2026-05-04 for 2 guests",
                "user_name": "Alice", "user_email": "alice@test.com",
                "session_id": session_id,
            })

        from backend.api.main import SESSION_STORE
        assert SESSION_STORE[session_id]["hotel_id"] == 1

    def test_user_profile_updated_on_each_turn(self, client):
        # User name and email updated each turn
        import uuid
        session_id = str(uuid.uuid4())

        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_tool("Hotels in Paris...")],
                intent="search_hotels", location="Paris",
            )
            client.post("/chat", json={
                "message": "find hotels in Paris",
                "user_name": "Bob Jones",
                "user_email": "bob@test.com",
                "session_id": session_id,
            })

        from backend.api.main import SESSION_STORE
        assert SESSION_STORE[session_id]["user_name"] == "Bob Jones"
        assert SESSION_STORE[session_id]["user_email"] == "bob@test.com"


# ── Output Guardrail in Booking Flow ──────────────────────────────────────────

class TestBookingOutputGuardrail:
    def test_internal_error_in_booking_sanitized(self, client):
        # Traceback in booking response sanitized
        with patch("backend.api.main.hotel_agent") as mock_agent:
            mock_agent.invoke.return_value = _base_result(
                messages=[_ai("Traceback (most recent call last): langgraph error")],
                booking_step="price_shown",
            )
            import uuid
            session_id = str(uuid.uuid4())
            from backend.api.main import SESSION_STORE
            SESSION_STORE[session_id] = {
                "messages": [], "user_name": "Alice", "user_email": "alice@test.com",
                "hotel_id": 1, "check_in": "2026-05-01", "check_out": "2026-05-04",
                "guests": 2, "room_type": "Standard", "location": "London",
                "booking_step": "price_shown", "intent": None, "selected_agent": None,
                "missing_fields": [], "room_type_id": None,
                "payment_transaction_id": None, "sort_by_price": False,
            }
            response = client.post("/chat", json={
                "message": "my card is 4111111111111111 name Alice",
                "user_name": "Alice", "user_email": "alice@test.com",
                "session_id": session_id,
            })

        assert response.status_code == 200
        reply = response.json()["response"]
        assert "traceback" not in reply.lower()
        assert "Sorry" in reply
