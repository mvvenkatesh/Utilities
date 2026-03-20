from fastapi.testclient import TestClient
import pytest
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)

def test_signup(client, mocker):
    mock_db = mocker.MagicMock()
    mocker.patch('app.main.get_db', return_value=mock_db)
    mock_db.query().filter().first.return_value = None

    response = client.post("/signup", json={
        "email": "mv@gmail.com",
        "password": "password123",
        "role": "user",
        "address": "okc"
    })

    assert response.status_code == 200
    assert response.json() == {"message": "Person signed up successfully"}


