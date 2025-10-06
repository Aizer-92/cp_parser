"""Tests for recommendation metadata exposure in API endpoints.

These tests lock the regression when category recommendations disappear from
the FastAPI responses and, consequently, from the Vue UI hints.
"""

from fastapi.testclient import TestClient
import pytest


# The application lives in the same directory; pytest adds the project root to
# sys.path, so we can import the module directly.
import app as app_module


class StubCalculator:
    """Lightweight calculator stub with deterministic recommendation data."""

    def __init__(self):
        self.categories = [
            {
                "category": "Тестовая категория",
                "material": "Пластик",
                "density": 215.0,
                "rates": {"rail_base": 5.0, "air_base": 8.5},
                "recommendations": {
                    "price_yuan_min": 10.0,
                    "price_yuan_max": 18.0,
                    "quantity_min": 120,
                    "quantity_max": 480,
                },
            }
        ]

    # FastAPI endpoints call into the real calculator through these methods.
    def find_category_by_name(self, product_name):  # pragma: no cover - trivial
        return self.categories[0]

    def get_recommendations(self, product_name):  # pragma: no cover - trivial
        return self.categories[0]["recommendations"]


@pytest.fixture(autouse=True)
def _override_auth(monkeypatch):
    """Disable authentication for the duration of each test."""

    app_module.app.dependency_overrides[app_module.require_auth] = lambda: True
    yield
    app_module.app.dependency_overrides.pop(app_module.require_auth, None)


@pytest.fixture
def client(monkeypatch):
    """Provide a test client wired to the stub calculator."""

    stub = StubCalculator()
    monkeypatch.setattr(app_module, "calculator", stub)
    monkeypatch.setattr(app_module, "get_calculator", lambda: stub)
    return TestClient(app_module.app)


def test_category_endpoint_exposes_recommendations(client):
    """`/api/category` must keep recommendation ranges for UI hints."""

    response = client.get("/api/category/любая_строка")
    assert response.status_code == 200

    payload = response.json()
    assert payload["category"] == "Тестовая категория"

    # Regression guard: the recommendations block used by the form hints
    # should travel all the way through the Pydantic model.
    assert "recommendations" in payload
    assert payload["recommendations"]["price_yuan_min"] == 10.0
    assert payload["recommendations"]["quantity_max"] == 480


def test_recommendations_endpoint_unchanged(client):
    """`/api/recommendations` still returns the extended payload."""

    response = client.get("/api/recommendations/что_угодно")
    assert response.status_code == 200

    payload = response.json()
    assert payload["category"] == "Тестовая категория"
    assert payload["recommendations"]["price_yuan_max"] == 18.0
    assert payload["recommendations"]["quantity_min"] == 120

