# Client Web Interface

A public, anonymous product catalogue: search by keyword, filter by
category, browse the results. No login required.

**Task 5 (AI Query Service) and Task 6 (Client Web Interface, as originally
specified — a natural-language question box backed by an AI Query
Service) are out of scope for this project** — decided with the project
supervisor. See `docs/plan-backend-securite.md` for context. This page was
initially built around that AI question-box UX; since Task 5 was never
going to exist, it was rebuilt as a plain catalogue instead, which doesn't
need an AI Query Service to be useful.

## How it works

- `js/api.js` calls the Backoffice's public (unauthenticated) endpoints:
  `GET /api/public/products` (optional `?q=` and `?category=`) and
  `GET /api/public/categories` — both served by the same app as the
  Backoffice, proxying the external Product API.
- `js/app.js` wires the search form and category select to those calls and
  renders the results.
- `js/config.js` points at `/api/public` by default (relative, works on any
  host/port since this page and the Backoffice are the same app).
