# Plan d'action — Backend / Sécurité / Base de données

Ce document définit mon rôle dans le projet HBntory (Lead Backend), corrige la répartition initiale (session cookie au lieu de JWT, pour rester cohérent avec `architecture_EN.md` et `communication-strategies.md`), et sert de checklist de suivi.

## Répartition d'équipe (résumé corrigé)

| Rôle | Responsable | Contenu |
| --- | --- | --- |
| Lead Backend / Sécurité / DB | Moi | Task 1 (DB + Backoffice foundation), Task 2 (Auth + RBAC), endpoints REST Backoffice |
| Frontend | Personne 2 | Backoffice UI (login, dashboard admin, dashboard user) |
| IA / MCP | Personne 3 | Task 4 (MCP Server) uniquement |
| Task 7 (Intégration/Tests/README) | Tout le monde, chacun sur sa partie | Backend: tests + doc API + README backend |

**Task 5 (AI Query Service) et Task 6 (Client Web Interface) : hors périmètre**, décision actée avec le responsable du projet — on ne les fait pas. Ancienne note ("trou non résolu — backend de `client_web`") retirée : elle partait d'une lecture de `architecture_EN.md`/`mvp-definition.md` (docs internes d'architecture) plutôt que de l'énoncé officiel des tâches. En relisant le vrai texte de Task 5/6 : c'est l'AI Query Service (Task 5, jamais construit) qui devait se connecter au MCP server et gérer l'accès au stock (au choix : étendre le MCP server, un DB MCP tool, ou une API interne) — pas `client_web` (Task 6), qui n'aurait été qu'une page appelant l'endpoint de Task 5. Comme Task 5/6 ne se font pas, `client_web/` a été reconstruit en catalogue produits public fonctionnel (recherche par mot-clé + filtre catégorie, `GET /api/public/products` et `GET /api/public/categories`, anonymes) plutôt que laissé en squelette lié à une IA inexistante — voir `client_web/README.md`.

Conséquence pour Task 4 (MCP Server, déjà fait et vérifié) : il n'aura pas de vrai consommateur (l'AI agent qui devait l'utiliser ne sera pas construit) — à mentionner clairement dans le README/la présentation finale comme un choix de périmètre assumé, pas un oubli.

Décision d'authentification corrigée : **session cookie signée, HTTP-only, same-site + protection CSRF sur les requêtes qui modifient l'état** (pas de JWT). Raison : cohérent avec l'architecture déjà écrite, invalidation immédiate d'un utilisateur soft-deleted plus simple qu'avec un JWT (pas de blocklist/refresh à gérer), et le Backoffice est une app browser classique, pas consommée par un client tiers.

## Task 1 — Database Design and Backoffice Foundation

