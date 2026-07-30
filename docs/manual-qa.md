# HBntory — Manual QA Evidence

**Test date:** 2026-07-30
**Commit:** `d35df08` (branch `Remy`)
**Test environment:** Windows 11, PowerShell, Python 3.14, SQLite (file-based,
`backoffice/dev.db` / disposable test files), real external Product API
(cloned from `github.com/hbtn-edu/hbntory-products-api`, run via
`docker compose up -d --build`, not mocked), real Product MCP Server
(`product_mcp_server/server.py`), all run against the actual FastAPI app
via `uvicorn` and real HTTP requests — not just `TestClient`/pytest, except
where noted.

Automated coverage: `backoffice/tests/`, 58 tests, run with
`python -m pytest tests/ -v`. This document combines two kinds of evidence:
manual end-to-end checks against real running services (sections 1, 2, 6, 7)
and automated test evidence from the suite above (sections 3, 4, 5, 8). Each
section states which one applies to it.

**AI scenarios: excluded from scope**, not tested — no AI Query Service
exists in this project (agreed with the project supervisor).
**Public Client Web Interface**: tested as what it actually is — a product
catalogue (search + category filter), not a question-answering interface.
See `README.md` Section 8 for that scope decision.

## 1. External Product API health check

```
curl http://localhost:5001/health
```

Result: `{"status": "ok", "products": 40, "suppliers": 5}` — **PASS**.

## 2. Backoffice startup and login

- Started with `python -m uvicorn app.main:app --port 5000` against a
  freshly seeded SQLite database (`python -m app.seed`).
- `GET /` → 200, serves the public catalogue page.
- `GET /login` → 200, serves the login page.
- `POST /api/auth/login` with the seeded admin credentials → 200, returns
  user info, sets a `Secure; HttpOnly; SameSite=lax` session cookie.
- `GET /api/auth/me` with that cookie → 200, returns the same user.

Result: **PASS**.

## 3. Common-user stock operations

Verified via automated tests (`backoffice/tests/test_stock_services.py`,
`test_rbac.py`) exercising the real service functions and real HTTP routes
against a fresh database — not mocked business logic:

| Scenario | Result |
| --- | --- |
| Common user adds valid stock for their own branch | PASS — `test_common_user_can_manage_stock_for_their_own_branch`, `test_add_stock_...` |
| Common user removes valid stock | PASS — `test_remove_stock_reduces_an_existing_quantity` |
| Common user cannot remove more stock than available | PASS — `test_remove_stock_rejects_removing_more_than_available`, rejected with a clean error, stored quantity untouched |
| Common user cannot operate on another branch | PASS — `test_stock_operations_ignore_a_client_supplied_branch_id`: `branch_id` isn't even a field on the request; a client-supplied one is rejected with 422 |
| Stock listing restricted to the authenticated user's branch | PASS — `test_list_branch_stock_only_returns_that_branchs_rows` |
| Adding a product unknown to the Product API is rejected | PASS — `test_add_stock_rejects_a_product_unknown_to_the_product_api` |
| Product details (name/price/category) come from the external API, never invented locally | PASS — confirmed by reading `product_client.py` and the schema: `Stock` only stores `product_id`/`quantity` |

## 4. Admin user-management operations

| Scenario | Result |
| --- | --- |
| Admin can create a common user | PASS — `test_create_common_user_succeeds_with_a_valid_branch` |
| Username conflict is rejected cleanly (409, not a crash) | PASS — `test_create_common_user_rejects_an_already_taken_username`, and the concurrent-race variant `test_create_common_user_converts_a_concurrent_duplicate_username_into_conflict_error` |
| Invalid branch is rejected (404, not a crash) | PASS — `test_create_common_user_rejects_an_unknown_branch` |
| Admin can change a user's username/branch | PASS — `test_update_user_changes_username_and_branch` |
| Admin can change a user's password | PASS — `test_change_password_updates_the_stored_hash` |
| Admin can soft-delete a common user | PASS — `test_soft_delete_marks_the_user_inactive` |
| Admin account itself cannot be edited/password-changed/deleted via these endpoints | PASS — `test_change_password_rejects_the_admin_account`, `test_soft_delete_rejects_the_admin_account` |
| Soft-deleted user's stock history is preserved | PASS — `test_soft_delete_does_not_touch_that_users_branchs_stock` |
| Admin cannot manage stock | PASS — `test_admin_cannot_manage_stock` (403) |
| Common user cannot manage users | PASS — `test_common_user_cannot_manage_users` (403) |

## 5. Deleted-user login and active-session rejection

| Scenario | Result |
| --- | --- |
| Deleted (soft-deleted/inactive) user cannot log in | PASS — `test_inactive_user_cannot_log_in` |
| An already-open session for a user who becomes inactive is rejected on the next request | PASS — `test_inactive_user_session_is_rejected`, `test_session_with_stale_token_version_is_rejected` |
| Logout revokes the session server-side, immediately, for every copy of the cookie | PASS — `test_logout_revokes_the_session_server_side`: a cookie copied before logout is confirmed rejected after |

## 6. Product MCP Server

Run against the real external Product API (not mocked), by calling
`server.py`'s tool functions directly — the same code path the MCP
Inspector or an agent would go through, since `@mcp.tool()` only registers
the function.

| # | Test | Result |
| --- | --- | --- |
| 1 | `list_products` returns the full catalogue, trimmed to summary fields | PASS — `count: 39` (one discontinued product excluded), no `description`/`tags`/`supplier` in the summary |
| 2 | `get_product_details` by numeric ID | PASS — full record, including nested `supplier` |
| 3 | `get_product_details` by SKU | PASS — identical record to test 2, confirming both identifier styles resolve the same way |
| 4 | Unknown identifier | PASS — `{"error": "product_not_found", ...}`, a normal tool result, not a protocol error |
| 5 | Empty identifier | PASS — `{"error": "invalid_identifier", ...}`, rejected before any network call |
| 6 | Product API unreachable (container stopped mid-session) | PASS — both tools returned `{"error": "product_api_unreachable", ...}` |
| 7 | Product API returns 503 | PASS (via a local test double — the tool deliberately never forwards a `force_error`-style parameter to the real API) — `{"error": "product_api_error", "status_code": 503}` |

Full detail: [`product_mcp_server/README.md`](../product_mcp_server/README.md).

## 7. Public catalogue (client_web)

Verified against the real external Product API, through the running app:

| Scenario | Result |
| --- | --- |
| `GET /` serves the catalogue page | PASS |
| `GET /api/public/categories` (no auth) | PASS — real category list with product counts returned |
| `GET /api/public/products` (no filter, no auth) | PASS — 39 products |
| `GET /api/public/products?category=Laptops` | PASS — 2 laptops returned |
| `GET /api/public/products?q=keyboard` | PASS — matching product returned |
| Page does not list every product by default (only after a search) | PASS — confirmed in the served JS (`loadProducts()` only runs on form submit, not on page load) |

## 8. Automated test suite

```
cd backoffice
python -m pytest tests/ -v
```

Result at time of writing: **58 passed**, 0 failed, no external
dependencies (SQLite in a temp-dir file, recreated per test).
