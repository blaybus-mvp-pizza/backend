from fastapi.testclient import TestClient
from app.core.config import settings


API = settings.API_V1_STR


def test_health_and_db(client: TestClient):
    r = client.get(f"{API}/health/")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

    r2 = client.get(f"{API}/db/metadata")
    assert r2.status_code == 200
    meta = r2.json()
    assert "version" in meta and "database" in meta and "tables" in meta

