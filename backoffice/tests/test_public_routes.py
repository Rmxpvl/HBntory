from fastapi.testclient import TestClient

from app.main import app
from app.services import product_client


def test_public_products_does_not_require_authentication(monkeypatch):
    monkeypatch.setattr(
        product_client, "list_products", lambda category=None, q=None: [{"id": 1}]
    )

    client = TestClient(app, base_url="https://testserver")
    response = client.get("/api/public/products")

    assert response.status_code == 200
    assert response.json() == [{"id": 1}]


def test_public_products_forwards_the_category_query_param(monkeypatch):
    seen = {}

    def fake_list_products(category=None, q=None):
        seen["category"] = category
        return []

    monkeypatch.setattr(product_client, "list_products", fake_list_products)

    client = TestClient(app, base_url="https://testserver")
    client.get("/api/public/products", params={"category": "Laptops"})

    assert seen["category"] == "Laptops"


def test_public_products_forwards_the_search_query_param(monkeypatch):
    seen = {}

    def fake_list_products(category=None, q=None):
        seen["q"] = q
        return []

    monkeypatch.setattr(product_client, "list_products", fake_list_products)

    client = TestClient(app, base_url="https://testserver")
    client.get("/api/public/products", params={"q": "keyboard"})

    assert seen["q"] == "keyboard"


def test_public_products_surfaces_product_api_failures_as_502(monkeypatch):
    def fake_list_products(category=None, q=None):
        raise RuntimeError("could not reach Product API")

    monkeypatch.setattr(product_client, "list_products", fake_list_products)

    client = TestClient(app, base_url="https://testserver")
    response = client.get("/api/public/products")

    assert response.status_code == 502


def test_public_categories_does_not_require_authentication(monkeypatch):
    monkeypatch.setattr(
        product_client,
        "list_categories",
        lambda: [{"name": "Laptops", "product_count": 2}],
    )

    client = TestClient(app, base_url="https://testserver")
    response = client.get("/api/public/categories")

    assert response.status_code == 200
    assert response.json() == [{"name": "Laptops", "product_count": 2}]
