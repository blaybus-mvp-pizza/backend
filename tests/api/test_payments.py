from fastapi.testclient import TestClient
from app.core.config import settings


API = settings.API_V1_STR


def auth_header_for(user_id: int) -> dict:
    return {"Authorization": f"Bearer {user_id}"}


def test_charge_and_refund(client: TestClient):
    r = client.post(
        f"{API}/payments/charge",
        headers=auth_header_for(1001),
        json={"amount": 9999, "provider": "dummy"},
    )
    assert r.status_code == 200
    pay = r.json()
    assert pay["status"] == "PAID"

    r2 = client.post(
        f"{API}/payments/refund",
        json={"payment_id": 6001, "amount": 150000, "reason": "seed refund"},
    )
    assert r2.status_code == 200

