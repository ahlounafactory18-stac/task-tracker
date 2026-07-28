"""Shared pytest fixtures for the Task Tracker API tests.

- ``reset_storage`` is autouse, so every test starts with an empty store and ids
  beginning at 1. Without this, tests would leak state into each other.
- ``client`` provides a FastAPI TestClient.
- ``created_task`` posts one task and returns its JSON, for tests that need an
  existing task to act on.
"""

import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset in-memory storage before and after every test."""
    storage._reset()
    yield
    storage._reset()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client bound to the app."""
    return TestClient(app)


@pytest.fixture
def created_task(client: TestClient) -> dict:
    """Create a single default task and return the response JSON."""
    response = client.post("/tasks", json={"title": "Sample task"})
    assert response.status_code == 201
    return response.json()
