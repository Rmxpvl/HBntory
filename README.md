# HBntory

Ce document existe en français puis en anglais ci-dessous.
This document exists in French, then in English below.

---

## Français

Un Backoffice de gestion de stock pour une entreprise possédant plusieurs
agences physiques, plus un catalogue produits public. Projet scolaire
(Holberton).

**À lire en premier :** ce README décrit uniquement ce qui a été réellement
construit et vérifié. Là où le plan initial prévoyait quelque chose qui
n'existe pas ici (une API Gateway, un AI Query Service, un déploiement
PostgreSQL complet), c'est signalé explicitement plutôt que laissé
ambigu — voir ["Périmètre final actée"](#périmètre-final-acté) ci-dessous.

### Sommaire

1. [Vue d'ensemble du projet](#1-vue-densemble-du-projet)
2. [Membres de l'équipe et responsabilités](#2-membres-de-léquipe-et-responsabilités)
3. [Résumé de l'architecture finale](#3-résumé-de-larchitecture-finale)
4. [Prérequis et installation](#4-prérequis-et-installation)
5. [Comment lancer chaque service livré](#5-comment-lancer-chaque-service-livré)
6. [Comment initialiser la base de données](#6-comment-initialiser-la-base-de-données)
7. [Comment accéder au Backoffice et l'utiliser](#7-comment-accéder-au-backoffice-et-lutiliser)
8. [Statut de l'interface Client Web publique](#8-statut-de-linterface-client-web-publique)
9. [Principales décisions techniques](#9-principales-décisions-techniques)
10. [Limitations connues et compromis](#10-limitations-connues-et-compromis)
11. [Fonctionnalités optionnelles implémentées](#11-fonctionnalités-optionnelles-implémentées)

### Périmètre final acté

Deux parties du plan initial ont été retirées d'un commun accord avec le
responsable du projet, et **ne font pas** partie de cette livraison :

- **L'AI Query Service** (réponse aux questions en langage naturel) — non
  construit. Rien dans ce projet ne répond à une question en langage
  naturel.
- **L'API Gateway** (un point d'entrée unique de routage devant des
  services Backoffice/Client séparés) — non construite. Le Backoffice est
  un unique service FastAPI ; il sert directement les pages authentifiées
  et le catalogue public.

Tout le reste décrit dans ce README existe et a été lancé et vérifié —
voir les preuves "QA manuelle" liées en Section 5.

### 1. Vue d'ensemble du projet

HBntory permet :

- à un utilisateur **admin** de gérer les comptes utilisateurs communs
  (créer, modifier, changer le mot de passe, désactiver) depuis une
  interface Backoffice ;
- à un utilisateur **commun** de gérer le stock (ajouter, retirer, lister,
  rechercher) de la seule agence à laquelle il est rattaché ;
- à un visiteur **anonyme** de parcourir un catalogue produits public
  (recherche par mot-clé, filtre par catégorie) sans aucun compte requis.

Les informations produit (nom, prix, catégorie, description) proviennent
toujours d'une API Produit externe fournie — HBntory ne stocke ni
n'invente jamais de détail produit localement, seulement un identifiant
numérique de produit et une quantité par agence.

Un **serveur MCP Produit** indépendant existe également, exposant le
catalogue produits sous forme d'outils MCP. Il est complet et vérifié
indépendamment, mais n'a aucun consommateur dans cette livraison (voir
"Périmètre final acté" ci-dessus).

### 2. Membres de l'équipe et responsabilités

| Membre | Responsabilité |
| --- | --- |
| Rémy Pinville | Lead Backend / Sécurité / Base de données — conception du schéma, authentification & autorisation, endpoints REST du Backoffice, tests, documentation |
| Nicolas J | Frontend — Interface Backoffice (pages login, stock, gestion des utilisateurs) |
| Aleksandre Loladze | Serveur MCP Produit |

Voir [`docs/plan-backend-securite.md`](docs/plan-backend-securite.md) pour
la répartition détaillée, tâche par tâche, et son statut.

### 3. Résumé de l'architecture finale

```
Navigateur interne ─┐
                     ├──▶ Backoffice (FastAPI) ──▶ SQLite (users, branches, stocks)
Navigateur public ───┘                       └──▶ API Produit externe (lecture seule)

Serveur MCP Produit ──▶ API Produit externe (lecture seule)
   (indépendant, aucun consommateur dans ce projet)
```

Un unique service FastAPI (`backoffice/`) sert tout ce qui est accessible
depuis un navigateur : les pages authentifiées (`/login`, `/stock`,
`/users`) et la page catalogue publique (`/`, servie par `client_web/`) —
il n'y a aucune passerelle devant, et aucun service séparé pour la page
publique. Les deux côtés (authentifié et public) appellent l'API Produit
externe via le même code (`app/services/product_client.py`) ; le côté
public ne touche jamais la base de données.

Détail complet, diagrammes de flux de données, et règles de sécurité :
[`docs/architecture.md`](docs/architecture.md) (français puis anglais) et
[`docs/backoffice-ui-approach.md`](docs/backoffice-ui-approach.md).

### 4. Prérequis et installation

- Python 3.11+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  (nécessaire uniquement pour lancer l'API Produit externe et,
  optionnellement, la dépendance du serveur MCP Produit envers elle)
- Un terminal (les exemples ci-dessous utilisent PowerShell ; bash
  fonctionne aussi avec les adaptations de syntaxe évidentes)

```powershell
git clone <ce dépôt>
cd HBntory
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backoffice\requirements.txt
```

### 5. Comment lancer chaque service livré

Instructions complètes, pas à pas, en français, avec un tableau de
dépannage pour les problèmes qu'on a réellement rencontrés en le mettant
en place : **[`docs/local-run-guide.md`](docs/local-run-guide.md)**.

Résumé de ce qui existe et comment le lancer :

| Service | Ce que c'est | Comment le lancer |
| --- | --- | --- |
| API Produit externe | Fournie, tierce, catalogue produits en lecture seule | `git clone https://github.com/hbtn-edu/hbntory-products-api.git` puis `docker compose up -d --build` depuis ce dossier |
| Backoffice | L'application principale : pages authentifiées + catalogue public | `python -m uvicorn app.main:app --port 5000` depuis `backoffice/`, après le seed (Section 6) |
| Serveur MCP Produit | Pont MCP indépendant vers l'API Produit (aucun consommateur dans ce projet) | `python server.py` depuis `product_mcp_server/`, après `pip install -r requirements.txt` — voir [`product_mcp_server/README.md`](product_mcp_server/README.md) |

Preuves de QA manuelle pour le flux complet livré (health check API
Produit, login Backoffice, opérations de stock, gestion des utilisateurs,
appels MCP) : [`docs/manual-qa.md`](docs/manual-qa.md).

### 6. Comment initialiser la base de données

Depuis `backoffice/`, avec `DATABASE_URL`, `ADMIN_PASSWORD` et
`SESSION_SECRET_KEY` définies (voir `docs/local-run-guide.md`, étape 3,
pour les commandes exactes) :

```powershell
python -m app.seed
```

Ça crée les tables (`Base.metadata.create_all()`, pas d'outil de
migration) et insère un compte `admin` (mot de passe depuis
`ADMIN_PASSWORD`), trois agences, et du stock d'exemple. C'est idempotent :
relancer la commande complète ce qui manque sans dupliquer les lignes ni
réinitialiser un mot de passe déjà existant.

### 7. Comment accéder au Backoffice et l'utiliser

Une fois initialisé et lancé (Sections 5–6), ouvre
`http://localhost:5000/` — c'est la page catalogue publique. Clique sur
"Se connecter" (ou va directement sur `/login`) pour atteindre le login du
Backoffice.

- **Compte admin** : connecte-toi, liste/crée/modifie/désactive les
  utilisateurs communs, change leur mot de passe ou leur agence. Ne peut
  pas gérer le stock (refusé côté serveur, pas seulement caché dans
  l'interface).
- **Compte common** : connecte-toi, vois ton agence assignée,
  ajoute/retire du stock, recherche ce qui est actuellement en stock. Ne
  peut pas gérer les utilisateurs, et ne peut agir sur aucune agence
  autre que la tienne (l'agence vient toujours de ta session, jamais de
  la page).

Parcours complet, sans captures d'écran :
[`docs/local-run-guide.md`](docs/local-run-guide.md), section "Guide
d'utilisation".

### 8. Comment accéder au catalogue produits public et l'utiliser

Ouvre `http://localhost:5000/` — aucun compte requis. Depuis cette page :

- **Rechercher** un produit par mot-clé (nom, référence) dans la case de
  recherche.
- **Filtrer** par catégorie via le menu déroulant (rempli depuis l'API
  Produit externe).
- Les résultats ne s'affichent qu'après une recherche explicite — la
  page ne liste pas tout le catalogue par défaut à l'ouverture.
- Un bouton "Se connecter" en haut de la page mène vers `/login`
  (Backoffice).

**Construite et fonctionnelle, mais avec un périmètre réduit par rapport
au plan initial.** `client_web/` est un vrai catalogue produits
fonctionnel, servi par l'application Backoffice sur `/`. Elle **n'affiche
pas** le stock ni la disponibilité par agence (uniquement les
informations produit : nom, catégorie, marque, prix), et **n'appelle
pas** le serveur MCP Produit — c'était le plan initial (une case de
question en langage naturel adossée à un AI Query Service), mais comme
l'AI Query Service est hors périmètre, il n'y a rien à appeler pour une
telle case de question. Plutôt que de livrer une page sans IA
fonctionnelle derrière, elle a été reconstruite autour d'une recherche
simple, fonctionnelle, façon magasin en ligne. Détail :
[`client_web/README.md`](client_web/README.md).

### 9. Principales décisions techniques

- **Cookie de session, pas de JWT.** Signé, `HttpOnly`, `SameSite=Lax`.
  Choisi plutôt que JWT car la révocation immédiate d'un utilisateur
  soft-supprimé est plus simple (pas de blocklist/refresh token à gérer),
  et le Backoffice est une application navigateur classique, pas
  consommée par un client tiers.
- **Vraie déconnexion côté serveur**, pas juste suppression du cookie. Un
  compteur `token_version` sur `User` est inclus dans le cookie signé et
  vérifié à chaque requête ; le logout l'incrémente, donc tous les
  cookies déjà émis pour cet utilisateur — pas seulement celui du
  navigateur qui se déconnecte — cessent de fonctionner immédiatement.
- **Argon2id** pour le hachage des mots de passe, avec un hash factice
  fixe utilisé quand un nom d'utilisateur n'existe pas, pour que le temps
  de connexion ne révèle pas quels noms sont réels. Détail complet :
  [`docs/password-security.md`](docs/password-security.md).
- **RBAC appliqué côté serveur**, jamais seulement en cachant un bouton :
  `admin` est refusé sur les routes de stock, `common` est refusé sur les
  routes de gestion des utilisateurs, et l'agence d'un utilisateur commun
  vient toujours de sa session, jamais du corps de la requête.
- **SQLite, pas PostgreSQL**, pour la configuration livrée/documentée —
  voir Section 10.
- **`Base.metadata.create_all()`, pas Alembic.** Évalué et volontairement
  écarté ; voir Section 10.
- **Le catalogue public réutilise le client Product API existant du
  Backoffice** (`product_client.py`) plutôt que de construire un service
  séparé appelant le serveur MCP et interrogeant la base de données — plus
  simple, et le catalogue n'a de toute façon pas besoin de données de
  stock.

### 10. Limitations connues et compromis

- **PostgreSQL n'est pas la base livrée.** Le schéma
  (`docs/db-schema.md`) a été conçu à l'origine pour PostgreSQL, mais la
  configuration locale documentée et testée utilise exclusivement
  SQLite. Un fichier Docker Compose PostgreSQL antérieur et la dépendance
  `psycopg2-binary` ont été retirés plutôt que laissés comme un chemin
  non documenté et non vérifié.
- **Pas de token CSRF explicite.** `SameSite=Lax` mitige les soumissions
  de formulaire cross-site classiques, mais les requêtes qui modifient
  l'état n'ont pas de token CSRF. Documenté comme limitation connue, non
  implémenté.
- **Pas de limitation de débit sur le login.** Non requis par l'énoncé,
  non construit.
- **`create_all()` ne peut pas modifier une table existante.** Un
  changement de schéma impose de supprimer et recréer la base locale — il
  n'y a pas de chemin de migration. (Alembic a été mis en place et évalué
  pendant le développement, puis volontairement retiré — le projet s'est
  arrêté sur `create_all()`, et garder un outil de migration à moitié
  branché et inutilisé prêtait plus à confusion que de n'en avoir aucun.)
- **L'incrément/décrément de la quantité de stock est une
  lecture-puis-écriture, pas une mise à jour SQL atomique.** Des requêtes
  concurrentes d'ajout/retrait sur exactement la même ligne
  (agence, produit) pourraient, en théorie, perdre une mise à jour sous
  une vraie concurrence. Les races d'insertion concurrente et de nom
  d'utilisateur concurrent sont gérées (converties en réponses 400/409
  propres plutôt qu'un crash) ; cette race plus étroite ne l'est pas.
- **Le serveur MCP Produit n'a aucun consommateur.** Complet et vérifié
  indépendamment contre la vraie API Produit, mais rien dans ce projet ne
  l'appelle, puisque l'AI Query Service qui devait le faire est hors
  périmètre.

### 11. Fonctionnalités optionnelles implémentées

- **Filtre catégorie et recherche libre** sur le catalogue public,
  au-delà d'une simple case de recherche — l'API Produit externe
  supporte les deux (`category=`, `q=`), donc les deux sont exposés.
- **Révocation de session réelle côté serveur** (Section 9) — plus
  robuste qu'une approche purement stateless à base de token, que
  l'énoncé aurait pourtant permise.
- **Login résistant au timing** contre l'énumération de noms
  d'utilisateur (Section 9), au-delà de ce qu'une simple vérification
  Argon2id exigerait.

---

## English

An inventory Backoffice for a company with several physical branches, plus
a public product catalogue. Built as a school project (Holberton).

**Read this first:** this README describes only what was actually built
and verified. Where the original plan included something that isn't here
(an API Gateway, an AI Query Service, a PostgreSQL deployment), that's
called out explicitly rather than left ambiguous — see
["Agreed final scope"](#agreed-final-scope) below.

### Table of contents

1. [Project overview](#1-project-overview)
2. [Team members and responsibilities](#2-team-members-and-responsibilities)
3. [Final architecture summary](#3-final-architecture-summary)
4. [Prerequisites and installation](#4-prerequisites-and-installation)
5. [How to run each delivered service](#5-how-to-run-each-delivered-service)
6. [How to initialise the database](#6-how-to-initialise-the-database)
7. [How to access and use the Backoffice](#7-how-to-access-and-use-the-backoffice)
8. [Status of the public Client Web Interface](#8-status-of-the-public-client-web-interface)
9. [Main technical decisions](#9-main-technical-decisions)
10. [Known limitations and trade-offs](#10-known-limitations-and-trade-offs)
11. [Optional features implemented](#11-optional-features-implemented)

### Agreed final scope

Two parts of the original plan were excluded by agreement with the project
supervisor, and are **not** part of this delivery:

- **The AI Query Service** (natural-language question answering) — not
  built. Nothing in this project answers a question in natural language.
- **The API Gateway** (a single routing entry point in front of separate
  Backoffice/Client services) — not built. The Backoffice is one FastAPI
  service; it serves both the authenticated pages and the public catalogue
  directly.

Everything else described in this README exists and has been run and
verified — see the "Manual QA" evidence linked in Section 5.

### 1. Project overview

HBntory lets:

- an **admin** user manage common-user accounts (create, edit, change
  password, soft-delete) from a Backoffice UI;
- a **common** user manage stock (add, remove, list, search) for the one
  branch they're assigned to;
- an **anonymous** visitor browse a public product catalogue (search by
  keyword, filter by category) with no account needed.

Product information (name, price, category, description) always comes
from an external, supplied Product API — HBntory never stores or invents
product details locally, only a numeric product ID and a quantity per
branch.

An independent **Product MCP Server** also exists, exposing the product
catalogue as MCP tools. It is complete and independently verified, but has
no consumer in this delivery (see "Agreed final scope" above).

### 2. Team members and responsibilities

| Member | Responsibility |
| --- | --- |
| Rémy Pinville | Lead Backend / Security / Database — schema design, authentication & authorization, Backoffice REST endpoints, tests, documentation |
| Nicolas J | Frontend — Backoffice UI (login, stock, user management pages) |
| Aleksandre Loladze | Product MCP Server |

See [`docs/plan-backend-securite.md`](docs/plan-backend-securite.md) for
the detailed, task-by-task breakdown and status.

### 3. Final architecture summary

```
Internal browser ──┐
                    ├──▶ Backoffice (FastAPI) ──▶ SQLite (users, branches, stocks)
Public browser  ────┘                       └──▶ External Product API (read-only)

Product MCP Server ──▶ External Product API (read-only)
   (independent, no consumer in this project)
```

One FastAPI service (`backoffice/`) serves everything reachable by a
browser: the authenticated pages (`/login`, `/stock`, `/users`) and the
public catalogue page (`/`, backed by `client_web/`) — there is no gateway
in front of it, and no separate service for the public page. Both the
authenticated and public sides call the external Product API through the
same code (`app/services/product_client.py`); the public side never
touches the database.

Full detail, data flow diagrams, and the security rules that back this up:
[`docs/architecture.md`](docs/architecture.md) (French then English) and
[`docs/backoffice-ui-approach.md`](docs/backoffice-ui-approach.md).

### 4. Prerequisites and installation

- Python 3.11+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (only
  needed to run the external Product API and, optionally, the Product MCP
  Server's dependency on it)
- A terminal (examples below use PowerShell; bash works too with the
  obvious syntax changes)

```powershell
git clone <this repository>
cd HBntory
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backoffice\requirements.txt
```

### 5. How to run each delivered service

Full step-by-step instructions, in French, with a troubleshooting table
for the exact problems we actually hit while setting this up:
**[`docs/local-run-guide.md`](docs/local-run-guide.md)**.

Summary of what exists and how to start it:

| Service | What it is | How to run it |
| --- | --- | --- |
| External Product API | Supplied, third-party, read-only product catalogue | `git clone https://github.com/hbtn-edu/hbntory-products-api.git` then `docker compose up -d --build` from that folder |
| Backoffice | The main app: authenticated pages + public catalogue | `python -m uvicorn app.main:app --port 5000` from `backoffice/`, after seeding (Section 6) |
| Product MCP Server | Independent MCP bridge to the Product API (no consumer in this project) | `python server.py` from `product_mcp_server/`, after `pip install -r requirements.txt` — see [`product_mcp_server/README.md`](product_mcp_server/README.md) |

Manual QA evidence for the full delivered flow (Product API health check,
Backoffice login, stock operations, user management, MCP tool calls):
[`docs/manual-qa.md`](docs/manual-qa.md).

### 6. How to initialise the database

From `backoffice/`, with `DATABASE_URL`, `ADMIN_PASSWORD` and
`SESSION_SECRET_KEY` set (see `docs/local-run-guide.md` Step 3 for exact
commands):

```powershell
python -m app.seed
```

This creates the tables (`Base.metadata.create_all()`, no migration tool)
and inserts one `admin` account (password from `ADMIN_PASSWORD`), three
branches, and sample stock. It's idempotent: re-running it fills in
anything missing without duplicating rows or resetting an existing
password.

### 7. How to access and use the Backoffice

Once seeded and running (Sections 5–6), open `http://localhost:5000/` —
this is the public catalogue page. Click "Se connecter" (or go directly to
`/login`) to reach the Backoffice login.

- **admin** account: log in, list/create/edit/soft-delete common users,
  change their password or branch. Cannot manage stock (enforced
  server-side, not just hidden in the UI).
- **common** account: log in, see your assigned branch, add/remove stock,
  search what's currently in stock. Cannot manage users, and cannot act on
  any branch other than your own (the branch always comes from your
  session, never from the page).

Full walkthrough with screenshots-free step descriptions:
[`docs/local-run-guide.md`](docs/local-run-guide.md), "Guide
d'utilisation" section.

### 8. How to access and use the public product catalogue

Open `http://localhost:5000/` — no account needed. From that page:

- **Search** for a product by keyword (name, reference) in the search box.
- **Filter** by category via the dropdown (populated from the external
  Product API).
- Results only appear after an explicit search — the page doesn't list
  the whole catalogue by default on load.
- A "Se connecter" button at the top of the page leads to `/login`
  (Backoffice).

**Built and working, but scoped down from the original plan.** `client_web/`
is a real, functional product catalogue, served by the Backoffice app at
`/`. It does **not** show stock or branch availability (product
information only: name, category, brand, price), and does **not** call
the Product MCP Server — that was the original plan (a natural-language
question box backed by an AI Query Service), but since the AI Query
Service is excluded from scope, there is nothing for a question box to
call. Rather than ship a page with no working AI behind it, it was rebuilt
around a plain, working online-store-style search instead. Detail:
[`client_web/README.md`](client_web/README.md).

### 9. Main technical decisions

- **Session cookie, not JWT.** Signed, `HttpOnly`, `SameSite=Lax`. Chosen
  over JWT because immediate revocation of a soft-deleted user is simpler
  (no blocklist/refresh-token machinery needed), and the Backoffice is a
  classic browser app, not consumed by a third-party client.
- **Real server-side logout**, not just cookie deletion. A `token_version`
  counter on `User` is embedded in the signed cookie and checked on every
  request; logout increments it, so every cookie previously issued for
  that user — not only the one in the browser that logged out — stops
  working immediately.
- **Argon2id** for password hashing, with a fixed dummy hash used when a
  username doesn't exist, so login timing doesn't leak which usernames are
  real. Full write-up: [`docs/password-security.md`](docs/password-security.md).
- **RBAC enforced server-side**, never only by hiding a button: `admin`
  is rejected on stock routes, `common` is rejected on user-management
  routes, and a common user's branch always comes from their session, never
  from the request body.
- **SQLite, not PostgreSQL**, for the delivered/documented setup — see
  Section 10.
- **`Base.metadata.create_all()`, not Alembic.** Evaluated and deliberately
  not adopted; see Section 10.
- **The public catalogue reuses the Backoffice's existing Product API
  client** (`product_client.py`) instead of building a separate service
  that calls the MCP server and queries the database — simpler, and the
  catalogue never needs stock data in the first place.

### 10. Known limitations and trade-offs

- **PostgreSQL is not the delivered database.** The schema
  (`docs/db-schema.md`) was originally designed for it, but the
  documented, tested local setup uses SQLite exclusively. An earlier
  PostgreSQL Docker Compose file and the `psycopg2-binary` dependency were
  removed rather than left as an undocumented, unverified path.
- **No explicit CSRF token.** `SameSite=Lax` mitigates ordinary
  cross-site form submissions, but state-changing requests have no CSRF
  token. Documented as a known limitation, not implemented.
- **No login rate limiting.** Not required by the task brief, not built.
- **`create_all()` can't alter an existing table.** A schema change
  requires dropping and recreating the local database — there is no
  migration path. (Alembic was set up and evaluated during development,
  then deliberately removed — the project settled on `create_all()`, and
  keeping an unused, half-wired migration tool around was more confusing
  than having none.)
- **The stock quantity increment/decrement is a read-then-write, not an
  atomic SQL update.** Concurrent add/remove requests on the exact same
  (branch, product) row could, in theory, lose an update under real
  concurrency. Concurrent-insert and concurrent-username races are handled
  (converted to clean 400/409 responses instead of crashing); this
  narrower race is not.
- **The Product MCP Server has no consumer.** Complete and independently
  verified against the real Product API, but nothing in this project calls
  it, since the AI Query Service that was meant to was excluded from
  scope.

### 11. Optional features implemented

- **Category filter and free-text search** on the public catalogue, beyond
  a single search box — the external Product API supports both
  (`category=`, `q=`), so both are exposed.
- **Real server-side session revocation** (Section 9) — stronger than a
  purely stateless signed-token approach, which the task brief would have
  allowed.
- **Timing-safe login** against username enumeration (Section 9), beyond
  what a minimal Argon2id check would require.