- [x] Concevoir le schéma PostgreSQL : `users`, `branches`, `stocks`.
  - [x] `users` : username, password_hash, role (`Admin`/`Common`), branch_id (nullable pour admin), status (Active/Inactive, réversible) + `deleted_at` (soft-delete distinct), created_at, updated_at.
  - [x] `branches` : branch_id, localisation. (pas de `name` séparé — un seul champ suffisait, pas justifié d'en ajouter un 2e)
  - [x] `stocks` : stock_id, branch_id (FK, `ON DELETE RESTRICT`), product_id (identifiant externe entier), quantity (contrainte >= 0). **Pas de `created_at`/`updated_at` sur `stocks`** — écart volontaire par rapport à ce plan initial, à assumer ou revoir si l'historique des mouvements de stock devient nécessaire.
- [x] Contrainte DB : `quantity >= 0` (CHECK constraint), pas seulement validation applicative.
- [x] Contrainte : un `Common` a exactement une branche ; `Admin` n'a pas de branche.
- [x] Implémenter les modèles SQLAlchemy + relations (User↔Branch, Branch↔Stock, `back_populates` + `passive_deletes`).
- [x] Script d'initialisation (seed) :
  - [x] 1 admin (mot de passe hashé Argon2, jamais en clair — lu depuis `ADMIN_PASSWORD` en variable d'environnement).
  - [x] 3 branches (Annecy, Thonon-les-bains, Genève).
  - [x] Stock d'exemple par branche, suffisant pour tester. Testé end-to-end en SQLite.
  - [x] Idempotent (vérifie l'existant avant chaque insert).
- [x] Stratégie d'initialisation : `Base.metadata.create_all()` + `app/seed.py` (idempotent). Alembic écarté volontairement, hors périmètre pour ce projet. Limite assumée : `create_all()` ne crée que les tables manquantes et ne modifie pas une table existante, donc un changement de `models.py` impose de supprimer et recréer la base.
- [x] Validation métier stock (Task 4) — `app/services/stock_services.py`, testée end-to-end en SQLite (API Produit mockée) :
  - [x] quantité entière positive obligatoire (`_validate_stock_operation`, partagée par add/remove).
  - [x] branche valide vérifiée avant toute opération.
  - [x] `add_stock` : incrémente si la ligne existe déjà, sinon valide le produit via l'API externe puis crée la ligne.
  - [x] `remove_stock` : rejette si la ligne n'existe pas, rejette si la quantité à retirer dépasse le stock disponible.
  - [x] product_id validé contre le Product API externe (`GET {PRODUCT_API_URL}/api/v1/products/{id}`) **uniquement à la création d'une nouvelle ligne** — pas re-vérifié à chaque réapprovisionnement d'une ligne déjà existante (décision assumée : le produit a déjà été validé une fois).
  - [x] ~~Point d'attention SKU vs Integer~~ — **résolu, pas un problème** : la vraie API Produit a un `id` entier (1 à 40) et un champ `sku` texte séparé. `Stock.product_id` en `Integer` correspond au bon champ (`id`), pas au `sku`. Vérifié contre l'API réelle.
  - [x] Tests automatisés (pytest) — `backoffice/tests/`, 40 tests, aucune dépendance externe (SQLite en fichier temporaire).
- [x] Documenter le schéma (`docs/db-schema.md`) + justification des choix, tenu à jour à chaque changement.

## Task 2 — Authentication and Authorization

- [x] Login : vérification credentials, rejet des users soft-deleted/inactifs. `POST /api/auth/login`, `app/services/auth_services.py::authenticate_user`.
- [x] Hash des mots de passe avec **Argon2id** (déjà décidé dans l'architecture) — documenté (mécanisme, hashing, vérification, pourquoi SHA256 seul est insuffisant) dans `docs/password-security.md`.
- [x] Session cookie signée, HTTP-only, same-site à la connexion réussie. `app/auth/sessions.py`, `app/routes/auth.py`.
- [x] Middleware/dépendance FastAPI qui recharge l'utilisateur à chaque requête protégée et vérifie : rôle, statut actif, branche. `app/auth/current_actor.py::get_current_actor`.
- [ ] Protection CSRF explicite (token) sur les routes state-changing — **non implémentée**. `SameSite=Lax` sur le cookie de session offre une mitigation contre les soumissions de formulaire cross-site basiques, mais ce n'est **pas équivalent** à une protection CSRF par token. Limitation connue, hors périmètre pour ce projet.
- [x] RBAC :
  - [x] `admin` : accès gestion users, refusé sur endpoints stock (`require_admin`, testé dans `test_rbac.py`).
  - [x] `common` : accès stock limité à sa branche (dérivée de la session, jamais du body/paramètre client — `StockChange` n'a même pas de champ `branch_id`), refusé sur endpoints users (`require_common`, testé).
- [x] Logout — **révocation réelle côté serveur**, pas juste suppression du cookie. `User.token_version` est inclus dans le token signé et comparé à chaque requête ; le logout l'incrémente, invalidant immédiatement tous les cookies déjà émis pour cet utilisateur (pas seulement celui du navigateur qui se déconnecte). Testé : un cookie volé avant logout est bien rejeté après (`test_logout_revokes_the_session_server_side`).
- [x] Tests : accès anonyme refusé, cross-branch refusé, priv-esc common→admin refusé, soft-deleted ne peut pas se connecter — `test_rbac.py`, `test_login.py`, `test_current_actor.py`.
- [ ] Rate limiting basique sur `/login` (protection brute-force) — **hors périmètre**, non demandé par l'énoncé, non implémenté. Ce n'est pas un TODO ouvert.
- [x] Documentation : stratégie Argon2id (`docs/password-security.md`), stratégie session/cookie (`docs/backoffice-ui-approach.md`, `docs/local-run-guide.md`), matrice RBAC (ce fichier + `test_rbac.py` comme preuve exécutable).

## Section 3 — Backoffice Functionalities

Section de la consigne pas anticipée dans la répartition initiale (absente jusqu'ici de ce plan). Découpage par sous-tâche :

| Sous-tâche | Qui | Notes |
| --- | --- | --- |
| 1. Common User Stock Operations | Moi | Logique déjà écrite (`app/services/stock_services.py`), reste la couche REST + RBAC branche |
| 2. Admin User Management | Moi | Lié à Task 2 (Auth/RBAC) — CRUD users, soft-delete, changement branche/mot de passe |
| 3. Product API Integration in Backoffice | Moi (point d'entrée backend) | Le backend doit exposer un moyen d'interroger l'API Produit externe ; le frontend (Personne 2) consomme cet endpoint. Jamais de détails produit dupliqués en local DB |
| 4. Backoffice Interface | Personne 2 (nico) | HTML/CSS des 4 pages déjà mergé sur `master`. Mon rôle : fournir des endpoints REST fonctionnels à brancher dessus |

- [x] 1 — Common User Stock Operations :
  - [x] `POST /api/stock/add` (branche déduite de la session, jamais du body client — cf. RBAC Task 2)
  - [x] `POST /api/stock/remove`
  - [x] `GET /api/stock` (liste produits en stock, filtrée sur la branche de l'utilisateur connecté)
  - [x] Vérifier la quantité disponible d'un produit avant retrait : couvert par `GET /api/stock` (une ligne absente = 0 en stock, cohérent dans les deux cas) — pas de route dédiée `GET /stock/{product_id}` (décision : `stock_services.get_quantity()` était du code mort, jamais exposé ni appelé ; supprimé plutôt que branché, l'interface existante suffit).
  - [x] Backend rejette toute tentative d'opérer sur une branche différente de celle de l'utilisateur (pas seulement côté UI) — testé (`test_stock_operations_ignore_a_client_supplied_branch_id`).
- [x] 2 — Admin User Management :
  - [x] `GET /api/users` (liste)
  - [x] `POST /api/users` (création, common uniquement — un admin ne se crée pas via cet endpoint sans contrôle)
  - [x] `PATCH /api/users/{id}` (changement username/branche)
  - [x] `PATCH /api/users/{id}/password` (changement mot de passe, séparé de la modification de profil)
  - [x] `DELETE /api/users/{id}` (soft-delete : `status=Inactive` + `deleted_at`, jamais de suppression physique)
  - [x] Vérifié : un user soft-deleted ne peut plus se connecter, et une session déjà ouverte est rejetée dès la requête suivante (le backend recharge l'utilisateur à chaque appel) ; son historique de stock reste intact (garanti par le schéma — `Stock` ne référence aucun `user_id`).
- [x] 3 — Product API Integration in Backoffice :
  - [x] Mode retenu : proxy backend (`app/services/product_client.py`) — le frontend ne parle jamais directement à l'API Produit externe.
  - [x] Aucune donnée produit (nom, prix, description) stockée en local, uniquement `product_id`.
  - [x] ~~Point d'attention `product_id`~~ — résolu (voir Task 1) : l'API réelle a un `id` entier, `Stock.product_id` est correct tel quel.
- [x] 4 — Backoffice Interface : endpoints REST fonctionnels, branchés sur les pages de `backoffice/static/` (login, stock, users), vérifiés en conditions réelles (navigateur + serveur local).

## Endpoints REST Backoffice livrés

- [x] `POST /api/auth/login`
- [x] `POST /api/auth/logout`
- [x] `GET /api/auth/me`
- [x] `GET /api/users` (admin)
- [x] `POST /api/users` (admin)
- [x] `PATCH /api/users/{id}` (admin — modification username/branche)
- [x] `PATCH /api/users/{id}/password` (admin — changement mot de passe)
- [x] `DELETE /api/users/{id}` (admin — soft delete)
- [x] `GET /api/stock` (common, filtré sur sa branche)
- [x] `POST /api/stock/add` (common)
- [x] `POST /api/stock/remove` (common)
- [x] `GET /api/products` (authentifié — Backoffice)
- [x] `GET /api/public/products`, `GET /api/public/categories` (anonymes — catalogue public `client_web`)
- [x] `GET /api/branches` (admin)

Chaque endpoint : valide l'entrée, applique le RBAC en backend (pas seulement cacher un bouton côté front), retourne des codes HTTP corrects (401/403/404/409/422).

## Task 7 — Ma part (tests, sécurité, doc, README)

- [x] Tests backend automatisés (modèles, validation stock, auth, RBAC) — `backoffice/tests/`, 40 tests.
- [x] Tests sécurité ciblés :
  - [x] injection via product_id / paramètres stock — Pydantic (`StrictInt`, rejet des booléens comme entiers, `extra="forbid"`).
  - [x] IDOR (accès stock d'une autre branche via manipulation d'ID) — `test_stock_operations_ignore_a_client_supplied_branch_id`.
  - [x] priv-esc common → admin — `test_admin_cannot_manage_stock`, `test_common_user_cannot_manage_users`.
  - [x] contournement soft-delete — `test_inactive_user_cannot_log_in`, `test_session_with_stale_token_version_is_rejected`.
  - [x] absence de protection CSRF par token sur requête state-changing — **constatée et documentée comme limitation connue** (pas un test à faire passer : `SameSite=Lax` seul, pas de token CSRF explicite).
- [x] Documentation API (endpoints, payloads, codes retour) — `docs/backoffice-ui-approach.md`, `README.md` (racine).
- [x] README section Backend (setup DB, seed, lancement service) — `README.md` (racine) + `docs/local-run-guide.md`.

## Notes de cohérence avec les docs existants

- Si `architecture_FR.md` existe et n'a pas encore été mis à jour (session cookie / AI en Phase 7 optionnelle), il faudra le resynchroniser avec `architecture_EN.md`.
- Ne pas réintroduire JWT dans le code ou les specs d'API sans rediscuter et remettre à jour `communication-strategies.md`.
