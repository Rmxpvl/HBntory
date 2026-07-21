# HBntory — Architecture du Backoffice

## 1. Périmètre

Le périmètre de réalisation retenu par l'équipe est le Backoffice de gestion des stocks, sans intelligence artificielle. Il comprend :

- un Backoffice authentifié destiné aux utilisateurs internes ;
- une base de données relationnelle pour les utilisateurs, les agences et les stocks ;
- l'intégration de l'API Produit externe fournie en lecture seule.

Les agents IA, l'AI Query Service, MCP, l'interface publique de conversation, les WebSockets et l'historique des conversations sont exclus de ce périmètre.

## 2. Composants

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

## 3. Circulation des données

### Authentification

1. L'utilisateur transmet ses identifiants au Backoffice.
2. Le Backoffice récupère le compte actif et vérifie le mot de passe à partir de son empreinte Argon2id.
3. Une authentification réussie crée un cookie de session signé et inaccessible à JavaScript.
4. Chaque requête protégée vérifie de nouveau le rôle, l'état du compte et l'agence.

### Consultation des stocks

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

### Gestion des utilisateurs

1. Le serveur vérifie le rôle `admin`.
2. Il valide les données de l'utilisateur commun et l'agence choisie.
3. Tout nouveau mot de passe est traité avec Argon2id avant son enregistrement.
4. La suppression désactive le compte et renseigne `deleted_at` sans supprimer la ligne.

## 4. Règles de sécurité

- Aucun mot de passe n'est enregistré en clair.
- Argon2id est utilisé, car cet algorithme est conçu pour le stockage des mots de passe et résiste aux attaques par force brute grâce à un coût mémoire et un coût de calcul configurables.
- Le navigateur s'authentifie au moyen d'un cookie de session signé, inaccessible à JavaScript et limité au même site. Les requêtes qui modifient des données sont protégées contre les attaques CSRF.
- L'authentification et les autorisations sont contrôlées côté serveur.
- `admin` n'est rattaché à aucune agence et ne peut pas modifier les stocks.
- Chaque utilisateur commun dépend d'une seule agence et ne peut pas en sélectionner une autre.
- Un utilisateur désactivé ne peut plus s'authentifier ni conserver son accès.
- Les secrets sont fournis par des variables d'environnement et ne sont pas versionnés.

## 5. Livrables associés

- [Schéma initial des services](initial-service-diagram.md)
- [Stratégie de communication](communication-strategies.md)
- [Définition du MVP](mvp-definition.md)
- [Schéma de base de données](database-schema.md)
- [Règles de validation](validation-rules.md)
