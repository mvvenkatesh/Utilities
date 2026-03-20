from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock
from main import app
from app.router import get_db


@pytest.fixture
def client():
    return TestClient(app)

def test_signup(client):
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post("/signup", json={
        "email": "mv@gmail.com",
        "password": "password123",
        "role": "user",
        "address": "okc"
    })

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"message": "Person signed up successfully"}
    assert mock_db.add.called
    assert mock_db.commit.called

def test_signup_existing_email(client):
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = True

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post("/signup", json={
        "email": "existing@gmail.com",
        "password": "password123",
        "role": "user",
        "address": "okc"
    })

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}