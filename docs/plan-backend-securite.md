# Plan d'action — Backend / Sécurité / Base de données

Ce document définit mon rôle dans le projet HBntory (Lead Backend), corrige la répartition initiale (session cookie au lieu de JWT, pour rester cohérent avec `architecture_EN.md` et `communication-strategies.md`), et sert de checklist de suivi.

## Répartition d'équipe (résumé corrigé)

| Rôle | Responsable | Contenu |
| --- | --- | --- |
| Lead Backend / Sécurité / DB | Moi | Task 1 (DB + Backoffice foundation), Task 2 (Auth + RBAC), endpoints REST Backoffice |
| Frontend | Personne 2 | Backoffice UI (login, dashboard admin, dashboard user) |
| IA / MCP | Personne 3 | Task 4 (MCP Server) uniquement |
| Task 7 (Intégration/Tests/README) | Tout le monde, chacun sur sa partie | Backend: tests + doc API + README backend |

**Task 5 (AI Query Service) et Task 6 (Client Web Interface) : hors périmètre**, décision actée avec le responsable du projet — on ne les fait pas. Ancienne note ("trou non résolu — backend de `client_web`") retirée : elle partait d'une lecture de `architecture_EN.md`/`mvp-definition.md` (docs internes d'architecture) plutôt que de l'énoncé officiel des tâches. En relisant le vrai texte de Task 5/6 : c'est l'AI Query Service (Task 5, jamais construit) qui devait se connecter au MCP server et gérer l'accès au stock (au choix : étendre le MCP server, un DB MCP tool, ou une API interne) — pas `client_web` (Task 6), qui n'aurait été qu'une page appelant l'endpoint de Task 5. Comme Task 5/6 ne se font pas, `client_web/` reste un squelette statique (JS vides) sans que ce soit un manque à combler.

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
- [ ] Migration Alembic initiale — **pas encore fait**, on utilise seulement `Base.metadata.create_all()` pour l'instant. À faire avant une vraie mise en prod / Task 7.
- [x] Validation métier stock (Task 4) — `app/services/stock_services.py`, testée end-to-end en SQLite (API Produit mockée) :
  - [x] quantité entière positive obligatoire (`_validate_stock_operation`, partagée par add/remove).
  - [x] branche valide vérifiée avant toute opération.
  - [x] `add_stock` : incrémente si la ligne existe déjà, sinon valide le produit via l'API externe puis crée la ligne.
  - [x] `remove_stock` : rejette si la ligne n'existe pas, rejette si la quantité à retirer dépasse le stock disponible.
  - [x] product_id validé contre le Product API externe (`GET {PRODUCT_API_URL}/api/v1/products/{id}`) **uniquement à la création d'une nouvelle ligne** — pas re-vérifié à chaque réapprovisionnement d'une ligne déjà existante (décision assumée : le produit a déjà été validé une fois).
  - [ ] **Point d'attention non résolu** : l'API Produit externe utilise des ID exemples type SKU (`"HB-LAP-1001"`), alors que `Stock.product_id` est un `Integer` en base — à clarifier avec l'équipe/le prof avant intégration réelle (peut nécessiter de changer le type de la colonne).
  - [ ] Pas encore de tests automatisés formels (pytest) — validé pour l'instant par un script ad hoc, à formaliser en Task 7.
- [x] Documenter le schéma (`docs/db-schema.md`) + justification des choix, tenu à jour à chaque changement.

## Task 2 — Authentication and Authorization

