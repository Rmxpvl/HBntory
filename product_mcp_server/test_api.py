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

