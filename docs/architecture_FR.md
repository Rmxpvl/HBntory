# HBntory — Architecture du système

## 1. Périmètre (tel que livré)

Ce document décrit le système réellement construit, pas le plan initial en
plusieurs phases. Voir `mvp-definition.md` pour le plan d'origine et ce qui
en a été retiré, d'un commun accord avec le responsable du projet.

HBntory, tel que livré, est une plateforme de gestion des stocks pour une
entreprise possédant plusieurs agences. Il comprend :

- **le Backoffice** — un unique service FastAPI qui authentifie les
  utilisateurs internes (`admin`, `common`) et sert, sur cette même
  application, une page publique anonyme de catalogue produits ;
- **SQLite** comme base de données locale documentée et testée pour les
  utilisateurs, agences et stocks (voir "Limitations connues" pour le
  statut de PostgreSQL) ;
- **l'API Produit externe fournie**, en lecture seule ;
- **un serveur MCP Produit indépendant** (`product_mcp_server/`) exposant
  des outils contrôlés via MCP.

Il n'y a **pas d'API Gateway**. Il n'y a **pas d'AI Query Service**. Les
deux faisaient partie du plan initial (`mvp-definition.md`, Phases 1 et 7)
et ont été retirés du périmètre final, d'un commun accord avec le
responsable du projet — voir la section "Hors périmètre" plus bas.

## 2. Composants et responsabilités

### Service Backoffice

Le Backoffice (`backoffice/`) est un unique service FastAPI doté d'une
interface simple en HTML, CSS et JavaScript. Il sert directement deux
choses, sans aucune passerelle devant lui :

- **Les pages authentifiées** (`/login`, `/stock`, `/users`) :
  - authentifie les utilisateurs internes via un cookie de session signé,
    `HttpOnly`, `SameSite=Lax` ;
  - applique les rôles et restrictions d'agence côté serveur, pas
    seulement dans l'interface ;
  - permet à l'unique `admin` de lister, créer, modifier et désactiver les
    utilisateurs communs, et de changer leur mot de passe ou leur agence ;
  - interdit à `admin` toute opération sur les stocks ;
  - permet aux utilisateurs communs de consulter, lister, ajouter et
    retirer du stock uniquement dans leur agence ;
  - récupère les informations produit auprès de l'API Produit externe via
    des requêtes REST en lecture seule (`app/services/product_client.py`).
- **La page catalogue publique** (`/`, servie par `client_web/`) :
  - anonyme, aucune session requise ;
  - permet aux visiteurs de rechercher le catalogue par mot-clé et de
    filtrer par catégorie (`GET /api/public/products`,
    `GET /api/public/categories`) ;
  - interroge l'API Produit externe directement via le même module
    `product_client.py` que le côté authentifié — **pas** via le serveur
    MCP Produit, et sans aucun accès à la base de données.

Il n'existe qu'un seul administrateur, nommé `admin`. Chaque utilisateur
commun est rattaché à une seule agence. Le serveur détermine cette agence
à partir de la session authentifiée, sans jamais faire confiance à une
agence transmise par le navigateur.

### Base de données locale

SQLite (un simple fichier, `dev.db` par défaut) est la base de données
locale documentée et testée. Elle contient uniquement :

- `users` : nom d'utilisateur, empreinte du mot de passe, rôle, agence,
  état de suppression logique, et un compteur `token_version` utilisé
  pour la révocation de session ;
- `branches` : identifiant et localisation de l'agence ;
- `stocks` : agence, identifiant numérique externe du produit et quantité
  disponible.

Elle ne contient ni nom, ni SKU, ni description, ni prix, ni image, ni
métadonnée de produit. Voir "Limitations connues" pour le statut de
PostgreSQL.

### API Produit externe

L'API fournie constitue la source de référence des informations produit.
Elle :

- liste les produits, avec filtres optionnels par catégorie et recherche
  libre ;
- renvoie les détails d'un produit à partir de son identifiant numérique
  ou de son SKU ;
- est accessible uniquement en lecture ;
- ne gère pas les quantités de stock propres à HBntory.

Le Backoffice vérifie l'existence d'un produit auprès de cette API avant
de créer une ligne de stock. Seul l'identifiant numérique canonique `id`
renvoyé par l'API est conservé — pas le champ `sku`, distinct.

### Serveur MCP Produit

`product_mcp_server/` est un pont indépendant vers l'API Produit externe,
exposant deux outils via MCP (Streamable HTTP) :

- `list_products` : résumés de produits, paginés et allégés ;
- `get_product_details` : un produit complet par identifiant numérique ou
  SKU.

C'est un simple pont, sans agent IA, sans état. **Rien dans ce projet ne
l'utilise actuellement** — l'AI Query Service qui devait le faire (Phase 7
du plan initial) n'a jamais été construit, conformément au périmètre final
retenu. Il est livré complet et vérifié indépendamment contre la vraie API
Produit (voir `product_mcp_server/README.md`), prêt à être branché à un
agent dans un futur développement.

## 3. Circulation des données

### Authentification du Backoffice

1. Le navigateur transmet ses identifiants directement au Backoffice
   (`POST /api/auth/login`) — aucune passerelle devant.
2. Le Backoffice récupère le compte actif et vérifie le mot de passe à
   partir de son empreinte Argon2id (avec un hash factice fixe utilisé
   quand le nom d'utilisateur n'existe pas, pour ne pas laisser fuir
   quels noms sont réels via le temps de réponse).
3. Une authentification réussie crée un cookie de session signé,
   `HttpOnly`, contenant l'identifiant de l'utilisateur et son
   `token_version` actuel.
