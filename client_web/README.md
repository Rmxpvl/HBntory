# Client Web Interface

Ce document existe en français puis en anglais ci-dessous.
This document exists in French, then in English below.

---

## Français

Un catalogue produits public et anonyme : recherche par mot-clé, filtre
par catégorie, parcours des résultats. Aucune connexion requise.

**Task 5 (AI Query Service) et Task 6 (Client Web Interface, telle que
spécifiée à l'origine — une case de question en langage naturel adossée à
un AI Query Service) sont hors périmètre pour ce projet** — décidé avec le
responsable du projet. Voir `docs/plan-backend-securite.md` pour le
contexte. Cette page a d'abord été construite autour de cette
expérience de case de question IA ; comme Task 5 n'allait jamais exister,
elle a été reconstruite en simple catalogue à la place, qui n'a pas besoin
d'un AI Query Service pour être utile.

### Fonctionnement

- `js/api.js` appelle les endpoints publics (sans authentification) du
  Backoffice : `GET /api/public/products` (`?q=` et `?category=`
  optionnels) et `GET /api/public/categories` — tous deux servis par la
  même application que le Backoffice, en relais vers l'API Produit
  externe.
- `js/app.js` relie le formulaire de recherche et le sélecteur de
  catégorie à ces appels et affiche les résultats.
- `js/config.js` pointe par défaut vers `/api/public` (chemin relatif,
  fonctionne sur n'importe quel hôte/port puisque cette page et le
  Backoffice sont la même application).

---

## English

A public, anonymous product catalogue: search by keyword, filter by
category, browse the results. No login required.

**Task 5 (AI Query Service) and Task 6 (Client Web Interface, as originally
specified — a natural-language question box backed by an AI Query
Service) are out of scope for this project** — decided with the project
supervisor. See `docs/plan-backend-securite.md` for context. This page was
initially built around that AI question-box UX; since Task 5 was never
going to exist, it was rebuilt as a plain catalogue instead, which doesn't
need an AI Query Service to be useful.

### How it works

- `js/api.js` calls the Backoffice's public (unauthenticated) endpoints:
  `GET /api/public/products` (optional `?q=` and `?category=`) and
  `GET /api/public/categories` — both served by the same app as the
  Backoffice, proxying the external Product API.
- `js/app.js` wires the search form and category select to those calls and
  renders the results.
- `js/config.js` points at `/api/public` by default (relative, works on any
  host/port since this page and the Backoffice are the same app).
