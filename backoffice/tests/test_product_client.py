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
