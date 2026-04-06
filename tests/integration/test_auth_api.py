"""
Integration tests for /auth/register and /auth/login endpoints.
Uses real FastAPI TestClient with an in-memory SQLite DB.
LLM/Langfuse calls are mocked so no external services needed.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def auth_client(db_with_hotel):
    """TestClient with DB overridden — patches LLM/Langfuse and bcrypt to avoid startup errors."""
    from fastapi.testclient import TestClient
    from backend.api.main import app
    from backend.db.database import get_db

    def override_get_db():
        yield db_with_hotel

    app.dependency_overrides[get_db] = override_get_db

    # Mock bcrypt — passlib is incompatible with bcrypt 4.x in this environment
    def _fake_hash(password):
        return f"hashed_{password}"

    def _fake_verify(password, hashed):
        return hashed == f"hashed_{password}"

    with patch("backend.api.main.hotel_agent"), \
         patch("backend.api.main.evaluate_response"), \
         patch("backend.api.main.trace_all"), \
         patch("backend.api.main.Langfuse"), \
         patch("backend.api.auth.pwd_context.hash", side_effect=_fake_hash), \
         patch("backend.api.auth.pwd_context.verify", side_effect=_fake_verify):
        client = TestClient(app, raise_server_exceptions=False)
        yield client

    app.dependency_overrides.clear()


class TestRegister:
    def test_register_new_user_returns_201(self, auth_client):
        # New user registration returns 201
        response = auth_client.post("/auth/register", json={
            "name": "Alice Smith",
            "email": "alice@test.com",
            "password": "SecurePass123",
        })
        assert response.status_code == 201
        assert "successful" in response.json()["message"].lower()

    def test_register_duplicate_email_returns_400(self, auth_client):
        # Duplicate email returns 400 error
        payload = {"name": "Alice", "email": "dup@test.com", "password": "pass123"}
        auth_client.post("/auth/register", json=payload)
        response = auth_client.post("/auth/register", json=payload)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_missing_fields_returns_422(self, auth_client):
        # Missing fields returns validation error
        response = auth_client.post("/auth/register", json={"name": "Alice"})
        assert response.status_code == 422


class TestLogin:
    def test_login_valid_credentials_returns_token(self, auth_client):
        # Valid login returns JWT token
        auth_client.post("/auth/register", json={
            "name": "Bob Jones", "email": "bob@test.com", "password": "MyPass99"
        })
        response = auth_client.post("/auth/login", json={
            "email": "bob@test.com", "password": "MyPass99"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_name"] == "Bob Jones"
        assert data["user_email"] == "bob@test.com"

    def test_login_wrong_password_returns_401(self, auth_client):
        # Wrong password returns 401
        auth_client.post("/auth/register", json={
            "name": "Carol", "email": "carol@test.com", "password": "correct"
        })
        response = auth_client.post("/auth/login", json={
            "email": "carol@test.com", "password": "wrong"
        })
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_login_unknown_email_returns_401(self, auth_client):
        # Unknown email returns 401
        response = auth_client.post("/auth/login", json={
            "email": "nobody@test.com", "password": "anything"
        })
        assert response.status_code == 401

    def test_login_missing_fields_returns_422(self, auth_client):
        # Missing fields returns validation error
        response = auth_client.post("/auth/login", json={"email": "bob@test.com"})
        assert response.status_code == 422

    def test_token_is_valid_jwt_string(self, auth_client):
        # JWT token has three dot segments
        auth_client.post("/auth/register", json={
            "name": "Dave", "email": "dave@test.com", "password": "pass"
        })
        response = auth_client.post("/auth/login", json={
            "email": "dave@test.com", "password": "pass"
        })
        token = response.json()["access_token"]
        assert token.count(".") == 2
