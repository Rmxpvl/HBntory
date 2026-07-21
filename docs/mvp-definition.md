# HBntory — Minimum Viable Product

## MVP Goal

Deliver a secure inventory Backoffice plus an anonymous, deterministic product-and-stock search interface. Product details come from the supplied API through the appropriate integration path; stock remains in PostgreSQL. AI (Phase 7) is a stretch goal attempted only if time remains after the mandatory scope.

## Phase 1 — Database and Backoffice Foundation

- PostgreSQL configuration.
- SQLAlchemy models for users, branches and stock.
- Alembic initial migration.
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
- Search-box interface using REST rather than WebSockets.
- Product catalogue search and product-detail display.
- Branch availability and quantity display.
- Products-in-branch listing.
- Product data obtained through MCP tools.
- Stock obtained through controlled, read-only database queries.
- Independent requests with no saved history.
- No AI-generated answers.

## Phase 6 — Integration and QA

- Simple functional HTML, CSS and JavaScript interfaces.
- Clear validation and external-service errors.
- Automated integration tests.
- Manual QA checklist.
- Documented startup and testing commands.

## Phase 7 — Optional AI Layer (Time Permitting)

Attempted only after Phases 1-6 are complete and tested.

- Independent AI Query Service, separate from the Backoffice.
- One or more AI agents connected to the Product MCP Server for product data.
- Controlled agent access to stock data (extended MCP tools or an internal read-only API).
- Natural-language question endpoint (REST or WebSocket) consumed by the Client Web Interface as an additional entry point alongside the deterministic search.
- Grounded responses only: the agent must not invent product, stock or branch data, and must state clearly when information is unavailable.

## Optional Features Only If Time Remains

- More polished responsive styling.
- Audit history for stock changes.
- Additional product filters.
- Short-lived in-memory product-response caching.
- Additional deployment automation.

## Explicitly Outside the MVP

- WebSockets and streamed responses for the deterministic client.
- Conversation history.
- Multiple administrators.
- Branch CRUD screens.
- Product creation or editing.
- Permanent storage of product details.
- Analytics dashboards.

## Acceptance Criteria

- The project starts from documented commands on a clean machine.
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
- Mandatory flows pass automated tests and the manual QA checklist.
