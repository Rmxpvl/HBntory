# HBntory — System Architecture

## 1. Scope (as delivered)

This document describes the system that was actually built, not the original
multi-phase plan. See `mvp-definition.md` for the original plan and which
parts of it were excluded by agreement with the project supervisor.

HBntory, as delivered, is an inventory platform for a company with several
physical branches. It contains:

- **the Backoffice** — a single FastAPI service that authenticates internal
  users (`admin`, `common`) and, on the same app, serves an anonymous public
  product catalogue page;
- **SQLite** as the documented and tested local database for users,
  branches and stock (see "Known limitations" below for PostgreSQL's status);
- **the supplied read-only external Product API**;
- **an independent Product MCP Server** (`product_mcp_server/`) that exposes
  controlled product tools over MCP.

There is **no API Gateway**. There is **no AI Query Service**. Both were
part of the original plan (`mvp-definition.md` Phases 1 and 7) and were
excluded from the final scope by agreement with the project supervisor —
see the "Excluded from scope" section below.

## 2. Components and Responsibilities

### Backoffice Service

The Backoffice (`backoffice/`) is a single FastAPI service with a plain
HTML, CSS and JavaScript interface. It serves two things directly, with no
gateway in front of it:

- **Authenticated pages** (`/login`, `/stock`, `/users`):
  - authenticates internal users via a signed, HTTP-only, `SameSite=Lax`
    session cookie;
  - enforces roles and branch restrictions in the backend, not just in the
    UI;
  - lets the single `admin` user list, create, modify and soft-delete
    common users, and change their password or branch;
  - prevents `admin` from managing stock;
  - lets common users consult, list, add and remove stock only for their
    assigned branch;
  - obtains product information from the external Product API through
    read-only REST requests (`app/services/product_client.py`).
- **The public catalogue page** (`/`, backed by `client_web/`):
  - anonymous, no session required;
  - lets visitors search the product catalogue by keyword and filter by
    category (`GET /api/public/products`, `GET /api/public/categories`);
  - calls the external Product API directly through the same
    `product_client.py` module the authenticated side uses — **not**
    through the Product MCP Server, and with no database access.

There is only one administrator, named `admin`. Common users belong to
exactly one branch. The backend derives a common user's branch from the
authenticated session rather than trusting a branch submitted by the
browser.

### Local Database

SQLite (a single file, `dev.db` by default) is the documented and tested
local database. It contains only:

- `users`: username, password hash, role, branch assignment, soft-deletion
  state, and a `token_version` counter used for session revocation;
- `branches`: branch identity and location name;
- `stocks`: branch, external numeric product ID and available quantity.

It does not contain product names, SKUs, descriptions, prices, images or
metadata. See "Known limitations" for PostgreSQL's status.

### External Product API

The supplied API is the authoritative source of product information. It:

- lists products, with optional category and free-text filters;
- returns product details by numeric ID or SKU;
- is read-only;
- does not own or return HBntory stock quantities.

The Backoffice validates product identifiers against this API before
creating stock records. It stores only the canonical numeric product `id`
returned by the API — the API's `id` field, not its separate `sku` string.

### Product MCP Server

`product_mcp_server/` is an independent bridge to the external Product API,
exposing two tools over MCP (Streamable HTTP):

- `list_products`: paginated, trimmed product summaries;
- `get_product_details`: one full product record by numeric ID or SKU.

It is a plain bridge with no AI agent, and holds no state. **Nothing in
this project currently consumes it** — the AI Query Service that was meant
to (Phase 7 of the original plan) was never built, per the agreed final
scope. It ships complete and independently verified against the real
Product API (see `product_mcp_server/README.md`), ready to be connected to
an agent in future work.

## 3. Data Flow

### Backoffice Authentication

1. The browser submits credentials directly to the Backoffice
   (`POST /api/auth/login`) — no gateway in front of it.
2. The Backoffice retrieves the active user and verifies the password
   against its Argon2id hash (with a fixed dummy hash used when the
   username doesn't exist, to avoid leaking which usernames are real
   through timing).
3. Successful authentication creates a signed, HTTP-only session cookie
   containing the user's ID and their current `token_version`.
4. Every protected request reloads the user from the database and checks:
   the signature and expiry of the cookie, the user's active status, and
   that `token_version` still matches (see "Logout" below).

### Backoffice Stock Consultation and Change

1. A common user requests or changes their branch's stock
   (`GET/POST /api/stock/*`).
2. The backend derives the branch from the authenticated session, never
   from the request body.
3. SQLAlchemy reads/writes the local `stocks` table.
4. Product identifiers are validated against the external Product API
   before a new stock row is created.
5. A positive-integer check and a database `CHECK` constraint together
   prevent negative quantities; removing more than what's in stock is
   rejected.

### Public Catalogue Search

1. An anonymous visitor searches or filters the catalogue
   (`GET /api/public/products`, `GET /api/public/categories`) — no
   session, no gateway.
2. The Backoffice calls the external Product API directly (the same
   `product_client.py` code the authenticated side uses).
3. Results are returned as-is; nothing is stored locally, and no database
   query is involved on this path at all.

### Logout

1. The client calls `POST /api/auth/logout`.
2. The backend increments that user's `token_version` in the database and
   deletes the browser's cookie.
3. Because every protected request compares the cookie's `token_version`
   against the current stored value, **every** cookie previously issued
   for that user — not just the one being deleted — stops being accepted
   immediately, even if a copy of it was taken beforehand.

## 4. Security and Integrity Rules

- Passwords are never stored in plain text; Argon2id is used because it is
  designed for password storage and resists brute-force attacks through
  configurable memory and computation costs (see `docs/password-security.md`).
- The Backoffice uses a signed, HTTP-only, `SameSite=Lax` session cookie.
  **This is not full CSRF protection** — `SameSite=Lax` mitigates ordinary
  cross-site form submissions, but there is no explicit CSRF token on
  state-changing requests. Documented as a known limitation, not
  implemented.
- Authentication and authorisation are enforced in the backend, not just
  hidden in the UI.
- `admin` has no branch and cannot use stock operations; a common user has
  exactly one branch and cannot select another.
- Soft-deleted users cannot authenticate, and an already-open session for
  a soft-deleted user is rejected on its next request.
- Logout revokes server-side, immediately, for every session of that user
  (see "Logout" above) — this is stronger than a stateless-token approach
  that only deletes the browser's cookie.
- Stock changes require positive integers and cannot make quantity
  negative (validated in code and enforced by a database constraint).
- The public catalogue endpoints are read-only and require no session.
- Secrets are supplied through environment variables and are not committed.

## 5. Excluded from Scope

Agreed with the project supervisor, not an oversight:

- **API Gateway** (original Phase 1) — not built. The Backoffice is the
  single service; it serves both the authenticated pages and the public
  catalogue directly.
- **AI Query Service** (original Phase 7) — not built. No natural-language
  question answering exists anywhere in this project.
- Consequently, the Product MCP Server has no consumer in the delivered
  system (see above).
- The original "Public Client Service" concept — its own backend calling
  the MCP server and querying stock directly — was not built either; the
  public catalogue page instead reuses the Backoffice's existing
  `product_client.py` module through two new anonymous endpoints. This is
  simpler and needed no stock access at all, since the catalogue shows
  product data only, not stock.

## 6. Known Limitations

- **PostgreSQL is not the delivered database.** The schema was originally
  designed for PostgreSQL and `psycopg2-binary` was in the dependency list,
  but the documented, tested local setup uses SQLite exclusively; the
  unused PostgreSQL Docker Compose file and dependency were removed rather
  than left as an undocumented, unverified path. Switching to PostgreSQL
  would require re-testing the full flow against it.
- **No explicit CSRF token.** See Section 4.
- **No login rate limiting.** Not implemented, not required by the task
  brief.
- **`Base.metadata.create_all()`, not migrations.** It creates missing
  tables but cannot alter an existing one — a schema change requires
  dropping and recreating the local database. Alembic was evaluated and
  deliberately not adopted for this project's scope.

## 7. Related Deliverables

- [MVP definition](mvp-definition.md) — the original plan and what was
  excluded from it.
- [Initial service diagram](initial-service-diagram.md)
- [Communication strategy](communication-strategies.md)
- [Local run guide](local-run-guide.md)
- [Product MCP Server README](../product_mcp_server/README.md)
