import httpx

url = "http://localhost:5001/api/v1/products"
all_products = []
offset = 0

with httpx.Client(timeout=10.0) as client:
    while True:
        response = client.get(url, params={"offset": offset})
        data = response.json()
        all_products.extend(data["results"])
        if len(all_products) >= data["count"]:
            break
        offset += data["limit"]

print(len(all_products))

# the eight fields the list keeps; one place to change the rule later
SUMMARY_FIELDS = ("id", "sku", "name", "category", "brand",
                  "unit_price", "currency", "discontinued")


def _summarize(product: dict) -> dict:
    """Build a trimmed summary dict for one product (browsing use case)."""
    # .get() returns None for a missing key instead of raising KeyError
    return {field: product.get(field) for field in SUMMARY_FIELDS}

print(_summarize(all_products[0]))