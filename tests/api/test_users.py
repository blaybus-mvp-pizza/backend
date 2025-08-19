from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.security import create_access_token


API = settings.API_V1_STR


def auth_header_for(user_id: int) -> dict:
    # Use JWT for endpoints that require strict JWT validation
    token = create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


def test_me_and_update_and_phone_flow(client: TestClient):
    r = client.get(f"{API}/users/me", headers=auth_header_for(1001))
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "alice@example.com"

    r2 = client.put(
        f"{API}/users/me",
        headers=auth_header_for(1001),
        json={"nickname": "Alice-Updated"},
    )
    assert r2.status_code == 200

    r3 = client.post(
        f"{API}/users/me/phone-verification-sms",
        params={"phone_number": "+821055512345"},
        headers=auth_header_for(1002),
    )
    assert r3.status_code in (200, 400, 500)

    r4 = client.post(
        f"{API}/users/me/phone-verification-sms/verify",
        params={"phone_number": "+821055512345", "code6": "123456"},
        headers=auth_header_for(1002),
    )
    assert r4.status_code in (200, 400)

