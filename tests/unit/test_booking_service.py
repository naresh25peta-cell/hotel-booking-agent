"""
Unit tests for backend/services/booking_service.py
Coverage target: ~85%
Patches SessionLocal and check_hotel_availability so no real DB needed.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.booking_service import create_booking_service


def _available_response(hotel_id=1, hotel_name="Test Grand Hotel"):
    return {
        "success": True,
        "hotel_id": hotel_id,
        "hotel_name": hotel_name,
        "location": "London",
        "rating": 4.5,
        "check_in": "2026-05-01",
        "check_out": "2026-05-04",
        "guests": 2,
        "available_room_types": [
            {
                "room_type_id": 1,
                "room_type": "Standard",
                "capacity": 2,
                "price_per_night": 100.0,
                "available_rooms": 3,
            },
            {
                "room_type_id": 2,
                "room_type": "Deluxe",
                "capacity": 3,
                "price_per_night": 200.0,
                "available_rooms": 1,
            },
        ],
    }


@pytest.fixture
def mock_deps(db_with_hotel):
    """Patches both SessionLocal and check_hotel_availability."""
    with patch("backend.services.booking_service.SessionLocal") as mock_sl, \
         patch("backend.services.booking_service.check_hotel_availability") as mock_avail:
        mock_sl.return_value = db_with_hotel
        mock_avail.return_value = _available_response()
        yield mock_sl, mock_avail


class TestCreateBookingSuccess:
    def test_returns_success_true(self, mock_deps):
        # Valid booking returns success
        result = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["success"] is True

    def test_returns_booking_reference(self, mock_deps):
        # Booking reference has BK- prefix
        result = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["booking_reference"].startswith("BK-")
        assert len(result["booking_reference"]) == 11  # BK- + 8 hex chars

    def test_correct_total_price(self, mock_deps):
        # 3 nights × £100 = £300
        result = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["total_price"] == 300.0

    def test_selects_specified_room_type(self, mock_deps):
        # Requested room type selected correctly
        result = create_booking_service(
            1, "2026-05-01", "2026-05-04", 2,
            "Alice", "alice@test.com", room_type="Deluxe"
        )
        assert result["success"] is True
        assert result["room_type"] == "Deluxe"
        assert result["booked_price_per_night"] == 200.0

    def test_selects_first_available_when_no_room_type(self, mock_deps):
        # First available room used as fallback
        result = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["room_type"] == "Standard"

    def test_payment_transaction_id_stored(self, mock_deps):
        # Payment transaction ID saved to booking
        result = create_booking_service(
            1, "2026-05-01", "2026-05-04", 2,
            "Alice", "alice@test.com",
            payment_transaction_id="TXN-ABC123456789"
        )
        assert result["payment_transaction_id"] == "TXN-ABC123456789"

    def test_currency_is_gbp(self, mock_deps):
        # Default currency is GBP
        result = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["currency"] == "GBP"

    def test_status_is_confirmed(self, mock_deps):
        # Booking status is confirmed
        result = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["status"] == "confirmed"

    def test_each_booking_has_unique_reference(self, mock_deps):
        # Every booking gets unique reference
        r1 = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        r2 = create_booking_service(1, "2026-05-05", "2026-05-08", 2, "Bob", "bob@test.com")
        assert r1["booking_reference"] != r2["booking_reference"]


class TestCreateBookingFailures:
    def test_hotel_not_found(self, mock_deps):
        # Unknown hotel ID returns error
        _, mock_avail = mock_deps
        mock_avail.return_value = {"success": False, "message": "Hotel with ID 999 not found."}
        result = create_booking_service(999, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["success"] is False
        assert "999" in result["message"]

    def test_no_rooms_available(self, mock_deps):
        # No available rooms returns error
        _, mock_avail = mock_deps
        mock_avail.return_value = {**_available_response(), "available_room_types": []}
        result = create_booking_service(1, "2026-05-01", "2026-05-04", 2, "Alice", "alice@test.com")
        assert result["success"] is False
        assert "No rooms available" in result["message"]

    def test_specified_room_type_not_available(self, mock_deps):
        # Unavailable room type returns error
        result = create_booking_service(
            1, "2026-05-01", "2026-05-04", 2,
            "Alice", "alice@test.com", room_type="Presidential"
        )
        assert result["success"] is False
        assert "Presidential" in result["message"]
