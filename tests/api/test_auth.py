from fastapi.testclient import TestClient
from app.core.config import settings


API = settings.API_V1_STR


def test_login_google_url(client: TestClient):
    r = client.get(f"{API}/auth/login/google/login-url")
    assert r.status_code == 200
    body = r.json()
    assert "login_url" in body

