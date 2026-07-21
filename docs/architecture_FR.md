# HBntory — Architecture du système

## 1. Périmètre

HBntory est une plateforme de gestion des stocks destinée à une entreprise possédant plusieurs agences. Le périmètre retenu, sans intelligence artificielle, comprend :

- un Backoffice authentifié destiné aux utilisateurs internes ;
- PostgreSQL pour les utilisateurs, les agences et les stocks ;
- l'API Produit externe fournie en lecture seule ;
- un serveur MCP Produit exposant des outils contrôlés ;
- une interface web publique permettant des recherches déterministes sur les produits et les stocks.

Les agents IA et l'AI Query Service sont exclus de l'implémentation. Les recherches publiques reposent sur des paramètres REST explicites et des résultats structurés, et non sur des réponses générées par une IA.

## 2. Composants et responsabilités

### Service Backoffice

Le Backoffice est un service FastAPI doté d'une interface simple en HTML, CSS et JavaScript. Il :

- authentifie les utilisateurs internes ;
- applique les rôles et les restrictions liées aux agences côté serveur ;
- permet à l'unique utilisateur `admin` de lister, créer, modifier et désactiver les utilisateurs communs ;
- permet à `admin` de modifier le mot de passe ou l'agence d'un utilisateur commun ;
- interdit à `admin` toute opération sur les stocks ;
- permet aux utilisateurs communs de consulter, lister, ajouter et retirer du stock uniquement dans leur agence ;
- accède aux données locales avec SQLAlchemy ;
- récupère les informations produit auprès de l'API externe au moyen de requêtes REST en lecture seule.

Il n'existe qu'un seul administrateur, nommé `admin`. Chaque utilisateur commun est rattaché à une seule agence. Le serveur détermine cette agence à partir du compte authentifié et ne fait pas confiance à une agence transmise par le navigateur.

### Base de données PostgreSQL

La base locale contient uniquement :

- `users` : nom d'utilisateur, empreinte du mot de passe, rôle, agence et état de suppression logique ;
- `branches` : identifiant et nom de l'agence ;
- `stock` : agence, identifiant numérique externe du produit et quantité disponible.

Elle ne contient ni nom, ni SKU, ni description, ni prix, ni image, ni métadonnée de produit.

### API Produit externe

L'API fournie constitue la source de référence des informations produit. Elle :

- fournit la liste des produits ;
- renvoie les détails d'un produit à partir de son identifiant numérique ou de son SKU ;
- est accessible uniquement en lecture ;
- ne gère pas les quantités de stock propres à HBntory.

Le Backoffice vérifie l'existence d'un produit auprès de cette API avant de créer un stock. Seul l'identifiant numérique canonique renvoyé par l'API est conservé.

### Serveur MCP Produit

Le serveur MCP Produit est un service indépendant servant d'intermédiaire avec l'API Produit. Il expose au minimum :

- `list_products` : renvoie les produits disponibles avec leurs identifiants et un résumé utile ;
- `get_product_details` : renvoie un produit à partir de son identifiant numérique ou de son SKU.

Il ne contient aucune IA. Le service web public appelle ces outils au moyen de MCP sur HTTP Streamable. Le serveur MCP ne modifie jamais les produits et n'enregistre pas leurs métadonnées.

### Service client public et interface web

Le composant `client_web` fournit une page de recherche anonyme et un petit backend REST. Il :

- permet aux visiteurs de rechercher des produits ;
- affiche les détails du produit sélectionné ;
- indique les agences qui possèdent ce produit et les quantités disponibles ;
- liste les produits disponibles dans une agence sélectionnée ;
- obtient les données produit auprès du serveur MCP Produit ;
- effectue des consultations de stock contrôlées et en lecture seule avec SQLAlchemy ;
- traite chaque requête indépendamment et ne conserve aucun historique.

Le service public ne peut ni créer des utilisateurs ni modifier les stocks.

## 3. Circulation des données

### Authentification du Backoffice

1. L'utilisateur transmet ses identifiants au Backoffice.
2. Le Backoffice récupère le compte actif et vérifie le mot de passe à partir de son empreinte Argon2id.
3. Une authentification réussie crée un cookie de session signé et inaccessible à JavaScript.
4. Chaque requête protégée vérifie de nouveau le rôle, l'état du compte et l'agence.

### Consultation des stocks dans le Backoffice

1. L'utilisateur commun demande à consulter son stock.
2. Le serveur déduit son agence du compte authentifié.
3. SQLAlchemy récupère les identifiants produit et les quantités enregistrées localement.
4. Le Backoffice demande les informations correspondantes à l'API Produit.
5. La réponse combinée est affichée sans enregistrer localement les informations produit.

### Modification des stocks

1. Le serveur vérifie qu'il s'agit d'un utilisateur commun actif.
2. Il déduit l'agence du compte authentifié.
3. Il n'accepte qu'une quantité entière strictement positive.
4. Il valide le produit auprès de l'API externe.
5. Il modifie le stock dans une transaction.
6. Un retrait est refusé si la quantité disponible est insuffisante.
7. Une contrainte de base de données garantit que la quantité ne devient jamais négative.

### Recherche publique de produits et de stocks

1. Un visiteur anonyme lance une recherche de produit ou d'agence par REST.
2. Le service client public appelle le serveur MCP Produit pour obtenir les informations produit.
3. Le serveur MCP appelle l'API Produit externe en lecture seule.
4. Lorsqu'une information de stock est nécessaire, le service client public effectue une requête contrôlée et en lecture seule dans la base.
5. Le service combine les résultats et renvoie des données structurées à la page.
6. Aucune réponse générée par une IA et aucun historique n'interviennent.

## 4. Règles de sécurité et d'intégrité

- Aucun mot de passe n'est enregistré en clair.
- Argon2id est utilisé, car cet algorithme est conçu pour le stockage des mots de passe et résiste aux attaques par force brute grâce à des coûts mémoire et de calcul configurables.
- Le Backoffice utilise un cookie de session signé, inaccessible à JavaScript et limité au même site. Les requêtes qui modifient des données sont protégées contre les attaques CSRF.
- L'authentification et les autorisations sont contrôlées côté serveur.
- `admin` n'est rattaché à aucune agence et ne peut pas modifier les stocks.
- Chaque utilisateur commun dépend d'une seule agence et ne peut pas en sélectionner une autre.
- Un utilisateur désactivé ne peut plus s'authentifier ni conserver son accès.
- Toute modification de stock exige un entier positif et ne peut produire une quantité négative.
- Les points d'accès publics et leurs accès à la base sont strictement en lecture seule.
- Les secrets sont fournis par des variables d'environnement et ne sont pas versionnés.

## 5. Livrables associés

- [Schéma initial des services](initial-service-diagram.md)
- [Stratégie de communication](communication-strategies.md)
- [Définition du MVP](mvp-definition.md)
