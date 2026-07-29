# Product MCP Server

Read-only bridge between the AI agent (Task 5) and the external Product API.
The server holds no state and no cache: every request it receives is forwarded
to the Product API and the answer is handed back reshaped for the agent. It
never touches PostgreSQL and knows nothing about stock, branches, or users.

## Running it

```bash
# Terminal 1 — external Product API (clone it as a sibling of this repo)
git clone https://github.com/hbtn-edu/hbntory-products-api.git
cd hbntory-products-api
docker compose up --build
# serves the API at http://localhost:5001

# Terminal 2 — this server
cd product_mcp_server
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python server.py
# serves MCP at http://127.0.0.1:8000/mcp
```

`PRODUCT_API_BASE_URL` controls where the server looks for the Product API.
It defaults to `http://localhost:5001` for local runs; inside Docker Compose
it's set to `http://external-products-api:5000` instead.

## Tools

| Tool | Input | Output on success |
|---|---|---|
| `list_products` | none | `{count, products: [...]}` — every page walked, eight summary fields per product (`id`, `sku`, `name`, `category`, `brand`, `unit_price`, `currency`, `discontinued`). Discontinued items are excluded by the API's default listing. |
| `get_product_details` | `identifier` — numeric ID or SKU, as a string | The complete product record, including the nested `supplier` object |

The list is trimmed on purpose: browsing shouldn't flood the agent's context
window, and a detail lookup is a deliberate question that deserves the full
record.

## Error handling

Neither tool ever raises. A raised exception reaches the agent as a generic
protocol failure it can't interpret; a returned dict with an `error` key is
output it can read, distinguish, and repeat honestly to a customer.

| `error` value | Trigger | Extra field |
|---|---|---|
| `invalid_identifier` | Empty or whitespace-only identifier, rejected before any network call | — |
| `product_not_found` | Product API answered 404: no such ID or SKU | — |
| `product_api_timeout` | No response within 10 seconds | — |
| `product_api_unreachable` | Connection refused — container down, wrong host or port | — |
| `product_api_error` | Any other non-2xx status, e.g. the API's forced 503 | `status_code` |

Two ordering details matter in the code:
- `TimeoutException` is caught before `RequestError`, since it's a subclass of
  it — checking the general case first would mislabel every timeout as
  "unreachable."
- For `get_product_details`, the 404 check happens *before*
  `raise_for_status()`. A 404 there is a meaningful answer ("no such
  product"), not an API malfunction, and the two must stay distinguishable.

## Manual test evidence

Run against the real `hbntory-products-api` (github.com/hbtn-edu/hbntory-products-api,
`docker compose up --build`, port 5001) by calling `server.py`'s tool
functions directly in a Python shell — not the MCP Inspector, but the same
code path the Inspector or an agent would go through, since `@mcp.tool()`
only registers the function and doesn't change how it runs.

| # | Test | Result |
|---|---|---|
| 1 | `list_products` returns the full catalogue, trimmed | PASS — `count: 39` (one discontinued product excluded; `/health` reports 40 total, matching). First item: `{'id': 4, 'sku': 'HB-MON-2102', 'name': '24 inch Compact Monitor', 'category': 'Displays', 'brand': 'LabForge', 'unit_price': 169.99, 'currency': 'USD', 'discontinued': False}` — exactly the eight summary fields, no `description`/`tags`/`supplier`. |
| 2 | `get_product_details` by numeric ID (`4`) | PASS — full record including `description`, `tags`, `weight_kg`, `updated_at`, and the nested `supplier` object (`SUP-LAB-002`, LabForge Supplies) that the list output doesn't carry. |
| 3 | `get_product_details` by SKU (`HB-MON-2102`) | PASS — byte-for-byte the same record as test 2, confirming both identifier styles resolve through the same code path. |
| 4 | Unknown identifier (`does-not-exist`) | PASS — `{"error": "product_not_found", "message": "No product found for identifier 'does-not-exist'."}`; a normal, successful tool result, not a protocol-level error. |
| 5 | Empty identifier (`""`) | PASS — `{"error": "invalid_identifier", ...}`, rejected before any network call (confirmed no request was logged). |
| 6 | Product API unreachable | PASS — container stopped (`docker compose stop`) in the middle of the test session; both `list_products()` and `get_product_details()` returned `{"error": "product_api_unreachable", "message": "Could not reach the Product API."}`. |
| 7 | Product API returns 503 | PASS (via a local test double, not the real API — see note below) — `{"error": "product_api_error", "status_code": 503}`. |

Test 7 uses a test double rather than the real API's `force_error=true`
because the tool deliberately never forwards arbitrary query parameters to
the Product API (see "avoid exposing unnecessary Product API behavior" in
the task brief) — there's no way to ask the real API for a 503 through the
tool's actual parameter surface, which is itself a confirmation that the
trimmed interface works as intended, not a gap in coverage. Confirmed
independently that the real API does answer 503 to
`curl "http://localhost:5001/api/v1/products?force_error=true"`.

## Design decisions

| Decision | Why |
|---|---|
| Trim the list, keep the detail whole | Browsing needs a compact result; a detail lookup is a deliberate question and deserves the full record. Reversible with a one-line edit to `SUMMARY_FIELDS`. |
| Return error dicts, never raise | A raised exception is information the agent can't use; a returned `{"error": ..., "message": ...}` dict is. |
| Walk every page of the Product API | Returning only page one would make the agent deny products that exist on later pages — a silent failure by omission. |
| Read the Product API address from the environment | Hard-coding `localhost:5001` breaks inside Docker Compose; `os.environ.get` with a local fallback works in both environments and keeps configuration out of Git. |

## What's next

Task 5 (AI Query Service) connects an agent to these two tools over the same
Streamable HTTP endpoint and combines them with a read-only stock path.
Nothing in `server.py` changes for that — the tool and error contracts above
stay as they are.
