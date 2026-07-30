# HBntory — Minimum Viable Product

**This is the original plan, kept for historical context.** See
`architecture.md` for what was actually delivered. Two phases below
(1's API Gateway, and all of Phase 7) were excluded from the final scope
by agreement with the project supervisor — marked inline below.

## MVP Goal

Deliver a secure inventory Backoffice plus an anonymous, deterministic product catalogue and search interface. Product details come from the supplied API through the appropriate integration path; the public catalogue does not expose stock. Stock stays in the local database, behind Backoffice authentication. ~~The AI Query Service is scheduled as the final phase~~ **Excluded from final scope — see Phase 7.**

## Phase 1 — Database and Backoffice Foundation

- ~~API Gateway as the single HTTP entry point~~ **Excluded from final scope.** The Backoffice is the single service; it serves the authenticated pages and the public catalogue directly, with no gateway in front.
- ~~PostgreSQL configuration.~~ **Delivered on SQLite instead** — the documented, tested local database. PostgreSQL was explored but is not the delivered path; see `architecture.md`, "Known limitations".
- SQLAlchemy models for users, branches and stock.
- Database initialization via Base.metadata.create_all() and an idempotent seed script (no Alembic).
- Exactly one `admin` account.
- At least two branches and sample stock.
- Argon2id password hashing.
- Product-ID validation against the Product API.
- Positive integer stock changes and negative-stock prevention.
- Automated model, initialisation and validation tests.

This phase is implemented by the Task 1 foundation.

## Phase 2 — Authentication and Authorisation

- Login and logout.
- Rejection of inactive users.
- Backend enforcement of `admin` and `common` roles.
- Backend enforcement of the authenticated common user's branch.
- Tests for forbidden role and cross-branch requests.

## Phase 3 — Mandatory Backoffice Operations

Admin can:

- list common users;
- create a common user and assign one branch;
- modify a common user;
- change a password or branch;
- soft-delete a common user.

Common users can, only for their assigned branch:

- consult stock;
- list products currently in stock;
- add a positive quantity;
- remove a positive quantity when sufficient stock exists.

`admin` cannot manage stock, and common users cannot manage users.

## Phase 4 — Product MCP Server

- Independent MCP server in `product_mcp_server/`.
- `list_products` tool backed by the external Product API.
- `get_product_details` tool accepting numeric IDs or SKUs.
- Explicit handling of API timeouts, `404` responses and service errors.
- No product metadata stored locally.

## Phase 5 — Public Client Web Interface

**Delivered differently from this original plan** — see
`architecture.md` Section 5 for what was built instead and why.

- Anonymous page in `client_web/`. Delivered.
- ~~Reached through the API Gateway, same as the Backoffice.~~ Served
  directly by the Backoffice app, no gateway.
- Search-box interface using REST rather than WebSockets. Delivered:
  keyword search + category filter.
- Product catalogue search. Delivered. ~~Product-detail display~~,
  ~~branch availability and quantity display~~, ~~products-in-branch
  listing~~ — not built: the delivered catalogue shows product data only,
  not stock or branch availability (stock is Backoffice-authenticated
  data, deliberately not exposed anonymously).
- ~~Product data obtained through MCP tools.~~ Delivered via the
  Backoffice's own `product_client.py` (direct REST to the Product API)
  instead — simpler, and the MCP server wasn't needed for a page with no
  AI agent behind it.
- ~~Stock obtained through controlled, read-only database queries.~~ Not
  built — the delivered catalogue never touches the database.
- Independent requests with no saved history. Delivered.
- ~~Deterministic answers first; AI-generated answers are added in Phase
  7.~~ Phase 7 excluded; this is the final state, not a first step.

## Phase 6 — Integration and QA

- Simple functional HTML, CSS and JavaScript interfaces.
- Clear validation and external-service errors.
- Automated integration tests.
- Manual QA checklist.
- Documented startup and testing commands.

## Phase 7 — AI Query Service — EXCLUDED FROM FINAL SCOPE

**Not built, by agreement with the project supervisor.** Nothing in this
list exists in the delivered project: no AI Query Service, no AI agent, no
natural-language question answering anywhere. The Product MCP Server
(Phase 4) was still built and verified on its own — it simply has no
consumer in the delivered system. Kept below for historical record only.

- ~~Independent AI Query Service, separate from the Backoffice.~~
- ~~One or more AI agents connected to the Product MCP Server tools.~~
- ~~Controlled, read-only access to stock (through the MCP server or a narrow internal API).~~
- ~~Grounded answers only: no invented product names, details, stock or branch availability.~~
- ~~Clear "information unavailable" responses when tools return nothing.~~
- ~~A REST query endpoint the Client Web Interface calls with a single question.~~
- ~~Supported question types documented (product details, product availability across branches, products in a branch, shopping-list branch recommendation).~~

## Optional Features Only If Time Remains

- More polished responsive styling.
- Audit history for stock changes.
- Additional product filters.
- Short-lived in-memory product-response caching.
- Additional deployment automation.

## Explicitly Outside the MVP

- WebSockets and streamed responses.
- Conversation history.
- Multiple administrators.
- Branch CRUD screens.
- Product creation or editing.
- Permanent storage of product details.
- Analytics dashboards.

## Acceptance Criteria (as delivered)

- The project starts from documented commands on a clean machine.
- ~~The API Gateway routes every request...~~ Not applicable — no gateway; the Backoffice serves both the authenticated pages and the public catalogue directly.
- Exactly one active administrator named `admin` exists.
- Passwords are stored only as Argon2id hashes.
- A common user always has exactly one branch.
- Cross-branch requests are rejected by the backend.
- `admin` manages users but cannot manage stock.
- Soft-deleted users cannot authenticate or retain access, including an already-open session.
- Invalid quantities, branches and products are rejected.
- Stock cannot become negative at application or database level.
- Product details are absent from the local schema.
- MCP tools list products and return product details, verified against the real external Product API.
- The anonymous public client uses REST and cannot change data.
- Product API failures produce clear errors.
- ~~The AI Query Service answers supported product and stock questions...~~ Excluded from final scope — no AI Query Service exists.
- Mandatory flows pass automated tests (`backoffice/tests/`) and manual QA (`docs/manual-qa.md`).
