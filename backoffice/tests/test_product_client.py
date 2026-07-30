import pytest

from app.services import product_client


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_list_products_terminates_even_if_the_api_reports_limit_zero(monkeypatch):
    # A misbehaving/misconfigured Product API reporting limit=0 must not
    # hang the caller forever - pagination progress must be driven by how
    # many results actually came back, not by a possibly-wrong "limit"
    # field.
    calls = {"count": 0}

    def fake_get(url, params, timeout):
        calls["count"] += 1
        if calls["count"] > 10:
            raise RuntimeError("list_products looped more than 10 times - infinite loop")

        return _FakeResponse({
            "count": 3,
            "limit": 0,
            "results": [{"id": 1}, {"id": 2}, {"id": 3}],
        })

    monkeypatch.setattr(product_client.requests, "get", fake_get)

    result = product_client.list_products()

    assert len(result) == 3
    assert calls["count"] == 1


def test_list_products_forwards_the_category_filter_to_the_api(monkeypatch):
    seen_params = {}

    def fake_get(url, params, timeout):
        seen_params.update(params)
        return _FakeResponse({"count": 0, "limit": 50, "results": []})

    monkeypatch.setattr(product_client.requests, "get", fake_get)

    product_client.list_products(category="Laptops")

    assert seen_params["category"] == "Laptops"


def test_list_products_omits_the_category_param_when_not_given(monkeypatch):
    seen_params = {}

    def fake_get(url, params, timeout):
        seen_params.update(params)
        return _FakeResponse({"count": 0, "limit": 50, "results": []})

    monkeypatch.setattr(product_client.requests, "get", fake_get)

    product_client.list_products()

    assert "category" not in seen_params


def test_list_products_forwards_the_search_query_to_the_api(monkeypatch):
    seen_params = {}

    def fake_get(url, params, timeout):
        seen_params.update(params)
        return _FakeResponse({"count": 0, "limit": 50, "results": []})

    monkeypatch.setattr(product_client.requests, "get", fake_get)

    product_client.list_products(q="keyboard")

    assert seen_params["q"] == "keyboard"


def test_list_categories_returns_names_and_counts(monkeypatch):
    def fake_get(url, timeout):
        assert url.endswith("/api/v1/categories")
        return _FakeResponse({
            "count": 2,
            "results": [
                {"name": "Laptops", "product_count": 2},
                {"name": "Audio", "product_count": 1},
            ],
        })

    monkeypatch.setattr(product_client.requests, "get", fake_get)

    result = product_client.list_categories()

    assert result == [
        {"name": "Laptops", "product_count": 2},
        {"name": "Audio", "product_count": 1},
    ]
