# HBntory — Minimum Viable Product

## MVP Goal

Deliver a secure inventory Backoffice plus an anonymous, deterministic product-and-stock search interface, both reached through a single API Gateway entry point. Product details come from the supplied API through the appropriate integration path; stock remains in PostgreSQL. The AI Query Service is scheduled as the final phase and built last, once the deterministic foundation is stable — it is deferred, not dropped.

## Phase 1 — Database, Backoffice and API Gateway Foundation

- API Gateway as the single HTTP entry point, routing requests to the Backoffice by path and forwarding headers/cookies unchanged (no authentication or business logic in the Gateway).
- PostgreSQL configuration.
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

- Anonymous page in `client_web/`.
- Reached through the API Gateway, same as the Backoffice.
- Search-box interface using REST rather than WebSockets.
- Product catalogue search and product-detail display.
- Branch availability and quantity display.
- Products-in-branch listing.
- Product data obtained through MCP tools.
- Stock obtained through controlled, read-only database queries.
- Independent requests with no saved history.
- Deterministic answers first; AI-generated answers are added in Phase 7.

## Phase 6 — Integration and QA

- Simple functional HTML, CSS and JavaScript interfaces.
- Clear validation and external-service errors.
- Automated integration tests.
- Manual QA checklist.
- Documented startup and testing commands.

## Phase 7 — AI Query Service (final phase)

- Independent AI Query Service, separate from the Backoffice.
- One or more AI agents connected to the Product MCP Server tools.
- Controlled, read-only access to stock (through the MCP server or a narrow internal API).
- Grounded answers only: no invented product names, details, stock or branch availability.
- Clear "information unavailable" responses when tools return nothing.
- A REST query endpoint the Client Web Interface calls with a single question.
- Supported question types documented (product details, product availability across branches, products in a branch, shopping-list branch recommendation).

This phase is built last, after Phases 1–6 are stable.

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

## Acceptance Criteria

- The project starts from documented commands on a clean machine.
- The API Gateway routes every request to the Backoffice or the Client Web Interface and returns a clear HTTP error (`404`/`502`/`503`/`504`) when a downstream service cannot answer.
- Exactly one active administrator named `admin` exists.
- Passwords are stored only as Argon2id hashes.
- A common user always has exactly one branch.
- Cross-branch requests are rejected by the backend.
- `admin` manages users but cannot manage stock.
- Soft-deleted users cannot authenticate or retain access.
- Invalid quantities, branches and products are rejected.
- Stock cannot become negative at application or database level.
- Product details are absent from the local schema.
- MCP tools list products and return product details.
- The anonymous public client uses REST and cannot change data.
- Product API failures produce clear errors.
- The AI Query Service (final phase) answers supported product and stock questions from real data and clearly states when information is unavailable.
- Mandatory flows pass automated tests and the manual QA checklist.
