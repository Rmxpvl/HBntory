# Backoffice UI/Backend Approach

## Approach chosen: REST API + lightweight HTML/CSS/JS

The Backoffice is one FastAPI application (`backoffice/app/main.py`) that does
two things:

- Serves the JSON REST API under `/api/*`.
- Serves three static, framework-free pages (`static/login.html`,
  `static/stock.html`, `static/users.html`) via `StaticFiles`, styled with
  plain CSS and driven by small vanilla JS modules (`static/js/*.js`) — no
  build step, no SPA framework.

This was preferred over Server-Side Rendering because the two user roles see
completely different, self-contained screens (stock vs. user management), so
there's little templating to share, and a thin REST contract keeps the
backend testable in isolation from any HTML rendering.

## How the frontend talks to the backend

`static/js/api.js` centralises every HTTP call through one `apiRequest()`
helper: JSON in/out, `credentials: 'include'` so the signed session cookie
rides along automatically, and errors normalised into one `ApiError` shape
regardless of which endpoint failed. `static/js/routes.js` is the single
source of truth for endpoint paths on the frontend side — it's the file that
must stay in sync with the backend's routers (`app/routes/*.py`,
`app/main.py`); a prefix mismatch between the two was caught and fixed this
way (`/api/auth/login` vs. an un-prefixed `/api/login`).

## Where authorization actually lives

`static/js/guards.js` redirects a logged-in common user away from
`users.html` and an admin away from `stock.html`, and bounces an anonymous
visitor to `login.html`. **This is a UX convenience only** — it reads
`GET /api/auth/me` and just decides which page to show. It enforces nothing.

The actual authorization boundary is server-side, on every request,
independent of which page (if any) made the call:

- `get_current_actor` (`app/auth/current_actor.py`) re-derives the caller's
  identity from the signed session cookie on every request — never trusts
  anything the client claims about itself.
- `require_admin` / `require_common` (`app/routes/users.py`,
  `app/routes/stock.py`) reject the wrong role with 403 before the route body
  ever runs.
- Stock operations take `branch_id` from the authenticated actor, never from
  the request body (`StockChange` has no `branch_id` field, and
  `extra="forbid"` rejects one if a client tries to add it) — a common user
  cannot touch another branch's stock no matter what the UI does or doesn't
  show.

Verified end-to-end in `backoffice/tests/test_rbac.py`: hitting the API
directly (no browser, no hidden buttons involved) with each role confirms the
four required rules hold at the backend layer.

## Product data

`app/services/product_client.py` is the only thing that talks to the external
Product API. The Backoffice never stores product name/price/description
locally — `Stock` only ever holds `product_id` and `quantity`. The frontend
gets product details by calling `GET /api/products` (a straight pass-through),
never from local state that could drift from the real catalogue.

## Error handling

Two exception handlers in `main.py` (`api_error`, `validation_error`) convert
every `HTTPException` and every Pydantic validation failure into the same
`{"error": "..."}` JSON shape, so `static/js/api.js` has one code path for
displaying any backend failure, instead of one shape per endpoint.