4. Chaque requête protégée recharge l'utilisateur depuis la base et
   vérifie : la signature et l'expiration du cookie, le statut actif du
   compte, et que `token_version` correspond toujours (voir "Déconnexion"
   ci-dessous).

### Consultation et modification du stock

1. Un utilisateur commun consulte ou modifie le stock de son agence
   (`GET/POST /api/stock/*`).
2. Le serveur déduit l'agence de la session authentifiée, jamais du corps
   de la requête.
3. SQLAlchemy lit/écrit dans la table locale `stocks`.
4. L'identifiant produit est validé auprès de l'API Produit externe avant
   la création d'une nouvelle ligne de stock.
5. Une vérification d'entier positif et une contrainte `CHECK` en base
   empêchent conjointement toute quantité négative ; un retrait supérieur
   au stock disponible est refusé.

### Recherche dans le catalogue public

1. Un visiteur anonyme recherche ou filtre le catalogue
   (`GET /api/public/products`, `GET /api/public/categories`) — sans
   session, sans passerelle.
2. Le Backoffice appelle directement l'API Produit externe (le même
   module `product_client.py` que le côté authentifié).
3. Les résultats sont renvoyés tels quels ; rien n'est stocké localement,
   et aucune requête en base n'intervient sur ce chemin.

### Déconnexion

1. Le client appelle `POST /api/auth/logout`.
2. Le serveur incrémente le `token_version` de cet utilisateur en base et
   supprime le cookie du navigateur.
3. Comme chaque requête protégée compare le `token_version` du cookie à la
   valeur actuellement stockée, **tous** les cookies déjà émis pour cet
   utilisateur — pas seulement celui qu'on supprime — cessent d'être
   acceptés immédiatement, même si une copie en avait été prise au
   préalable.

## 4. Règles de sécurité et d'intégrité

- Aucun mot de passe n'est enregistré en clair ; Argon2id est utilisé car
  cet algorithme est conçu pour le stockage des mots de passe et résiste
  aux attaques par force brute grâce à des coûts mémoire et de calcul
  configurables (voir `docs/password-security.md`).
- Le Backoffice utilise un cookie de session signé, `HttpOnly`,
  `SameSite=Lax`. **Ce n'est pas une protection CSRF complète** —
  `SameSite=Lax` mitige les soumissions de formulaire cross-site
  classiques, mais aucun token CSRF explicite n'est présent sur les
  requêtes qui modifient l'état. Documenté comme limitation connue, non
  implémenté.
- L'authentification et les autorisations sont contrôlées côté serveur,
  pas seulement cachées dans l'interface.
- `admin` n'est rattaché à aucune agence et ne peut pas modifier les
  stocks ; un utilisateur commun dépend d'une seule agence et ne peut pas
  en sélectionner une autre.
- Un utilisateur désactivé ne peut plus s'authentifier, et une session
  déjà ouverte pour un utilisateur désactivé est rejetée dès la requête
  suivante.
- La déconnexion révoque côté serveur, immédiatement, toutes les sessions
  de cet utilisateur (voir "Déconnexion" ci-dessus) — plus robuste qu'une
  approche à token purement stateless qui ne ferait que supprimer le
  cookie du navigateur.
- Toute modification de stock exige un entier positif et ne peut produire
  une quantité négative (validé en code et garanti par une contrainte en
  base).
- Les points d'accès du catalogue public sont en lecture seule et ne
  requièrent aucune session.
- Les secrets sont fournis par des variables d'environnement et ne sont
  pas versionnés.

## 5. Hors périmètre

Décision actée avec le responsable du projet, pas un oubli :

- **API Gateway** (Phase 1 initiale) — non construit. Le Backoffice est
  l'unique service ; il sert directement les pages authentifiées et le
  catalogue public.
- **AI Query Service** (Phase 7 initiale) — non construit. Aucune réponse
  en langage naturel n'existe nulle part dans ce projet.
- Conséquence : le serveur MCP Produit n'a aucun consommateur dans le
  système livré (voir ci-dessus).
- Le concept initial de "Public Client Service" — son propre backend
  appelant le serveur MCP et interrogeant le stock directement — n'a pas
  non plus été construit ; la page catalogue public réutilise à la place
  le module `product_client.py` déjà existant du Backoffice, via deux
  nouveaux endpoints anonymes. Plus simple, et sans besoin d'accès au
  stock puisque le catalogue n'affiche que des données produit, pas de
  stock.

## 6. Limitations connues

- **PostgreSQL n'est pas la base livrée.** Le schéma a été conçu à
  l'origine pour PostgreSQL et `psycopg2-binary` figurait dans les
  dépendances, mais la configuration locale documentée et testée utilise
  exclusivement SQLite ; le fichier Docker Compose PostgreSQL inutilisé
  et la dépendance ont été retirés plutôt que laissés comme un chemin non
  documenté et non vérifié. Passer à PostgreSQL demanderait de retester
  le flux complet contre cette base.
- **Pas de token CSRF explicite.** Voir Section 4.
- **Pas de limitation de débit sur le login.** Non implémenté, non requis
  par l'énoncé.
- **`Base.metadata.create_all()`, pas de migrations.** Il crée les tables
  manquantes mais ne peut pas modifier une table existante — un
  changement de schéma impose de supprimer et recréer la base locale.
  Alembic a été évalué et volontairement écarté pour le périmètre de ce
  projet.

## 7. Livrables associés

- [Définition du MVP](mvp-definition.md) — le plan initial et ce qui en a
  été retiré.
- [Schéma initial des services](initial-service-diagram.md)
- [Stratégie de communication](communication-strategies.md)
- [Guide de lancement local](local-run-guide.md)
- [README du serveur MCP Produit](../product_mcp_server/README.md)
