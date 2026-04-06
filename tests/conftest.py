"""
Shared fixtures for unit and integration tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.db.database import Base, get_db
from backend.db.models import Hotel, RoomType, Booking
from backend.db.auth_models import User


# ── In-memory SQLite engine for all tests ─────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # all connections share the same in-memory DB
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Fresh in-memory DB per test — tables created, torn down after each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_with_hotel(db):
    """DB pre-populated with one hotel and two room types."""
    hotel = Hotel(
        id=1,
        name="Test Grand Hotel",
        location="London",
        amenities="WiFi, Pool",
        rating=4.5,
    )
    db.add(hotel)
    db.flush()

    standard = RoomType(
        id=1, hotel_id=hotel.id,
        name="Standard", capacity=2,
        price_per_night=100.0, total_rooms=5,
    )
    deluxe = RoomType(
        id=2, hotel_id=hotel.id,
        name="Deluxe", capacity=3,
        price_per_night=200.0, total_rooms=2,
    )
    db.add_all([standard, deluxe])
    db.commit()
    return db


@pytest.fixture(scope="function")
def api_client(db_with_hotel):
    """FastAPI TestClient with DB dependency overridden to use test DB."""
    from backend.api.main import app

    def override_get_db():
        try:
            yield db_with_hotel
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()
