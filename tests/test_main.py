"""
Tests for the Scholarship Recommendation API.
Run with:  pytest tests/ -v
"""
import pytest
from unittest.mock import patch, MagicMock
import torch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Mocks — patch heavy ML objects before importing the app so tests run fast
# without loading real .pkl files or GPU tensors.
# ---------------------------------------------------------------------------

MOCK_SCHOLARSHIPS = [
    "AI and Machine Learning Scholarship for Data Science students with CGPA above 3.5",
    "Need-based scholarship for students with family income below 30,000",
    "Networking and Cybersecurity Scholarship for students interested in security",
]

# 5 students × 3 scholarships, all scores identical for simplicity
MOCK_SIMILARITY = torch.tensor(
    [
        [0.90, 0.80, 0.70],
        [0.60, 0.95, 0.55],
        [0.75, 0.65, 0.85],
        [0.50, 0.88, 0.60],
        [0.82, 0.72, 0.78],
    ]
)


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with ML objects mocked out."""
    with (
        patch("builtins.open", MagicMock()),
        patch("pickle.load", side_effect=[
            MagicMock(),          # profile_embeddings
            MagicMock(),          # scholarship_embeddings
            MOCK_SCHOLARSHIPS,    # scholarships list
        ]),
        patch(
            "sentence_transformers.util.cos_sim",
            return_value=MOCK_SIMILARITY,
        ),
    ):
        from app.main import app
        yield TestClient(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["scholarships_loaded"] == 3


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

def test_home_returns_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Scholarship" in resp.text


# ---------------------------------------------------------------------------
# /recommend — happy paths
# ---------------------------------------------------------------------------

def test_recommend_high_cgpa_high_income(client):
    """Student with high CGPA and high income: CGPA scholarship passes, income one filtered."""
    resp = client.post(
        "/recommend",
        data={"student_index": 0, "cgpa": 3.8, "income": 50000},
    )
    assert resp.status_code == 200
    # CGPA scholarship should appear (score 0.90, cgpa ok)
    assert "AI and Machine Learning" in resp.text
    # Need-based scholarship must NOT appear (income > 30 000)
    assert "Need-based" not in resp.text


def test_recommend_low_cgpa_low_income(client):
    """Student with low CGPA and low income: income scholarship passes, CGPA one filtered."""
    resp = client.post(
        "/recommend",
        data={"student_index": 1, "cgpa": 3.0, "income": 20000},
    )
    assert resp.status_code == 200
    assert "Need-based" in resp.text
    assert "AI and Machine Learning" not in resp.text


def test_recommend_shows_student_profile(client):
    """Results page must echo back CGPA and income."""
    resp = client.post(
        "/recommend",
        data={"student_index": 2, "cgpa": 3.9, "income": 15000},
    )
    assert resp.status_code == 200
    assert "3.9" in resp.text
    assert "15000" in resp.text


# ---------------------------------------------------------------------------
# /recommend — edge cases & validation
# ---------------------------------------------------------------------------

def test_recommend_boundary_cgpa_exactly_35(client):
    """CGPA exactly 3.5 should NOT be filtered (condition is < 3.5)."""
    resp = client.post(
        "/recommend",
        data={"student_index": 0, "cgpa": 3.5, "income": 50000},
    )
    assert resp.status_code == 200
    assert "AI and Machine Learning" in resp.text


def test_recommend_boundary_income_exactly_30000(client):
    """Income exactly 30 000 should NOT be filtered (condition is > 30 000)."""
    resp = client.post(
        "/recommend",
        data={"student_index": 1, "cgpa": 2.9, "income": 30000},
    )
    assert resp.status_code == 200
    assert "Need-based" in resp.text


def test_recommend_missing_field_returns_422(client):
    """Missing a required form field must return 422 Unprocessable Entity."""
    resp = client.post(
        "/recommend",
        data={"student_index": 0, "cgpa": 3.5},  # income missing
    )
    assert resp.status_code == 422


def test_recommend_invalid_cgpa_type_returns_422(client):
    """Non-numeric CGPA must return 422."""
    resp = client.post(
        "/recommend",
        data={"student_index": 0, "cgpa": "abc", "income": 10000},
    )
    assert resp.status_code == 422
