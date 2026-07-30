# Faire tourner HBntory en local — guide pas à pas

Ce guide couvre le Backoffice (login, gestion de stock, gestion des
utilisateurs), le catalogue produits public (`client_web`, servi par la
même application) et l'API Produit externe dont ils dépendent tous les
deux. Seule l'IA (AI Query Service, Task 5/6) n'est pas couverte :
exclue d'un commun accord avec le responsable du projet (voir
`docs/plan-backend-securite.md`) — `client_web` a été reconstruit en
catalogue fonctionnel sans dépendance IA, voir `client_web/README.md`.

## Prérequis

- Python 3.11+ installé
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé (pour l'API Produit)
- Un terminal (PowerShell sur Windows)

## Étape 1 — Cloner et lancer l'API Produit externe

Le Backoffice a besoin de cette API pour afficher les noms/prix des produits.

```powershell
git clone https://github.com/hbtn-edu/hbntory-products-api.git ../hbntory-products-api
cd ../hbntory-products-api
docker compose up -d --build
```

Vérifie qu'elle répond :

```powershell
curl http://localhost:5001/health
```

Tu dois voir `{"status": "ok", "products": 40, ...}`.

## Étape 2 — Préparer l'environnement Python du Backoffice

Depuis la racine du repo HBntory :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backoffice\requirements.txt
```

## Étape 3 — Créer la base de données et l'administrateur

On utilise SQLite ici — un simple fichier, aucune dépendance en plus.
C'est suffisant pour tester le Backoffice en local.

```powershell
Set-Location backoffice
$env:DATABASE_URL = "sqlite:///dev.db"
$env:ADMIN_PASSWORD = "ChoisisTonMotDePasse123"
$env:SESSION_SECRET_KEY = "dev-secret"
python -m app.seed
```

`seed_database()` already calls `Base.metadata.create_all()` itself, so this
one command both creates the tables (on a fresh `dev.db`) and inserts the
initial data. It creates :
- 1 compte admin (`admin` / le mot de passe choisi ci-dessus)
- 3 branches (Annecy, Thonon-les-bains, Genève)
- Du stock d'exemple

Relance cette commande à tout moment pour **compléter** ce qui manquerait
(idempotent — ne duplique rien, mais ne remplace pas non plus un mot de
passe ou un stock déjà existant). Pour repartir totalement à zéro, supprime
`dev.db` avant de relancer.

> **Mise à niveau ponctuelle si `dev.db` existait déjà avant l'ajout de
> `token_version`** (colonne utilisée pour la révocation de session au
> logout) : `Base.metadata.create_all()` crée les tables **manquantes**,
> il ne modifie pas une table déjà existante. Un `dev.db` créé avec un
> schéma plus ancien n'aura pas cette colonne, et le serveur plantera au
> premier login. Supprime `dev.db` et relance `python -m app.seed` — les
> bases existantes ne sont pas modifiées automatiquement.

## Étape 4 — Lancer le serveur

Toujours dans `backoffice/`, avec les mêmes variables d'environnement actives :

```powershell
python -m uvicorn app.main:app --port 5000
```

Laisse ce terminal ouvert (`Ctrl+C` pour arrêter).

## Étape 5 — Ouvrir la page dans le navigateur

```text
http://localhost:5000/        catalogue produits public (accueil, aucun compte requis)
http://localhost:5000/login   connexion au Backoffice
```

Sur `/login`, connecte-toi avec `admin` / le mot de passe choisi à
l'étape 3 (ou un compte common créé ensuite par l'admin).

## Étape 6 — Lancer le Product MCP Server (optionnel)

Ce service est indépendant du Backoffice — voir
[`product_mcp_server/README.md`](../product_mcp_server/README.md) pour le
détail complet (tools, gestion d'erreurs, preuves de test). Commandes
essentielles, dans un nouveau terminal, depuis la racine du repo :

```powershell
Set-Location product_mcp_server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

L'API Produit externe (étape 1) doit déjà tourner. Aucune variable
d'environnement à définir pour ce setup local : `PRODUCT_API_BASE_URL` vaut
déjà `http://localhost:5001` par défaut. Le serveur MCP écoute ensuite sur :

```text
http://127.0.0.1:8000/mcp
```

---

# Guide d'utilisation

## Se connecter

Va sur `/login`. Une fois connecté, tu es redirigé automatiquement vers le
bon tableau de bord selon le rôle du compte utilisé — admin ou common.
(`/` reste la page catalogue publique, accessible sans connexion.)

## Catalogue produits public (`/`, sans connexion)

- **Rechercher** un produit par mot-clé (nom, référence).
- **Filtrer** par catégorie (menu déroulant, rempli depuis l'API Produit).
- Les résultats ne s'affichent qu'après une recherche explicite (le
  catalogue ne liste pas tout par défaut à l'ouverture de la page).
- N'affiche ni le stock ni la disponibilité par agence — uniquement les
  informations produit (nom, catégorie, marque, prix), obtenues en direct
  depuis l'API Produit externe.

## En tant qu'admin — gestion des utilisateurs

- **Lister** les utilisateurs, filtrer par branche ou statut.
- **Créer** un utilisateur *common* : nom d'utilisateur, mot de passe,
  branche assignée (obligatoire pour un common user).
- **Modifier** un utilisateur : changer son nom ou sa branche.
- **Changer le mot de passe** d'un utilisateur.
- **Supprimer** (soft-delete) un utilisateur : il ne pourra plus se
  connecter, mais son historique de stock reste intact. Le compte admin
  ne peut pas être modifié/supprimé depuis cette interface.

L'admin ne peut pas gérer le stock — ce n'est pas caché, c'est refusé côté
serveur (403) si on essaie directement via l'API.

## En tant que common user — gestion du stock

- Le nom de la branche assignée s'affiche en haut de la page — impossible
  d'opérer sur une autre branche, ni depuis l'interface ni en contournant
  l'API (la branche vient toujours de la session, jamais d'un champ du
  formulaire).
- **Ajouter du stock** : choisir un produit (liste vient de l'API Produit
  externe) et une quantité.
- **Retirer du stock** : idem, refusé si la quantité dépasse le stock
  disponible.
- **Consulter** la liste des produits actuellement en stock dans sa
  branche, avec recherche.

Un common user ne peut pas gérer les utilisateurs — refusé côté serveur
(403) si on essaie directement via l'API.

## Se déconnecter

Bouton de déconnexion en haut de chaque page — invalide la session côté
serveur immédiatement.

## Lancer les tests automatisés (optionnel)

```powershell
cd backoffice
python -m pytest tests/ -v
```

58 tests — login/session (dont la révocation immédiate au logout et le
cookie `Secure` configurable), mots de passe, règles d'autorisation
admin/common, opérations de stock et gestion des utilisateurs (succès et
cas limites : retrait supérieur au stock, produit inconnu, conflits de
nom d'utilisateur, changement de mot de passe, soft-delete), le seed
(création + reruns idempotents), les routes publiques du catalogue, et la
pagination/le filtrage côté client Product API — aucune dépendance
externe (base SQLite dans un fichier temporaire, recréée à chaque test).

## Problèmes fréquents

| Symptôme | Cause probable |
| --- | --- |
| "Impossible de contacter le serveur" dans le navigateur | Le serveur n'est pas lancé, ou tourne sur un port différent de celui attendu par l'URL ouverte |
| Les noms de produits n'apparaissent pas dans la page stock | L'API Produit externe (`docker compose up -d`, étape 1) n'est pas lancée |
| `ADMIN_PASSWORD must be set before running seed.py` | La variable d'environnement `$env:ADMIN_PASSWORD` n'est pas définie dans le terminal courant |
| La connexion boucle silencieusement en accédant via une IP du réseau local (`http://192.168.x.x:5000`) ou dans Safari | Le cookie de session est marqué `Secure` par défaut (nécessite HTTPS ou `localhost`). Lance le serveur avec `$env:COOKIE_SECURE = "false"` pour tester dans ces cas-là |
