"""
API Tests – Tests for the Smart Resource Allocation API.

Uses an in-memory SQLite database to avoid requiring PostgreSQL for tests.

Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from services.nlp_service import extract_from_text
from services.priority_service import compute_priority_score
from services.matching_service import find_best_volunteer
from models.need import Need, UrgencyLevel, NeedStatus
from models.volunteer import Volunteer
from models.user import User

# ── Test Database Setup (SQLite in-memory) ───────────────────────

SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable ARRAY emulation for SQLite (PostgreSQL ARRAY not supported)
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Handle SQLite not supporting ARRAY during table creation
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY
import sqlite3
import json

@compiles(ARRAY, 'sqlite')
def compile_array(element, compiler, **kw):
    return "VARCHAR"

# SQLite can't bind Python lists — serialize them as JSON strings
sqlite3.register_adapter(list, lambda l: json.dumps(l))
sqlite3.register_converter("VARCHAR", lambda b: json.loads(b.decode()) if b.startswith(b"[") else b.decode())


Base.metadata.create_all(bind=engine)

client = TestClient(app)


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_tables():
    """Clean all tables before each test."""
    db = TestSessionLocal()
    db.query(Need).delete()
    db.query(Volunteer).delete()
    db.query(User).delete()
    db.commit()
    db.close()
    yield


# ── Helper: register and login to get token ──────────────────────

def _register_user(email="test@example.com", password="testpass123", role="volunteer"):
    return client.post("/auth/register", json={
        "email": email, "password": password, "role": role,
    })


def _login_user(email="test@example.com", password="testpass123"):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json().get("access_token")


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── NLP Service Tests ────────────────────────────────────────────

class TestNLPService:
    """Tests for the NLP extraction service."""

    def test_extract_food_category(self):
        result = extract_from_text(
            "200 families need food rations and meals in Mumbai"
        )
        assert result["category"] == "food"
        assert result["people_affected"] == 200

    def test_extract_medical_category(self):
        result = extract_from_text(
            "Emergency medical assistance needed. 500 people injured."
        )
        assert result["category"] == "medical"
        assert result["people_affected"] == 500

    def test_extract_water_category(self):
        result = extract_from_text(
            "Clean drinking water needed for 300 villagers in Kathmandu"
        )
        assert result["category"] == "water"
        assert result["people_affected"] == 300

    def test_detect_high_urgency(self):
        result = extract_from_text(
            "Urgent: Critical food shortage. 1000 people affected."
        )
        assert result["urgency"] == "high"

    def test_detect_medium_urgency(self):
        result = extract_from_text(
            "Growing concern: 100 people soon need medical assistance."
        )
        assert result["urgency"] == "medium"

    def test_detect_low_urgency(self):
        result = extract_from_text(
            "A community of 50 people could use extra supplies."
        )
        assert result["urgency"] == "low"

    def test_extract_location(self):
        result = extract_from_text(
            "Shelter needed in Mumbai for 200 displaced families."
        )
        assert result["location"] is not None
        assert "mumbai" in result["location"].lower()


# ── Priority Service Tests ───────────────────────────────────────

class TestPriorityService:
    """Tests for the priority scoring engine."""

    def test_high_urgency_many_people_medical(self):
        score = compute_priority_score("high", 1000, "medical")
        assert score >= 80  # Should be very high

    def test_low_urgency_few_people(self):
        score = compute_priority_score("low", 10, "education")
        assert score <= 30  # Should be low

    def test_score_range(self):
        """All scores must be between 0 and 100."""
        for urgency in ("low", "medium", "high"):
            for people in (0, 50, 500, 5000):
                for category in ("food", "medical", "water", "general"):
                    score = compute_priority_score(urgency, people, category)
                    assert 0 <= score <= 100, f"Score {score} out of range"

    def test_higher_urgency_higher_score(self):
        low = compute_priority_score("low", 100, "food")
        med = compute_priority_score("medium", 100, "food")
        high = compute_priority_score("high", 100, "food")
        assert low < med < high

    def test_more_people_higher_score(self):
        few = compute_priority_score("medium", 10, "medical")
        many = compute_priority_score("medium", 500, "medical")
        assert few < many


# ── Matching Service Tests ───────────────────────────────────────

class TestMatchingService:
    """Tests for the volunteer matching engine."""

    def _make_need(self, **kwargs):
        defaults = {
            "id": 1, "raw_text": "test", "category": "medical",
            "urgency": UrgencyLevel.HIGH, "people_affected": 100,
            "location": "Mumbai", "latitude": 19.076, "longitude": 72.8777,
            "priority_score": 80.0, "status": NeedStatus.PENDING,
        }
        defaults.update(kwargs)
        need = Need()
        for k, v in defaults.items():
            setattr(need, k, v)
        return need

    def _make_volunteer(self, **kwargs):
        defaults = {
            "id": 1, "name": "Test Vol", "skills": ["medical", "first_aid"],
            "location": "Mumbai", "latitude": 19.08, "longitude": 72.88,
            "availability": True, "rating": 4.0,
        }
        defaults.update(kwargs)
        vol = Volunteer()
        for k, v in defaults.items():
            setattr(vol, k, v)
        return vol

    def test_match_returns_result(self):
        need = self._make_need()
        vols = [self._make_volunteer()]
        result = find_best_volunteer(need, vols)
        assert result is not None
        assert result["volunteer_id"] == 1

    def test_match_prefers_closer_volunteer(self):
        need = self._make_need(latitude=19.076, longitude=72.8777)
        near = self._make_volunteer(id=1, latitude=19.08, longitude=72.88, skills=["medical"])
        far = self._make_volunteer(id=2, latitude=28.70, longitude=77.10, skills=["medical"], name="Far Vol")
        result = find_best_volunteer(need, [near, far])
        assert result is not None
        assert result["volunteer_id"] == 1  # closer volunteer wins

    def test_unavailable_volunteer_excluded(self):
        need = self._make_need()
        vol = self._make_volunteer(availability=False)
        result = find_best_volunteer(need, [vol])
        assert result is None

    def test_no_volunteers_returns_none(self):
        need = self._make_need()
        result = find_best_volunteer(need, [])
        assert result is None


# ── API Endpoint Tests ───────────────────────────────────────────

class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    def test_health_check(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_upload_report(self):
        response = client.post("/api/upload-report", json={
            "raw_text": "Urgent: 300 families in Mumbai need clean drinking water and medical supplies immediately."
        })
        assert response.status_code == 201
        data = response.json()
        assert data["category"] in ("water", "medical")
        assert data["urgency"] == "high"
        assert data["people_affected"] == 300
        assert data["priority_score"] > 0
        assert data["status"] == "pending"

    def test_upload_report_validation(self):
        """Empty text should fail validation."""
        response = client.post("/api/upload-report", json={"raw_text": "short"})
        assert response.status_code == 422

    def test_list_needs(self):
        # Create a need first
        client.post("/api/upload-report", json={
            "raw_text": "200 people in Delhi need temporary shelter after flooding."
        })
        response = client.get("/api/needs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_needs_with_filter(self):
        client.post("/api/upload-report", json={
            "raw_text": "Urgent: 100 families need food rations in Kathmandu."
        })
        response = client.get("/api/needs", params={"urgency": "high"})
        assert response.status_code == 200

    def test_dashboard(self):
        client.post("/api/upload-report", json={
            "raw_text": "500 people in Kolkata need emergency medical assistance."
        })
        response = client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_needs" in data
        assert "high_priority_needs" in data
        assert "category_breakdown" in data
        assert data["total_needs"] >= 1


# ── Authentication Tests ─────────────────────────────────────────

class TestAuth:
    """Tests for registration, login, and JWT auth."""

    def test_register_success(self):
        resp = _register_user()
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["role"] == "volunteer"

    def test_register_duplicate_email(self):
        _register_user()
        resp = _register_user()
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_login_success(self):
        _register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com", "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "volunteer"

    def test_login_wrong_password(self):
        _register_user()
        resp = client.post("/auth/login", json={
            "email": "test@example.com", "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_get_me(self):
        _register_user()
        token = _login_user()
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_me_no_token(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401


# ── Admin RBAC Tests ─────────────────────────────────────────────

class TestAdminRBAC:
    """Tests for admin-only endpoints."""

    def _setup_admin_and_volunteer(self):
        """Create admin user, volunteer user, and a volunteer record."""
        _register_user(email="admin@example.com", password="adminpass", role="admin")
        _register_user(email="vol@example.com", password="volpass", role="volunteer")

        # Add a volunteer record
        client.post("/api/add-volunteer", json={
            "name": "Test Volunteer",
            "skills": ["medical"],
            "location": "Mumbai",
            "latitude": 19.076,
            "longitude": 72.8777,
        })

        admin_token = _login_user(email="admin@example.com", password="adminpass")
        vol_token = _login_user(email="vol@example.com", password="volpass")
        return admin_token, vol_token

    def test_admin_can_update_volunteer(self):
        admin_token, _ = self._setup_admin_and_volunteer()
        # Get volunteer ID
        vols = client.get("/api/volunteers").json()
        vol_id = vols[0]["id"]

        resp = client.put(f"/api/volunteer/{vol_id}", json={
            "email": "updated@example.com",
            "availability": False,
        }, headers=_auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "updated@example.com"
        assert resp.json()["availability"] is False

    def test_volunteer_cannot_update_volunteer(self):
        _, vol_token = self._setup_admin_and_volunteer()
        vols = client.get("/api/volunteers").json()
        vol_id = vols[0]["id"]

        resp = client.put(f"/api/volunteer/{vol_id}", json={
            "availability": False,
        }, headers=_auth_header(vol_token))
        assert resp.status_code == 403

    def test_admin_can_delete_volunteer(self):
        admin_token, _ = self._setup_admin_and_volunteer()
        vols = client.get("/api/volunteers").json()
        vol_id = vols[0]["id"]

        resp = client.delete(f"/api/volunteer/{vol_id}", headers=_auth_header(admin_token))
        assert resp.status_code == 204

    def test_volunteer_cannot_delete_volunteer(self):
        _, vol_token = self._setup_admin_and_volunteer()
        vols = client.get("/api/volunteers").json()
        vol_id = vols[0]["id"]

        resp = client.delete(f"/api/volunteer/{vol_id}", headers=_auth_header(vol_token))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_update(self):
        """No token → 401."""
        resp = client.put("/api/volunteer/1", json={"availability": False})
        assert resp.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

