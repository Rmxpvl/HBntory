import os
import httpx
from mcp.server.fastmcp import FastMCP

# Base URL of the external Product API (Docker container).
# Read from the environment so it isn't hard-coded; falls back to local dev.
PRODUCT_API_BASE_URL = os.environ.get("PRODUCT_API_BASE_URL", "http://localhost:5001")

# How long we wait for the Product API before giving up (seconds).
REQUEST_TIMEOUT = 10.0

mcp = FastMCP("hbntory-product-mcp")   # the server object; tools register onto it

# Fields kept in the list summary. Full detail comes from get_product_details.
SUMMARY_FIELDS = ("id", "sku", "name", "category", "brand",
                  "unit_price", "currency", "discontinued")

def _summarize(product: dict) -> dict:
    """Build a trimmed summary dict for one product (browsing use case)."""
    # .get() returns None for a missing key instead of raising KeyError
    return {field: product.get(field) for field in SUMMARY_FIELDS}

@mcp.tool()                     # registers this function as a tool the agent can call
def list_products() -> dict:
    """List available products from the external Product API.

    Returns a trimmed summary per product (id, sku, name, category, brand,
    unit_price, currency, discontinued). Walks all pages so nothing is missed.
    On failure, returns a dict with an 'error' key instead of raising.
    """
    url = f"{PRODUCT_API_BASE_URL}/api/v1/products"
    all_products = []                # accumulates across every page
    offset = 0                       # how many products to skip; starts at 0
    try:
        # one Client reused for every page, closed automatically at the end
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            while True:
                response = client.get(url, params={"offset": offset})
                response.raise_for_status()   # turn any 4xx/5xx into an exception
                data = response.json()        # JSON text -> Python dict
                # NOTE: the array lives under "results", not "products"
                for product in data["results"]:
                    all_products.append(_summarize(product))
                # stop once we've collected everything the API reports
                if len(all_products) >= data["count"]:
                    break
                offset += data["limit"]      # jump forward one page and go again
    except httpx.TimeoutException:      # API alive but too slow
        return {"error": "product_api_timeout",
                "message": "The Product API did not respond in time."}
    except httpx.RequestError:          # never connected: wrong port, container down
        return {"error": "product_api_unreachable",
                "message": "Could not reach the Product API."}
    except httpx.HTTPStatusError as exc:  # connected, but answered 4xx/5xx (e.g. 503)
        return {"error": "product_api_error",
                "message": "The Product API returned an error.",
                "status_code": exc.response.status_code}
    return {"count": len(all_products), "products": all_products}

@mcp.tool()
def get_product_details(identifier: str) -> dict:
    """Get the full record for one product, by numeric ID or SKU.

    Returns the complete product (including supplier info). If no product
    matches, returns an 'error' dict rather than raising, so the AI agent
    gets a clear, non-silent signal.
    """
    identifier = str(identifier).strip()   # tolerate a number or stray spaces
    if not identifier:
        return {"error": "invalid_identifier",
                "message": "A product id or SKU is required."}

    url = f"{PRODUCT_API_BASE_URL}/api/v1/products/{identifier}"
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(url)
            # check 404 BEFORE raise_for_status, so "does not exist" stays
            # separate from "the API is broken"
            if response.status_code == 404:
                return {"error": "product_not_found",
                        "message": f"No product found for identifier '{identifier}'."}
            response.raise_for_status()   # any OTHER bad status becomes an exception
            return response.json()        # full record, supplier included — no trimming
    except httpx.TimeoutException:
        return {"error": "product_api_timeout",
                "message": "The Product API did not respond in time."}
    except httpx.RequestError:
        return {"error": "product_api_unreachable",
                "message": "Could not reach the Product API."}
    except httpx.HTTPStatusError as exc:
        return {"error": "product_api_error",
                "message": "The Product API returned an error.",
                "status_code": exc.response.status_code}

# must stay at the BOTTOM: everything above is registered before the server starts
if __name__ == "__main__":
    mcp.run(transport="streamable-http")   # serves MCP at http://127.0.0.1:8000/mcp