import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import items


@pytest.fixture
def client():
    # Start every test with an empty store so tests don't affect each other.
    items.items_db.clear()
    items.next_id = 1
    return TestClient(app)
