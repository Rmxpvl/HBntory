# HBntory — Initial Service Diagram

![HBntory non-AI Backoffice service diagram](./initial-service-diagram.svg)

## Connections

| Source | Destination | Communication |
| --- | --- | --- |
| Internal browser | Backoffice Service | REST with signed session cookie |
| Backoffice Service | PostgreSQL | SQLAlchemy |
| Backoffice Service | External Product API | Read-only REST |

The Product API supplies product information. PostgreSQL stores users, branches, product IDs and stock quantities. No AI or MCP service belongs to the agreed implementation scope.
