"""
Unit tests for backend/services/price_service.py
Coverage target: ~90%
Mocks the DB session so no real DB is needed.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.price_service import calculate_price_service


def _make_hotel(id=1, name="Test Hotel"):
    h = MagicMock()
    h.id = id
    h.name = name
    return h


def _make_room(name="Standard", capacity=2, price=100.0):
    r = MagicMock()
    r.name = name
    r.capacity = capacity
    r.price_per_night = price
    return r


@pytest.fixture
def mock_db(db_with_hotel):
    """Patches SessionLocal to return the test SQLite session."""
    with patch("backend.services.price_service.SessionLocal") as mock_sl:
        mock_sl.return_value = db_with_hotel
        yield mock_sl


class TestCalculatePriceSuccess:
    def test_correct_total(self, mock_db):
        # 3 nights × £100 = £300
        result = calculate_price_service(1, "Standard", "2026-05-01", "2026-05-04", 2)
        assert result["success"] is True
        assert result["total_price"] == 300.0
        assert result["nights"] == 3
        assert result["price_per_night"] == 100.0
        assert result["currency"] == "GBP"

    def test_correct_hotel_and_room_info(self, mock_db):
        # Hotel and room names returned correctly
        result = calculate_price_service(1, "Standard", "2026-05-01", "2026-05-03", 1)
        assert result["hotel_name"] == "Test Grand Hotel"
        assert result["room_type"] == "Standard"

    def test_one_night(self, mock_db):
        # Single night stay calculates correctly
        result = calculate_price_service(1, "Standard", "2026-05-01", "2026-05-02", 1)
        assert result["success"] is True
        assert result["total_price"] == 100.0
        assert result["nights"] == 1

    def test_deluxe_room_price(self, mock_db):
        # Deluxe room uses correct price
        result = calculate_price_service(1, "Deluxe", "2026-05-01", "2026-05-03", 2)
        assert result["success"] is True
        assert result["total_price"] == 400.0  # 2 nights × £200

    def test_guests_within_capacity(self, mock_db):
        # Guests within room capacity passes
        result = calculate_price_service(1, "Deluxe", "2026-05-01", "2026-05-02", 3)
        assert result["success"] is True


class TestCalculatePriceFailures:
    def test_checkout_before_checkin(self, mock_db):
        # Checkout before checkin fails
        result = calculate_price_service(1, "Standard", "2026-05-05", "2026-05-01", 2)
        assert result["success"] is False
        assert "Check-out" in result["message"]

    def test_same_day_checkin_checkout(self, mock_db):
        # Same day checkin/checkout fails
        result = calculate_price_service(1, "Standard", "2026-05-01", "2026-05-01", 2)
        assert result["success"] is False

    def test_hotel_not_found(self, mock_db):
        # Unknown hotel ID returns error
        result = calculate_price_service(999, "Standard", "2026-05-01", "2026-05-03", 2)
        assert result["success"] is False
        assert "999" in result["message"]

    def test_room_type_not_found(self, mock_db):
        # Unknown room type lists available options
        result = calculate_price_service(1, "Presidential", "2026-05-01", "2026-05-03", 2)
        assert result["success"] is False
        assert "Presidential" in result["message"]
        assert "Standard" in result["message"] or "Deluxe" in result["message"]

    def test_guests_exceed_capacity(self, mock_db):
        # Too many guests for room capacity fails
        result = calculate_price_service(1, "Standard", "2026-05-01", "2026-05-03", 5)
        assert result["success"] is False
        assert "5" in result["message"]
