import os
import subprocess
import pathlib
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.config import settings
import pymysql


SEED_PATH = str(pathlib.Path(__file__).resolve().parents[1] / "integration_seed.sql")


def run_seed():
    db_url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    assert db_url and db_url.startswith(
        "mysql+pymysql://"
    ), "DATABASE_URL must be set (mysql+pymysql://...)"
    url = db_url[len("mysql+pymysql://") :]
    creds, host_db = url.split("@", 1)
    user, password = creds.split(":", 1)
    host_port, db = host_db.split("/", 1)
    if "?" in db:
        db = db.split("?", 1)[0]
    host, port = host_port.split(":", 1)

    with open(SEED_PATH, "r", encoding="utf-8") as f:
        sql_text = f.read()

    # Split on semicolons; keep statements that have non-whitespace
    # Split while keeping delimiters inside statements like PREPARE/EXECUTE
    statements = []
    buff = []
    for line in sql_text.splitlines():
        l = line.strip()
        if not l or l.startswith("--"):
            continue
        buff.append(line)
        # commit statements at the end of multi-line blocks where ';' appears
        # before any inline comment '--'
        check = l
        if "--" in check:
            check = check.split("--", 1)[0].rstrip()
        if check.endswith(";"):
            statements.append("\n".join(buff))
            buff = []
    if buff:
        statements.append("\n".join(buff))
    conn = pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=db,
        autocommit=True,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            for stmt in statements:
                try:
                    cur.execute(stmt)
                except pymysql.err.ProgrammingError as e:
                    if "Duplicate entry" in str(e):
                        continue
                    print("SEED STATEMENT FAILED:\n", stmt)
                    raise
    finally:
        conn.close()


API = settings.API_V1_STR


def make_auth_header(user_id: int) -> dict:
    # Use fallback supported in get_current_user_id: token can be the integer user id itself
    return {"Authorization": f"Bearer {user_id}"}


def make_jwt_header(user_id: int) -> dict:
    token = create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


client = TestClient(app)


def setup_module(_):
    run_seed()


def test_health():
    r = client.get(f"{API}/health/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_store_and_products_listing():
    # recent stores with products
    r = client.get(f"{API}/products/stores/recent")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert set(["items", "page", "size", "total"]).issubset(body.keys())
    assert isinstance(body["items"], list) and len(body["items"]) >= 1
    # store meta
    r2 = client.get(f"{API}/catalog/stores/2001/meta")
    assert r2.status_code == 200
    assert r2.json()["store_id"] == 2001
    # products by store (latest)
    r3 = client.get(f"{API}/catalog/stores/2001/products?sort=latest&page=1&size=10")
    assert r3.status_code == 200
    j = r3.json()
    assert isinstance(j, dict)
    assert set(["items", "page", "size", "total"]).issubset(j.keys())
    assert isinstance(j["items"], list)


def test_product_meta_and_auction_info():
    # product meta
    r = client.get(f"{API}/catalog/products/3001/meta")
    assert r.status_code == 200
    meta = r.json()
    assert meta["id"] == 3001
    assert len(meta["images"]) >= 1
    # auction info
    r2 = client.get(f"{API}/catalog/products/3001/auction")
    assert r2.status_code == 200
    info = r2.json()
    assert info["auction_id"] == 4001
    assert info["start_price"] == 50000.0


def test_list_bids_and_similar():
    r = client.get(f"{API}/catalog/products/3001/bids")
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j, dict)
    assert set(["items", "page", "size", "total"]).issubset(j.keys())
    assert isinstance(j["items"], list)
    r2 = client.get(f"{API}/catalog/products/3001/similar")
    assert r2.status_code == 200
    j2 = r2.json()
    assert isinstance(j2, dict)
    assert set(["items", "page", "size", "total"]).issubset(j2.keys())
    assert isinstance(j2["items"], list)


def test_place_bid_requires_auth_and_rules():
    # missing auth
    r = client.post(f"{API}/auction/bid", params={"auction_id": 4001, "amount": 72000})
    assert r.status_code in (401, 403)
    # valid bid with user 1002 (has deposit)
    r2 = client.post(
        f"{API}/auction/bid",
        params={"auction_id": 4001, "amount": 72000},
        headers=make_auth_header(1002),
    )
    assert r2.status_code in (200, 400)
    if r2.status_code == 200:
        body = r2.json()
        assert body["amount"] == 72000.0


def test_buy_now_flow_and_order_state():
    # buy now for auction 4004 (has buy_now_price)
    r = client.post(
        f"{API}/auction/buy-now",
        params={"auction_id": 4004},
        headers=make_auth_header(1001),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ORDER_PLACED"


def test_buy_now_not_allowed_when_no_buy_now_price():
    r = client.post(
        f"{API}/auction/buy-now",
        params={"auction_id": 4005},
        headers=make_auth_header(1001),
    )
    assert r.status_code == 400
    body = r.json()
    assert body.get("code") == "BUY_NOT_ALLOWED"


def test_payment_charge_and_refund():
    # charge arbitrary amount for user 1001
    r = client.post(
        f"{API}/payments/charge",
        json={"amount": 12345, "provider": "dummy"},
        headers=make_auth_header(1001),
    )
    assert r.status_code == 200
    pay = r.json()
    assert pay["status"] == "PAID"

    # refund existing seeded payment 6001
    r2 = client.post(
        f"{API}/payments/refund",
        json={"payment_id": 6001, "amount": 150000, "reason": "test refund"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "REFUNDED"


def test_users_me_and_update_and_phone_verification():
    # get me
    r = client.get(f"{API}/users/me", headers=make_jwt_header(1001))
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "alice@example.com"
    # request phone verification for bob (will fail without real SOLAPI keys)
    r2 = client.post(
        f"{API}/users/me/phone-verification-sms",
        params={"phone_number": "+821055512345"},
        headers=make_jwt_header(1002),
    )
    assert r2.status_code in (200, 400, 500)

    # verify using seeded code
    r3 = client.post(
        f"{API}/users/me/phone-verification-sms/verify",
        params={"phone_number": "+821055512345", "code6": "123456"},
        headers=make_jwt_header(1002),
    )
    assert r3.status_code in (200, 400)


