# HBntory — Communication Strategy

## Decision Summary

| Communication | Selected Option |
| --- | --- |
| Internal browser → Backoffice | REST with HTML, CSS and JavaScript |
| Backoffice → PostgreSQL | SQLAlchemy |
| Backoffice → Product API | Read-only REST |
| Public browser → Client Service | REST, not WebSockets |
| Client Service → Product MCP Server | MCP over Streamable HTTP |
| Product MCP Server → Product API | Read-only REST |
| Client Service → stock database | Controlled, read-only SQLAlchemy queries |

## Backoffice: REST with HTML, CSS and JavaScript

**Selected option:** A FastAPI REST backend with a small frontend written in plain HTML, CSS and JavaScript.

**Main benefit:** The API is explicit and independently testable while the interface remains small and requires no frontend framework.

**Trade-off:** The team must write browser-side request handling and update pages with JavaScript. Server-side rendering would require less browser code.

## Public Client: REST, Not WebSockets

**Selected option:** Each search is one independent REST request.

**Main benefit:** REST is simple to implement, test and debug, and no persistent connection state is required.

**Trade-off:** REST does not provide continuous bidirectional communication or streamed responses. Neither is needed for deterministic product and stock searches.

## Client Service to Product MCP Server

**Selected option:** MCP over Streamable HTTP on the internal Docker network.

**Main benefit:** The Client Service and Product MCP Server remain independent components and can run in separate containers.

**Trade-off:** This creates another internal endpoint and requires service configuration. A local standard-input/output transport would be simpler only if both components ran together.

## Product MCP Server to Product API

**Selected option:** Read-only REST requests to the supplied Product API.

**Main benefit:** Product data always comes from its authoritative source and is never duplicated locally.

**Trade-off:** Product searches may be temporarily unavailable when the external service is slow or offline. The service must return a clear error rather than inventing or permanently caching data.

## Stock Access for the Public Client

**Selected option:** Narrow, read-only SQLAlchemy queries implemented by the server-side Client Service.

**Main benefit:** Anonymous visitors can consult availability without receiving unrestricted database access.

**Trade-off:** Every public query must be deliberately implemented and tested; arbitrary SQL is not exposed.

## Authentication Transport

**Selected option:** A signed, HTTP-only, same-site session cookie for the Backoffice. State-changing requests also use CSRF protection.

**Main benefit:** JavaScript cannot read the cookie, and the browser attaches it automatically to Backoffice requests.

**Trade-off:** This mechanism is intended for the browser-based Backoffice. An unrelated API client would require a separate authentication method.

## AI Scope

No AI agent or AI Query Service is implemented. The public client returns deterministic product and stock results from MCP tools and read-only database queries.
