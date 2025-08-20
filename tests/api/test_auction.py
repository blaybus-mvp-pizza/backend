from fastapi.testclient import TestClient
from app.core.config import settings


API = settings.API_V1_STR


def auth_header_for(user_id: int) -> dict:
    return {"Authorization": f"Bearer {user_id}"}


def test_bid_and_buy_now(client: TestClient):
    # missing auth
    r = client.post(f"{API}/auction/bid", params={"auction_id": 4001, "amount": 72000})
    assert r.status_code in (401, 403)

    # valid/authenticated
    r2 = client.post(
        f"{API}/auction/bid",
        params={"auction_id": 4001, "amount": 72000},
        headers=auth_header_for(1002),
    )
    assert r2.status_code in (200, 400)

    # buy-now allowed
    r3 = client.post(
        f"{API}/auction/buy-now",
        params={"auction_id": 4004},
        headers=auth_header_for(1001),
    )
    assert r3.status_code == 200

    # buy-now not allowed when no buy_now_price
    r4 = client.post(
        f"{API}/auction/buy-now",
        params={"auction_id": 4005},
        headers=auth_header_for(1001),
    )
    assert r4.status_code == 400

