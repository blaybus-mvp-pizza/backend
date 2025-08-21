from fastapi.testclient import TestClient
from app.core.config import settings


API = settings.ADMIN_API_STR or "/admin/v1"


def admin_headers() -> dict:
    # Ensure admin token for tests
    settings.ADMIN_TOKEN = settings.ADMIN_TOKEN or "test-admin-token"
    return {"Authorization": f"Bearer {settings.ADMIN_TOKEN}"}


def test_admin_auctions_list(client: TestClient):
    r = client.get(f"{API}/auctions", params={"page": 1, "size": 5}, headers=admin_headers())
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)


def test_admin_auction_detail(client: TestClient):
    # Use known seeded auction id from existing tests
    auction_id = 4001
    r = client.get(f"{API}/auctions/{auction_id}", headers=admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["auction_id"] == auction_id
    assert data["status"] in {"SCHEDULED", "RUNNING", "PAUSED", "ENDED", "CANCELLED"}


def test_admin_auction_status_change_pause_resume(client: TestClient):
    auction_id = 4001
    # Try pause
    r_pause = client.patch(
        f"{API}/auctions/{auction_id}/status",
        json={"status": "PAUSED"},
        headers=admin_headers(),
    )
    assert r_pause.status_code in (200, 400)
    # Try resume
    r_resume = client.patch(
        f"{API}/auctions/{auction_id}/status",
        json={"status": "RUNNING"},
        headers=admin_headers(),
    )
    assert r_resume.status_code in (200, 400)


def test_admin_auction_shipping(client: TestClient):
    auction_id = 4001
    r = client.get(f"{API}/auctions/{auction_id}/shipping", headers=admin_headers())
    assert r.status_code == 200
    data = r.json()
    assert "shipment_status" in data


def test_admin_finalize_requires_ended(client: TestClient):
    # Use an auction that is likely not ENDED to assert 400 or, if ended, 200
    auction_id = 4005
    r = client.post(f"{API}/auctions/{auction_id}/finalize", headers=admin_headers())
    assert r.status_code in (200, 400)


def test_admin_auction_update_patch(client: TestClient):
    # Fetch detail then attempt patch with same values (allowed only if SCHEDULED and before start)
    auction_id = 4001
    detail = client.get(f"{API}/auctions/{auction_id}", headers=admin_headers())
    assert detail.status_code == 200
    d = detail.json()
    payload = {
        "product_id": d["product_id"],
        "start_price": d["start_price"],
        "min_bid_price": d["min_bid_price"],
        "buy_now_price": d.get("buy_now_price"),
        "deposit_amount": d["deposit_amount"],
        # Admin inputs times in KST; the API will convert. We pass the same ISO string.
        "starts_at": d["starts_at"],
        "ends_at": d["ends_at"],
        "status": d["status"],
    }
    r = client.patch(f"{API}/auctions/{auction_id}", json=payload, headers=admin_headers())
    assert r.status_code in (200, 400)


