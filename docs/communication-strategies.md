# HBntory — Communication Strategy

**This document has been corrected to describe what was actually built.**
Several entries in the original decision table (API Gateway, Client
Service querying the database, AI Query Service) described components that
were excluded from the final scope — see `architecture_EN.md` for the full
explanation.

## Decision Summary (as delivered)

| Communication | Selected Option |
| --- | --- |
| Internal browser → Backoffice | REST with HTML, CSS and JavaScript, signed session cookie |
| Public browser → Backoffice | REST, anonymous — same app as above, no gateway |
| Backoffice → SQLite | SQLAlchemy |
| Backoffice → Product API | Read-only REST (used by both authenticated and public catalogue endpoints) |
| Product MCP Server → Product API | Read-only REST |

## Backoffice: REST with HTML, CSS and JavaScript

**Selected option:** A FastAPI REST backend with a small frontend written in plain HTML, CSS and JavaScript.

**Main benefit:** The API is explicit and independently testable while the interface remains small and requires no frontend framework.

**Trade-off:** The team must write browser-side request handling and update pages with JavaScript. Server-side rendering would require less browser code.

## Public Catalogue: REST, Not WebSockets

**Selected option:** Each search or filter is one independent REST request to the Backoffice's public endpoints.

**Main benefit:** REST is simple to implement, test and debug, and no persistent connection state is required.

**Trade-off:** REST does not provide continuous bidirectional communication or streamed responses. Neither is needed for a keyword/category product search.

## Product MCP Server to Product API

**Selected option:** Read-only REST requests to the supplied Product API.

**Main benefit:** Product data always comes from its authoritative source and is never duplicated locally.

**Trade-off:** Product searches may be temporarily unavailable when the external service is slow or offline. The service must return a clear error rather than inventing or permanently caching data.

## Authentication Transport

**Selected option:** A signed, HTTP-only, `SameSite=Lax` session cookie for the Backoffice, with a `token_version` counter checked on every request so logout revokes server-side, immediately, for every session of that user.

**Main benefit:** JavaScript cannot read the cookie, the browser attaches it automatically to Backoffice requests, and logout doesn't rely on the client discarding the cookie honestly.

**Trade-off:** This mechanism is intended for the browser-based Backoffice. An unrelated API client would require a separate authentication method. It does not include an explicit CSRF token — `SameSite=Lax` is a partial mitigation only, documented as a known limitation.

## Excluded from Scope

The following were part of the original communication plan and were not
built, by agreement with the project supervisor:

- **API Gateway** as a single routing entry point in front of the
  Backoffice and a separate Client Service. Not built — the Backoffice
  serves both the authenticated pages and the public catalogue directly.
- **Client Service → stock database**, controlled read-only SQLAlchemy
  queries from a separate public-facing service. Not built — the
  delivered public catalogue shows product data only, never touches the
  database, and is served by the Backoffice itself rather than a separate
  service.
- **Public browser → AI Query Service**, and **AI Query Service → Product
  MCP Server / stock database**. Not built at all — no AI Query Service
  exists in this project. The Product MCP Server was still built and
  verified independently; it simply has no consumer.
