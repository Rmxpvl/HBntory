# HBntory — Service Diagram (as delivered)

**This replaces the original planning diagram** — see `mvp-definition.md`
for that original plan and `architecture.md` for the full explanation
of what changed and why.

![HBntory delivered service diagram: a single Backoffice service serves both authenticated pages and the public catalogue directly, with no gateway; the Product MCP Server is independent and has no consumer](./initial-service-diagram.svg)

## Connections

| Source | Destination | Communication |
| --- | --- | --- |
| Internal browser | Backoffice Service | REST with signed session cookie |
| Public browser | Backoffice Service | REST, anonymous, same app as above |
| Backoffice Service | SQLite | SQLAlchemy |
| Backoffice Service | External Product API | Read-only REST (used by both the authenticated and the public catalogue endpoints) |
| Product MCP Server | External Product API | Read-only REST |

There is no API Gateway: both internal (authenticated) and public
(anonymous) browser traffic reach the Backoffice service directly, which
is the single entry point. The Product API is the authority for product
information — both the authenticated Backoffice pages and the public
catalogue call it through the same `product_client.py` module, not through
the MCP server. SQLite stores users, branches, and stock; the public
catalogue path never touches it. The Product MCP Server is independent and
verified on its own, but nothing in this project calls it — the AI Query
Service that was meant to was excluded from the final scope, along with
the API Gateway shown in the original plan.
