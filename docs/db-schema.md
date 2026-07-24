# HBntory — Schéma de base de données

## 1. Portée

La base PostgreSQL du Backoffice contient exactement trois tables : `users`, `branches` et `stocks`. Aucune autre table n'est ajoutée : pas de table produit locale, pas de table de configuration ou d'audit — ces besoins ne sont pas requis par le projet à ce stade.

Conformément à l'architecture (`architecture_FR.md`), les informations produit (nom, description, prix, image) ne sont **jamais** stockées en local. Seul l'identifiant numérique externe du produit apparaît, dans `stocks`.

## 2. Table `users`

| Colonne | Type | Contrainte |
| --- | --- | --- |
| `user_id` | entier | clé primaire |
| `username` | texte | `UNIQUE`, `NOT NULL` |
| `password_hash` | texte | `NOT NULL` |
| `role` | énumération (`Admin` \| `Common`) | `NOT NULL` |
| `branch_id` | entier | clé étrangère → `branches.branch_id`, nullable |
| `status` | énumération (`Active` \| `Inactive`) | `NOT NULL`, aucune valeur par défaut au niveau base — doit être fournie explicitement à la création |
| `created_at` | horodatage (avec fuseau) | `NOT NULL`, valeur posée par PostgreSQL (`server_default=now()`) |
| `updated_at` | horodatage (avec fuseau) | `NOT NULL`, posée et rafraîchie par PostgreSQL (`server_default`/`onupdate=now()`) |

Contrainte de table :

```sql
CHECK (
  (role = 'Admin' AND branch_id IS NULL)
  OR
  (role = 'Common' AND branch_id IS NOT NULL)
)
```

**Justifications :**
- `password_hash` ne contient jamais de mot de passe en clair ni chiffré de façon réversible : c'est un hash Argon2id (irréversible, résistant au brute-force). Chiffrer un mot de passe impliquerait une clé de déchiffrement quelque part, ce qui recrée un risque en cas de fuite.
- `role` et `branch_id` sont liés par une contrainte `CHECK` combinée plutôt qu'une simple colonne nullable : une colonne nullable seule autoriserait un `Common` sans branche ou un `Admin` avec une branche, deux états incohérents. La contrainte les empêche au niveau base, indépendamment de tout bug applicatif.
- `status` sert de soft-delete : un utilisateur désactivé passe à `Inactive` plutôt que d'être supprimé physiquement. Son historique (créations de stock, etc.) reste traçable. **Point d'attention :** la colonne n'a actuellement aucune valeur par défaut au niveau base — le code applicatif (script de seed, endpoint de création) doit fixer `Active` explicitement à la création d'un utilisateur.
- `created_at`/`updated_at` : traçabilité, calculées côté PostgreSQL (`server_default`) plutôt que côté Python, pour rester correctes même en cas d'insertion hors du chemin applicatif habituel (script SQL direct, migration de données).

### Règle : admin non assigné à la gestion de stock

Cette règle est **supportée structurellement** par le schéma, mais pas imposée par une contrainte SQL à elle seule :
- la table `stocks` ne référence aucun `user_id` — le stock est rattaché à une `branch`, jamais à un utilisateur ;
- la contrainte combinée `CHECK` ci-dessus force `branch_id IS NULL` pour tout `role = 'Admin'` ; un compte admin n'est donc structurellement rattaché à aucune agence, et les opérations de stock (toujours scannées par branche) ne peuvent pas s'appliquer à lui par construction.

L'interdiction *active* (refuser explicitement une requête de modification de stock si l'utilisateur authentifié a `role = 'Admin'`) reste une responsabilité applicative, traitée dans Task 2 (Authentication and Authorization / RBAC), pas dans le schéma seul.

## 3. Table `branches`

| Colonne | Type | Contrainte |
| --- | --- | --- |
| `branch_id` | entier | clé primaire |
| `localisation` | texte | `NOT NULL` |

Aucun autre champ n'a été ajouté (pas de statut d'ouverture, pas de description, pas de liste de produits) : rien dans les règles du projet ne justifie ces champs à ce stade, et une liste de produits sur `branches` dupliquerait la relation déjà portée par `stocks`.

## 4. Table `stocks`

| Colonne | Type | Contrainte |
| --- | --- | --- |
| `stock_id` | entier | clé primaire |
| `product_id` | entier | `NOT NULL` — identifiant numérique externe, retourné par l'API Produit |
| `branch_id` | entier | clé étrangère → `branches.branch_id`, `NOT NULL` |
| `quantity` | entier | `NOT NULL`, aucune valeur par défaut au niveau base — doit être fournie explicitement à l'écriture |

Contraintes de table :

```sql
CHECK (quantity >= 0)
UNIQUE (branch_id, product_id)
```

**Justifications :**
- `CHECK (quantity >= 0)` empêche toute écriture (ajout, retrait, script d'init) de laisser la ligne dans un état invalide, quelle que soit la logique applicative qui a produit la valeur. C'est la garantie de dernier recours, en plus de la validation applicative qui doit refuser un retrait insuffisant avant même de tenter l'écriture.
- `UNIQUE (branch_id, product_id)` garantit une seule ligne de stock par couple agence/produit. Sans cette contrainte, rien n'empêcherait deux lignes séparées pour le même produit dans la même agence, rendant les opérations d'ajout/retrait ambiguës (laquelle des deux lignes modifier ?).
- Aucune colonne `description` ou `fournisseur` : ce sont des données produit, qui appartiennent exclusivement à l'API Produit externe, jamais à la base locale.

## 5. Relations

```
branches (1) ──< (N) users        via users.branch_id
branches (1) ──< (N) stocks       via stocks.branch_id
```

Un `Common` appartient à exactement une agence (`users.branch_id NOT NULL` imposé par la contrainte combinée). Un `Admin` n'appartient à aucune agence (`branch_id IS NULL` imposé par la même contrainte). Une agence peut avoir plusieurs lignes de stock, une par produit distinct (garanti par `UNIQUE`).

Les relations Python (`relationship()` SQLAlchemy, pour naviguer `branch.users`/`user.branch`/`branch.stocks` sans requête manuelle) ne sont pas encore implémentées dans `backoffice/app/models.py` — prévues à la suite de l'étape "Implement SQLAlchemy Models".

## 6. Ce qui n'est volontairement pas dans ce schéma

- Table produit locale (nom, prix, description, image) : source de vérité = API Produit externe uniquement.
- Suppression physique des utilisateurs : remplacée par `status = Inactive`.
- Historique des mouvements de stock : non requis par le MVP (`mvp-definition.md` le liste en "Optional Features Only If Time Remains").
