import os

import httpx
from mcp.server.fastmcp import FastMCP


PRODUCT_API_BASE_URL = os.environ.get(
    "PRODUCT_API_BASE_URL",
    "http://localhost:5001"
)

REQUEST_TIMEOUT = 10.0

mcp = FastMCP("hbntory-product-mcp")


# Fields kept in the list summary. Full detail comes from get_product_details.
SUMMARY_FIELDS = (
    "id",
    "sku",
    "name",
    "category",
    "brand",
    "unit_price",
    "currency",
    "discontinued",
)


def _summarize(product: dict) -> dict:
    """Build a trimmed summary dictionary for one product."""
    # .get() returns None for a missing key instead of raising KeyError.
    return {
        field: product.get(field)
        for field in SUMMARY_FIELDS
    }


@mcp.tool()
def list_products() -> dict:
    """List available products from the external Product API.

    Returns a trimmed summary per product (id, sku, name, category, brand,
    unit_price, currency, discontinued). Walks all pages so nothing is missed.
    """
    url = f"{PRODUCT_API_BASE_URL}/api/v1/products"
    all_products = []
    offset = 0

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        while True:
            response = client.get(url, params={"offset": offset})
            response.raise_for_status()
            data = response.json()

            for product in data["results"]:
                all_products.append(_summarize(product))

            if len(all_products) >= data["count"]:
                break

            offset += data["limit"]

    return {
        "count": len(all_products),
        "products": all_products,
    }