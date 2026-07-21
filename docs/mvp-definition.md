# HBntory — Minimum Viable Product

## MVP Goal

Deliver a secure, functional inventory Backoffice for one administrator and branch-bound common users. Product details come from the supplied external API; local stock remains in PostgreSQL.

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

## Phase 4 — Functional Interface and QA

- Simple HTML, CSS and JavaScript pages for every mandatory operation.
- Product details retrieved live from the Product API.
- Clear validation and external-service errors.
- Automated integration tests.
- Manual QA checklist and documented startup commands.

## Optional Features Only If Time Remains

- More polished responsive styling.
- Audit history for stock changes.
- Additional product filters.
- Short-lived in-memory product-response caching.
- Additional deployment automation.

## Explicitly Outside the MVP

- AI agents and an AI Query Service.
- MCP servers or MCP database tools.
- Public chat or natural-language queries.
- WebSockets and streamed responses.
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
- Mandatory flows pass automated tests and the manual QA checklist.
