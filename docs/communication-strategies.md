# HBntory — Communication Strategy

## Backoffice: REST with HTML, CSS and JavaScript

**Selected option:** A FastAPI REST backend with a small frontend written in plain HTML, CSS and JavaScript.

**Main benefit:** The API is explicit and independently testable while the interface remains small and requires no frontend framework.

**Trade-off:** The team must write browser-side request handling and update the page with JavaScript. Server-side rendering would require less browser code.

## Backoffice to Database: SQLAlchemy

**Selected option:** The Backoffice is the only service that performs application database operations, using SQLAlchemy sessions and Alembic migrations.

**Main benefit:** Validation, transactions and data access remain in one controlled application layer.

**Trade-off:** Changes to the models require reviewed migrations; the database schema must not be modified manually.

## Backoffice to Product API: Read-only REST

**Selected option:** The Backoffice calls the supplied API through HTTP REST requests whenever product information or product-ID validation is required.

**Main benefit:** Product data always comes from its authoritative source and is never duplicated locally.

**Trade-off:** Product information may be temporarily unavailable when the external service is slow or offline. The Backoffice must return a clear error and must not invent or cache permanent product details.

## Authentication Transport

**Selected option:** A signed, HTTP-only, same-site session cookie. State-changing requests also use CSRF protection.

**Main benefit:** JavaScript cannot read the cookie, and the browser attaches it automatically to Backoffice requests.

**Trade-off:** This choice is intended for the browser-based Backoffice. A future unrelated API client would require a separate authentication method.

Credentials are never stored in plain text, and every role or branch restriction is enforced by the backend.

## Excluded communication

The agreed implementation does not contain an AI Query Service, MCP server, public AI client or WebSocket communication. No implementation decision is required for components that are outside the project scope.
