#!/usr/bin/env python3

import os

import requests


# On the laptop, the Product API uses localhost:5001.
# Docker Compose can override this with the container's service address.
PRODUCT_API_URL = os.environ.get(
    "PRODUCT_API_URL",
    "http://localhost:5001",
)
TIMEOUT = 5


def get_product(identifier):
    """Return one product by numeric ID or SKU."""
    try:
        response = requests.get(
            f"{PRODUCT_API_URL}/api/v1/products/{identifier}",
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"could not reach Product API: {exc}")

    if response.status_code == 404:
        return None

    if response.status_code >= 400:
        raise RuntimeError(
            f"Product API error {response.status_code}"
        )

    return response.json()


def list_products():
    """Return every active product by requesting all API pages."""
    products = []
    offset = 0

    while True:
        try:
            response = requests.get(
                f"{PRODUCT_API_URL}/api/v1/products",
                params={
                    "offset": offset,
                    "limit": 50,
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"could not list products: {exc}")

        payload = response.json()
        results = payload["results"]

        if not results:
            return products

        products.extend(results)
        # Advance by how many results actually came back, not by the
        # reported "limit" - a misconfigured/misbehaving API reporting
        # limit=0 must not stall progress forever.
        offset += len(results)

        if offset >= payload["count"]:
            return products


def product_exists(product_id):
    """Return whether a product exists in the external catalogue."""
    return get_product(product_id) is not None
