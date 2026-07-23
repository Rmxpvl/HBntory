# HBntory — Schéma de base de données

## 1. Portée

La base PostgreSQL du Backoffice contient exactement trois tables : `users`, `branches` et `stock`. Aucune autre table n'est ajoutée : pas de table produit locale, pas de table de configuration ou d'audit — ces besoins ne sont pas requis par le projet à ce stade.

Conformément à l'architecture (`architecture_FR.md`), les informations produit (nom, description, prix, image) ne sont **jamais** stockées en local. Seul l'identifiant numérique externe du produit apparaît, dans `stock`.

## 2. Table `users`

| Colonne | Type | Contrainte |
| --- | --- | --- |
| `user_id` | entier | clé primaire |
| `username` | texte | `UNIQUE`, `NOT NULL` |
| `password_hash` | texte | `NOT NULL` |
| `role` | texte (`admin` \| `common`) | `NOT NULL` |
| `branch_id` | entier | clé étrangère → `branches.branche_id`, nullable |
| `status` | texte (`actif` \| `inactif`) | `NOT NULL`, défaut `actif` |
| `created_at` | horodatage | `NOT NULL`, défaut à la création |
| `updated_at` | horodatage | `NOT NULL`, mis à jour à chaque modification |

Contrainte de table :

```sql
CHECK (
  (role = 'admin' AND branch_id IS NULL)
  OR
  (role = 'common' AND branch_id IS NOT NULL)
)
```

**Justifications :**
- `password_hash` ne contient jamais de mot de passe en clair ni chiffré de façon réversible : c'est un hash Argon2id (irréversible, résistant au brute-force). Chiffrer un mot de passe impliquerait une clé de déchiffrement quelque part, ce qui recrée un risque en cas de fuite.
- `role` et `branch_id` sont liés par une contrainte `CHECK` combinée plutôt qu'une simple colonne nullable : une colonne nullable seule autoriserait un `common` sans branche ou un `admin` avec une branche, deux états incohérents. La contrainte les empêche au niveau base, indépendamment de tout bug applicatif.
- `status` sert de soft-delete : un utilisateur désactivé passe à `inactif` plutôt que d'être supprimé physiquement. Son historique (créations de stock, etc.) reste traçable.
- `created_at`/`updated_at` : traçabilité, pas de contrainte métier associée mais recommandés par l'énoncé.

## 3. Table `branches`

| Colonne | Type | Contrainte |
| --- | --- | --- |
| `branche_id` | entier | clé primaire |
| `localisation` | texte | `NOT NULL` |

Aucun autre champ n'a été ajouté (pas de statut d'ouverture, pas de description, pas de liste de produits) : rien dans les règles du projet ne justifie ces champs à ce stade, et une liste de produits sur `branches` dupliquerait la relation déjà portée par `stock`.

## 4. Table `stock`

| Colonne | Type | Contrainte |
| --- | --- | --- |
| `stock_id` | entier | clé primaire |
| `product_id` | entier | `NOT NULL` — identifiant numérique externe, retourné par l'API Produit |
| `branche_id` | entier | clé étrangère → `branches.branche_id`, `NOT NULL` |
| `quantite` | entier | `NOT NULL`, défaut `0` |

Contraintes de table :

```sql
CHECK (quantite >= 0)
UNIQUE (branche_id, product_id)
```

**Justifications :**
- `CHECK (quantite >= 0)` empêche toute écriture (ajout, retrait, script d'init) de laisser la ligne dans un état invalide, quelle que soit la logique applicative qui a produit la valeur. C'est la garantie de dernier recours, en plus de la validation applicative qui doit refuser un retrait insuffisant avant même de tenter l'écriture.
- `UNIQUE (branche_id, product_id)` garantit une seule ligne de stock par couple agence/produit. Sans cette contrainte, rien n'empêcherait deux lignes séparées pour le même produit dans la même agence, rendant les opérations d'ajout/retrait ambiguës (laquelle des deux lignes modifier ?).
- Aucune colonne `description` ou `fournisseur` : ce sont des données produit, qui appartiennent exclusivement à l'API Produit externe, jamais à la base locale.

## 5. Relations

```
branches (1) ──< (N) users        via users.branch_id
branches (1) ──< (N) stock        via stock.branche_id
```

Un `common` appartient à exactement une agence (`users.branch_id NOT NULL` imposé par la contrainte combinée). Un `admin` n'appartient à aucune agence (`branch_id IS NULL` imposé par la même contrainte). Une agence peut avoir plusieurs lignes de stock, une par produit distinct (garanti par `UNIQUE`).

## 6. Ce qui n'est volontairement pas dans ce schéma

- Table produit locale (nom, prix, description, image) : source de vérité = API Produit externe uniquement.
- Suppression physique des utilisateurs : remplacée par `status = inactif`.
- Historique des mouvements de stock : non requis par le MVP (`mvp-definition.md` le liste en "Optional Features Only If Time Remains").
