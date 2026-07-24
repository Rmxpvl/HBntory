import httpx

with httpx.Client(timeout=10.0) as client:
    response = client.get("http://localhost:5001/api/v1/products")
    data = response.json()

print(data["count"], "products in total")
print(len(data["results"]), "in this page")
print(data["results"][0]["name"])

