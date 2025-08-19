from fastapi.testclient import TestClient
from app.core.config import settings


API = settings.API_V1_STR


def assert_page_shape(resp_json):
    assert isinstance(resp_json, dict)
    assert set(["items", "page", "size", "total"]).issubset(resp_json.keys())
    assert isinstance(resp_json["items"], list)


def test_products_feeds_and_pagination(client: TestClient):
    # ending soon default
    r = client.get(f"{API}/products/ending-soon")
    assert r.status_code == 200
    body = r.json()
    assert_page_shape(body)
    # recommended page 2 size 2
    r = client.get(f"{API}/products/recommended?page=2&size=2")
    assert r.status_code == 200
    assert_page_shape(r.json())
    # new with size=1
    r = client.get(f"{API}/products/new?size=1")
    assert r.status_code == 200
    body = r.json()
    assert_page_shape(body)
    assert len(body["items"]) <= 1


def test_recent_stores_with_products_and_store_list(client: TestClient):
    r = client.get(f"{API}/products/stores/recent?page=1&stores=2&size=2")
    assert r.status_code == 200
    body = r.json()
    assert_page_shape(body)
    items = body["items"]
    if items:
        first = items[0]
        assert "store" in first and "products" in first

    r2 = client.get(f"{API}/products/stores?page=1&size=2")
    assert r2.status_code == 200
    assert_page_shape(r2.json())

