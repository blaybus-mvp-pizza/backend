from fastapi.testclient import TestClient
from app.core.config import settings


API = settings.API_V1_STR


def assert_page_shape(resp_json):
    assert isinstance(resp_json, dict)
    assert set(["items", "page", "size", "total"]).issubset(resp_json.keys())
    assert isinstance(resp_json["items"], list)


def test_store_meta_and_products(client: TestClient):
    r = client.get(f"{API}/catalog/stores/2001/meta")
    assert r.status_code == 200
    meta = r.json()
    assert meta["store_id"] == 2001

    r2 = client.get(f"{API}/catalog/stores/2001/products?sort=latest&page=1&size=3")
    assert r2.status_code == 200
    assert_page_shape(r2.json())


def test_product_meta_auction_bids_similar(client: TestClient):
    r = client.get(f"{API}/catalog/products/3001/meta")
    assert r.status_code == 200
    r = client.get(f"{API}/catalog/products/3001/auction")
    assert r.status_code == 200
    r = client.get(f"{API}/catalog/products/3001/bids?page=1&size=2")
    assert r.status_code == 200
    assert_page_shape(r.json())
    r = client.get(f"{API}/catalog/products/3001/similar?page=1&size=2")
    assert r.status_code == 200
    assert_page_shape(r.json())

