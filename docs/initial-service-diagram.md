# HBntory — Initial Service Diagram

![HBntory service diagram without AI](./initial-service-diagram.svg)

## Connections

| Source | Destination | Communication |
| --- | --- | --- |
| Internal browser | Backoffice Service | REST with signed session cookie |
| Backoffice Service | PostgreSQL | SQLAlchemy |
| Backoffice Service | External Product API | Read-only REST |
| Public browser | Public Client Service | REST, not WebSockets |
| Public Client Service | Product MCP Server | MCP over Streamable HTTP |
| Product MCP Server | External Product API | Read-only REST |
| Public Client Service | PostgreSQL | Controlled, read-only SQLAlchemy queries |

The Product API is the authority for product information. PostgreSQL stores users, branches, external product IDs and stock quantities. The Product MCP Server and public Client Web Interface are part of the planned MVP; only AI agents and the AI Query Service are excluded.