- [ ] Login : vérification credentials, rejet des users soft-deleted/inactifs.
- [x] Hash des mots de passe avec **Argon2id** (déjà décidé dans l'architecture) — documenté (mécanisme, hashing, vérification, pourquoi SHA256 seul est insuffisant) dans `docs/password-security.md`.
- [ ] Session cookie signée, HTTP-only, same-site à la connexion réussie.
- [ ] Middleware/dépendance FastAPI qui recharge l'utilisateur à chaque requête protégée et vérifie : rôle, statut actif, branche.
- [ ] Protection CSRF sur les routes state-changing (POST/PUT/DELETE).
- [ ] RBAC :
  - [ ] `admin` : accès gestion users, refusé sur endpoints stock.
  - [ ] `common` : accès stock limité à sa branche (dérivée du compte authentifié, jamais du body/paramètre client), refusé sur endpoints users.
- [ ] Logout (invalidation de session côté serveur).
- [ ] Tests : accès anonyme refusé, cross-branch refusé, priv-esc common→admin refusé, soft-deleted ne peut pas se connecter.
- [ ] Rate limiting basique sur `/login` (protection brute-force) — bon ajout portfolio sécurité, à voir si le temps permet.
- [ ] Documentation : stratégie Argon2id, stratégie session/CSRF, matrice RBAC.

## Section 3 — Backoffice Functionalities

Section de la consigne pas anticipée dans la répartition initiale (absente jusqu'ici de ce plan). Découpage par sous-tâche :

| Sous-tâche | Qui | Notes |
| --- | --- | --- |
| 1. Common User Stock Operations | Moi | Logique déjà écrite (`app/services/stock_services.py`), reste la couche REST + RBAC branche |
| 2. Admin User Management | Moi | Lié à Task 2 (Auth/RBAC) — CRUD users, soft-delete, changement branche/mot de passe |
| 3. Product API Integration in Backoffice | Moi (point d'entrée backend) | Le backend doit exposer un moyen d'interroger l'API Produit externe ; le frontend (Personne 2) consomme cet endpoint. Jamais de détails produit dupliqués en local DB |
| 4. Backoffice Interface | Personne 2 (nico) | HTML/CSS des 4 pages déjà mergé sur `master`. Mon rôle : fournir des endpoints REST fonctionnels à brancher dessus |

- [ ] 1 — Common User Stock Operations :
  - [ ] `POST /stock/add` (branche déduite de la session, jamais du body client — cf. RBAC Task 2)
  - [ ] `POST /stock/remove`
  - [ ] `GET /stock` (liste produits en stock, filtrée sur la branche de l'utilisateur connecté)
  - [ ] `GET /stock/{product_id}` (quantité disponible pour un produit, dans sa branche)
  - [ ] Backend doit rejeter toute tentative d'opérer sur une branche différente de celle de l'utilisateur (pas seulement côté UI)
- [ ] 2 — Admin User Management :
  - [ ] `GET /users` (liste)
  - [ ] `POST /users` (création, common uniquement — un admin ne se crée pas via cet endpoint sans contrôle)
  - [ ] `PUT /users/{id}` (changement branche, changement mot de passe)
  - [ ] `DELETE /users/{id}` (soft-delete : `status=Inactive` + `deleted_at`, jamais de suppression physique)
  - [ ] Vérifier : un user soft-deleted ne peut plus se connecter (Task 2, check au login), et son historique de stock reste intact (déjà garanti par le schéma — `Stock` ne référence aucun `user_id`)
- [ ] 3 — Product API Integration in Backoffice :
  - [ ] Décider du mode d'exposition (proxy backend vers l'API Produit, ou sélecteur/recherche côté frontend qui appelle l'API Produit directement) — à trancher avant de coder
  - [ ] Aucune donnée produit (nom, prix, description) stockée en local, uniquement `product_id` — déjà respecté par le schéma
  - [ ] Résoudre le point d'attention `product_id` (Integer local vs SKU string API externe, cf. Task 1) avant d'intégrer pour de vrai
- [ ] 4 — Backoffice Interface : côté moi, s'assurer que les endpoints REST ci-dessus répondent avec des codes HTTP et payloads exploitables par les pages déjà présentes dans `backoffice/static/`

## Endpoints REST Backoffice à livrer

- [ ] `POST /login`
- [ ] `POST /logout`
- [ ] `GET /users` (admin)
- [ ] `POST /users` (admin)
- [ ] `PUT /users/{id}` (admin — modification, changement branche/mot de passe)
- [ ] `DELETE /users/{id}` (admin — soft delete)
- [ ] `GET /stock` (common, filtré sur sa branche)
- [ ] `POST /stock/add` (common)
- [ ] `POST /stock/remove` (common)

Chaque endpoint : valider entrée, appliquer RBAC en backend (pas seulement cacher un bouton côté front), retourner codes HTTP corrects (401/403/404/409/422).

## Task 7 — Ma part (tests, sécurité, doc, README)

- [ ] Tests backend automatisés (modèles, validation stock, auth, RBAC).
- [ ] Tests sécurité ciblés :
  - [ ] injection via product_id / paramètres stock
  - [ ] IDOR (accès stock d'une autre branche via manipulation d'ID)
  - [ ] priv-esc common → admin
  - [ ] contournement soft-delete
  - [ ] absence de CSRF token sur requête state-changing
- [ ] Documentation API (endpoints, payloads, codes retour).
- [ ] README section Backend (setup DB, migrations, seed, lancement service).

## Notes de cohérence avec les docs existants

- Si `architecture_FR.md` existe et n'a pas encore été mis à jour (session cookie / AI en Phase 7 optionnelle), il faudra le resynchroniser avec `architecture_EN.md`.
- Ne pas réintroduire JWT dans le code ou les specs d'API sans rediscuter et remettre à jour `communication-strategies.md`.
