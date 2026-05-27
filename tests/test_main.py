"""
Tests for the Scholarship Recommendation API.
Run with:  pytest tests/ -v
"""
import pickle
import sys
from unittest.mock import MagicMock, patch

import pytest
import torch

# ---------------------------------------------------------------------------
# Mocks — we patch only pickle.load so the real filesystem (templates, etc.)
# stays untouched.  A fresh module import is forced each time via sys.modules.
# ---------------------------------------------------------------------------

MOCK_SCHOLARSHIPS = [
    "AI and Machine Learning Scholarship for Data Science students with CGPA above 3.5",
    "Need-based scholarship for students with family income below 30,000",
    "Networking and Cybersecurity Scholarship for students interested in security",
]

MOCK_SIMILARITY = torch.tensor(
    [
        [0.90, 0.80, 0.70],
        [0.60, 0.95, 0.55],
        [0.75, 0.65, 0.85],
        [0.50, 0.88, 0.60],
        [0.82, 0.72, 0.78],
    ]
)

_pickle_call_count = 0

def _fake_pickle_load(f):
    global _pickle_call_count
    _pickle_call_count += 1
    if _pickle_call_count == 1:
        return MagicMock()           # profile_embeddings
    elif _pickle_call_count == 2:
        return MagicMock()           # scholarship_embeddings
    else:
        return MOCK_SCHOLARSHIPS     # scholarships list


@pytest.fixture(scope="module")
def client():
    global _pickle_call_count
    _pickle_call_count = 0

    # Remove cached module so patches apply cleanly
    for key in list(sys.modules.keys()):
        if "app.main" in key or key == "app":
            del sys.modules[key]

    with (
        patch("pickle.load", side_effect=_fake_pickle_load),
        patch(
            "sentence_transformers.util.cos_sim",
            return_value=MOCK_SIMILARITY,
        ),
    ):
        from fastapi.testclient import TestClient
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
    """High CGPA passes CGPA filter; high income blocks need-based scholarship."""
    resp = client.post(
        "/recommend",
        data={"student_index": 0, "cgpa": 3.8, "income": 50000},
    )
    assert resp.status_code == 200
    assert "AI and Machine Learning" in resp.text
    assert "Need-based" not in resp.text


def test_recommend_low_cgpa_low_income(client):
    """Low CGPA blocks CGPA scholarship; low income passes need-based one."""
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
    """CGPA exactly 3.5 should NOT be filtered (condition is cgpa < 3.5)."""
    resp = client.post(
        "/recommend",
        data={"student_index": 0, "cgpa": 3.5, "income": 50000},
    )
    assert resp.status_code == 200
    assert "AI and Machine Learning" in resp.text


def test_recommend_boundary_income_exactly_30000(client):
    """Income exactly 30 000 should NOT be filtered (condition is income > 30 000)."""
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
