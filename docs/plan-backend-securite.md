# Plan d'action — Backend / Sécurité / Base de données

Ce document définit mon rôle dans le projet HBntory (Lead Backend), corrige la répartition initiale (session cookie au lieu de JWT, pour rester cohérent avec `architecture_EN.md` et `communication-strategies.md`), et sert de checklist de suivi.

## Répartition d'équipe (résumé corrigé)

| Rôle | Responsable | Contenu |
| --- | --- | --- |
| Lead Backend / Sécurité / DB | Moi | Task 1 (DB + Backoffice foundation), Task 2 (Auth + RBAC), endpoints REST Backoffice |
| Frontend | Personne 2 | Task 6, Backoffice UI (login, dashboard admin, dashboard user), Client Web UI |
| IA / MCP | Personne 3 | Task 4 (MCP Server), Task 5 (AI Query Service, en dernier, optionnel — voir `mvp-definition.md` Phase 7) |
| Task 7 (Intégration/Tests/README) | Tout le monde, chacun sur sa partie | Backend: tests + doc API + README backend |

Décision d'authentification corrigée : **session cookie signée, HTTP-only, same-site + protection CSRF sur les requêtes qui modifient l'état** (pas de JWT). Raison : cohérent avec l'architecture déjà écrite, invalidation immédiate d'un utilisateur soft-deleted plus simple qu'avec un JWT (pas de blocklist/refresh à gérer), et le Backoffice est une app browser classique, pas consommée par un client tiers.

## Task 1 — Database Design and Backoffice Foundation

- [ ] Concevoir le schéma PostgreSQL : `users`, `branches`, `stock`.
  - [ ] `users` : username, password_hash, role (`admin`/`common`), branch_id (nullable pour admin), is_active/deleted_at, created_at, updated_at.
  - [ ] `branches` : id, name.
  - [ ] `stock` : id, branch_id (FK), product_id (identifiant externe numérique), quantity (contrainte >= 0), created_at, updated_at.
- [ ] Contrainte DB : `quantity >= 0` (CHECK constraint), pas seulement validation applicative.
- [ ] Contrainte : un `common` a exactement une branche ; `admin` n'a pas de branche.
- [ ] Implémenter les modèles SQLAlchemy + relations (User↔Branch, Branch↔Stock).
- [ ] Script d'initialisation (seed) :
  - [ ] 1 admin (mot de passe hashé, jamais en clair dans le script/commit).
  - [ ] Au moins 2 branches.
  - [ ] Stock d'exemple suffisant pour tester.
- [ ] Migration Alembic initiale.
- [ ] Validation métier stock :
  - [ ] quantité entière positive obligatoire pour add/remove.
  - [ ] remove refusé si stock insuffisant.
  - [ ] product_id validé contre le Product API externe avant écriture (quand applicable).
- [ ] Documenter le schéma (docs/db-schema.md ou équivalent) + justification des choix (pourquoi pas de table produit locale, pourquoi soft-delete, etc.).

## Task 2 — Authentication and Authorization

- [ ] Login : vérification credentials, rejet des users soft-deleted/inactifs.
- [ ] Hash des mots de passe avec **Argon2id** (déjà décidé dans l'architecture) — documenter pourquoi Argon2id > SHA256 seul (pas de salt/cost factor adapté, trop rapide donc vulnérable au brute-force).
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
