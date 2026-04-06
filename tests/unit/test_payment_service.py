"""
Unit tests for backend/services/payment_service.py
Coverage target: ~95%
No DB, no LLM — pure logic tests.
"""
import pytest
from backend.services.payment_service import process_payment_service


class TestValidPayment:
    def test_returns_success_true(self):
        # Valid card returns success
        result = process_payment_service(150.0, "GBP", "4111111111111111", "John Smith")
        assert result["success"] is True

    def test_returns_transaction_id(self):
        # Transaction ID has TXN- prefix
        result = process_payment_service(150.0, "GBP", "4111111111111111", "John Smith")
        assert result["transaction_id"].startswith("TXN-")
        assert len(result["transaction_id"]) == 16  # TXN- + 12 hex chars

    def test_returns_correct_last4(self):
        # Last 4 digits extracted correctly
        result = process_payment_service(100.0, "GBP", "4111111111111111", "John Smith")
        assert result["card_last4"] == "1111"

    def test_returns_amount_and_currency(self):
        # Amount and currency stored correctly
        result = process_payment_service(250.0, "USD", "4111111111111111", "Jane Doe")
        assert result["amount"] == 250.0
        assert result["currency"] == "USD"

    def test_strips_spaces_from_card(self):
        # Spaces in card number removed
        result = process_payment_service(100.0, "GBP", "4111 1111 1111 1111", "John Smith")
        assert result["success"] is True
        assert result["card_last4"] == "1111"

    def test_strips_hyphens_from_card(self):
        # Hyphens in card number removed
        result = process_payment_service(100.0, "GBP", "4111-1111-1111-1111", "John Smith")
        assert result["success"] is True

    def test_minimum_13_digit_card(self):
        # 13-digit card is accepted
        result = process_payment_service(100.0, "GBP", "4111111111111", "John Smith")
        assert result["success"] is True

    def test_maximum_19_digit_card(self):
        # 19-digit card is accepted
        result = process_payment_service(100.0, "GBP", "4111111111111111111", "John Smith")
        assert result["success"] is True

    def test_cardholder_name_stripped(self):
        # Cardholder name whitespace trimmed
        result = process_payment_service(100.0, "GBP", "4111111111111111", "  Jane Doe  ")
        assert result["cardholder_name"] == "Jane Doe"

    def test_each_transaction_id_is_unique(self):
        # Every transaction gets unique ID
        r1 = process_payment_service(100.0, "GBP", "4111111111111111", "Alice")
        r2 = process_payment_service(100.0, "GBP", "4111111111111111", "Alice")
        assert r1["transaction_id"] != r2["transaction_id"]


class TestInvalidCard:
    def test_too_short_card(self):
        # Card under 13 digits rejected
        result = process_payment_service(100.0, "GBP", "123456789012", "John Smith")
        assert result["success"] is False
        assert "Invalid card" in result["message"]

    def test_too_long_card(self):
        # Card over 19 digits rejected
        result = process_payment_service(100.0, "GBP", "42345678901234567890", "John Smith")
        assert result["success"] is False
        assert "Invalid card" in result["message"]

    def test_non_numeric_card(self):
        # Letters-only card rejected
        result = process_payment_service(100.0, "GBP", "ABCDEFGHIJKLMN", "John Smith")
        assert result["success"] is False

    def test_empty_card(self):
        # Empty card number rejected
        result = process_payment_service(100.0, "GBP", "", "John Smith")
        assert result["success"] is False

    def test_card_with_letters_mixed(self):
        # Mixed letters and digits rejected
        result = process_payment_service(100.0, "GBP", "4111-ABCD-1111-1111", "John Smith")
        assert result["success"] is False


class TestInvalidCardholder:
    def test_empty_cardholder_name(self):
        # Empty cardholder name rejected
        result = process_payment_service(100.0, "GBP", "4111111111111111", "")
        assert result["success"] is False
        assert "Cardholder" in result["message"]

    def test_whitespace_only_name(self):
        # Whitespace-only name rejected
        result = process_payment_service(100.0, "GBP", "4111111111111111", "   ")
        assert result["success"] is False
