# Product MCP Server

Ce document existe en français puis en anglais ci-dessous.
This document exists in French, then in English below.

---

## Français

Pont MCP indépendant et en lecture seule vers l'API Produit externe. Le
serveur ne conserve aucun état ni cache : chaque requête reçue est
transmise à l'API Produit, et la réponse est renvoyée reformatée pour le
client MCP appelant. Il ne touche jamais la base de données et ne connaît
ni le stock, ni les agences, ni les utilisateurs.

### Le lancer

```bash
# Terminal 1 — API Produit externe (cloner en tant que dossier voisin de ce dépôt)
git clone https://github.com/hbtn-edu/hbntory-products-api.git
cd hbntory-products-api
docker compose up --build
# sert l'API sur http://localhost:5001

# Terminal 2 — ce serveur
cd product_mcp_server
python -m venv .venv && source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
python server.py
# sert MCP sur http://127.0.0.1:8000/mcp
```

`PRODUCT_API_BASE_URL` contrôle où le serveur cherche l'API Produit. Elle
vaut par défaut `http://localhost:5001` en local ; dans Docker Compose,
elle est plutôt fixée à `http://external-products-api:5000`.

### Outils

| Outil | Entrée | Sortie en cas de succès |
|---|---|---|
| `list_products` | aucune | `{count, products: [...]}` — toutes les pages parcourues, huit champs résumés par produit (`id`, `sku`, `name`, `category`, `brand`, `unit_price`, `currency`, `discontinued`). Les produits discontinués sont exclus par le listing par défaut de l'API. |
| `get_product_details` | `identifier` — identifiant numérique ou SKU, sous forme de chaîne | L'enregistrement produit complet, y compris l'objet `supplier` imbriqué |

La liste est volontairement allégée : parcourir le catalogue ne doit pas
saturer la fenêtre de contexte de l'agent, et une recherche de détail est
une question délibérée qui mérite l'enregistrement complet.

### Gestion des erreurs

Aucun des deux outils ne lève jamais d'exception. Une exception levée
arrive à l'agent comme un échec de protocole générique qu'il ne peut pas
interpréter ; un dictionnaire renvoyé avec une clé `error` est une sortie
qu'il peut lire, distinguer, et répéter honnêtement à un client.

| Valeur `error` | Déclencheur | Champ supplémentaire |
|---|---|---|
| `invalid_identifier` | Identifiant vide ou uniquement des espaces, rejeté avant tout appel réseau | — |
| `product_not_found` | L'API Produit a répondu 404 : aucun ID ou SKU de ce type | — |
| `product_api_timeout` | Aucune réponse en 10 secondes | — |
| `product_api_unreachable` | Connexion refusée — conteneur arrêté, mauvais hôte ou port | — |
| `product_api_error` | Tout autre statut non-2xx, ex. le 503 forcé de l'API | `status_code` |

Deux détails d'ordre comptent dans le code :
- `TimeoutException` est attrapée avant `RequestError`, puisqu'elle en est
  une sous-classe — vérifier le cas général en premier étiquetterait à
  tort chaque timeout comme "unreachable".
- Pour `get_product_details`, la vérification du 404 se fait *avant*
  `raise_for_status()`. Un 404 ici est une réponse significative
  ("pas un tel produit"), pas un dysfonctionnement de l'API, et les deux
  doivent rester distinguables.

### Preuve de test manuel

Testé contre le vrai `hbntory-products-api`
(github.com/hbtn-edu/hbntory-products-api, `docker compose up --build`,
port 5001) en appelant directement les fonctions outils de `server.py`
dans un shell Python — pas l'Inspecteur MCP, mais le même chemin de code
que l'Inspecteur ou un agent emprunterait, puisque `@mcp.tool()` ne fait
qu'enregistrer la fonction sans changer son exécution.

| # | Test | Résultat |
|---|---|---|
| 1 | `list_products` renvoie le catalogue complet, allégé | PASS — `count: 39` (un produit discontinué exclu ; `/health` rapporte 40 au total, cohérent). Premier élément : `{'id': 4, 'sku': 'HB-MON-2102', 'name': '24 inch Compact Monitor', 'category': 'Displays', 'brand': 'LabForge', 'unit_price': 169.99, 'currency': 'USD', 'discontinued': False}` — exactement les huit champs résumés, sans `description`/`tags`/`supplier`. |
| 2 | `get_product_details` par ID numérique (`4`) | PASS — enregistrement complet incluant `description`, `tags`, `weight_kg`, `updated_at`, et l'objet `supplier` imbriqué (`SUP-LAB-002`, LabForge Supplies) que la liste ne porte pas. |
| 3 | `get_product_details` par SKU (`HB-MON-2102`) | PASS — enregistrement identique au test 2, confirmant que les deux styles d'identifiant passent par le même chemin de code. |
| 4 | Identifiant inconnu (`does-not-exist`) | PASS — `{"error": "product_not_found", "message": "No product found for identifier 'does-not-exist'."}` ; un résultat d'outil normal et réussi, pas une erreur de protocole. |
| 5 | Identifiant vide (`""`) | PASS — `{"error": "invalid_identifier", ...}`, rejeté avant tout appel réseau (confirmé : aucune requête journalisée). |
| 6 | API Produit injoignable | PASS — conteneur arrêté (`docker compose stop`) en plein test ; `list_products()` et `get_product_details()` ont tous deux renvoyé `{"error": "product_api_unreachable", "message": "Could not reach the Product API."}`. |
| 7 | API Produit renvoie 503 | PASS (via un double de test local, pas l'API réelle — voir note ci-dessous) — `{"error": "product_api_error", "status_code": 503}`. |

Le test 7 utilise un double de test plutôt que le `force_error=true` de
l'API réelle parce que l'outil ne transmet volontairement jamais de
paramètres de requête arbitraires à l'API Produit (voir "avoid exposing
unnecessary Product API behavior" dans l'énoncé) — il n'y a aucun moyen de
demander un 503 à l'API réelle via la surface de paramètres réelle de
l'outil, ce qui est en soi une confirmation que l'interface allégée
fonctionne comme prévu, pas un trou de couverture. Confirmé
indépendamment que l'API réelle répond bien 503 à
`curl "http://localhost:5001/api/v1/products?force_error=true"`.

### Décisions de conception

| Décision | Pourquoi |
|---|---|
| Alléger la liste, garder le détail complet | Parcourir a besoin d'un résultat compact ; une recherche de détail est une question délibérée et mérite l'enregistrement complet. Réversible avec une modification d'une ligne dans `SUMMARY_FIELDS`. |
| Renvoyer des dictionnaires d'erreur, jamais lever d'exception | Une exception levée est une information que l'agent ne peut pas utiliser ; un dictionnaire `{"error": ..., "message": ...}` renvoyé, si. |
| Parcourir toutes les pages de l'API Produit | Ne renvoyer que la première page ferait croire à l'agent que des produits des pages suivantes n'existent pas — un échec silencieux par omission. |
| Lire l'adresse de l'API Produit depuis l'environnement | Coder en dur `localhost:5001` casse dans Docker Compose ; `os.environ.get` avec un repli local fonctionne dans les deux environnements et garde la configuration hors de Git. |

### Et ensuite

Les deux outils MCP sont complets et vérifiés indépendamment contre l'API
Produit externe. Aucun service IA consommateur n'a été construit,
conformément au périmètre final acté (Task 5, AI Query Service, est hors
périmètre de ce projet).

---

## English

Independent, read-only MCP bridge to the external Product API. The server
holds no state and no cache: every request it receives is forwarded to the
Product API and the answer is handed back reshaped for whichever MCP client
calls it. It never touches the database and knows nothing about stock,
branches, or users.

### Running it

```bash
# Terminal 1 — external Product API (clone it as a sibling of this repo)
git clone https://github.com/hbtn-edu/hbntory-products-api.git
cd hbntory-products-api
docker compose up --build
# serves the API at http://localhost:5001

# Terminal 2 — this server
cd product_mcp_server
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python server.py
# serves MCP at http://127.0.0.1:8000/mcp
```

`PRODUCT_API_BASE_URL` controls where the server looks for the Product API.
It defaults to `http://localhost:5001` for local runs; inside Docker Compose
it's set to `http://external-products-api:5000` instead.

### Tools

| Tool | Input | Output on success |
|---|---|---|
| `list_products` | none | `{count, products: [...]}` — every page walked, eight summary fields per product (`id`, `sku`, `name`, `category`, `brand`, `unit_price`, `currency`, `discontinued`). Discontinued items are excluded by the API's default listing. |
| `get_product_details` | `identifier` — numeric ID or SKU, as a string | The complete product record, including the nested `supplier` object |

The list is trimmed on purpose: browsing shouldn't flood the agent's context
window, and a detail lookup is a deliberate question that deserves the full
record.

### Error handling

Neither tool ever raises. A raised exception reaches the agent as a generic
protocol failure it can't interpret; a returned dict with an `error` key is
output it can read, distinguish, and repeat honestly to a customer.

| `error` value | Trigger | Extra field |
|---|---|---|
| `invalid_identifier` | Empty or whitespace-only identifier, rejected before any network call | — |
| `product_not_found` | Product API answered 404: no such ID or SKU | — |
| `product_api_timeout` | No response within 10 seconds | — |
| `product_api_unreachable` | Connection refused — container down, wrong host or port | — |
| `product_api_error` | Any other non-2xx status, e.g. the API's forced 503 | `status_code` |

Two ordering details matter in the code:
- `TimeoutException` is caught before `RequestError`, since it's a subclass of
  it — checking the general case first would mislabel every timeout as
  "unreachable."
- For `get_product_details`, the 404 check happens *before*
  `raise_for_status()`. A 404 there is a meaningful answer ("no such
  product"), not an API malfunction, and the two must stay distinguishable.

### Manual test evidence

Run against the real `hbntory-products-api` (github.com/hbtn-edu/hbntory-products-api,
`docker compose up --build`, port 5001) by calling `server.py`'s tool
functions directly in a Python shell — not the MCP Inspector, but the same
code path the Inspector or an agent would go through, since `@mcp.tool()`
only registers the function and doesn't change how it runs.

| # | Test | Result |
|---|---|---|
| 1 | `list_products` returns the full catalogue, trimmed | PASS — `count: 39` (one discontinued product excluded; `/health` reports 40 total, matching). First item: `{'id': 4, 'sku': 'HB-MON-2102', 'name': '24 inch Compact Monitor', 'category': 'Displays', 'brand': 'LabForge', 'unit_price': 169.99, 'currency': 'USD', 'discontinued': False}` — exactly the eight summary fields, no `description`/`tags`/`supplier`. |
| 2 | `get_product_details` by numeric ID (`4`) | PASS — full record including `description`, `tags`, `weight_kg`, `updated_at`, and the nested `supplier` object (`SUP-LAB-002`, LabForge Supplies) that the list output doesn't carry. |
| 3 | `get_product_details` by SKU (`HB-MON-2102`) | PASS — byte-for-byte the same record as test 2, confirming both identifier styles resolve through the same code path. |
| 4 | Unknown identifier (`does-not-exist`) | PASS — `{"error": "product_not_found", "message": "No product found for identifier 'does-not-exist'."}`; a normal, successful tool result, not a protocol-level error. |
| 5 | Empty identifier (`""`) | PASS — `{"error": "invalid_identifier", ...}`, rejected before any network call (confirmed no request was logged). |
| 6 | Product API unreachable | PASS — container stopped (`docker compose stop`) in the middle of the test session; both `list_products()` and `get_product_details()` returned `{"error": "product_api_unreachable", "message": "Could not reach the Product API."}`. |
| 7 | Product API returns 503 | PASS (via a local test double, not the real API — see note below) — `{"error": "product_api_error", "status_code": 503}`. |

Test 7 uses a test double rather than the real API's `force_error=true`
because the tool deliberately never forwards arbitrary query parameters to
the Product API (see "avoid exposing unnecessary Product API behavior" in
the task brief) — there's no way to ask the real API for a 503 through the
tool's actual parameter surface, which is itself a confirmation that the
trimmed interface works as intended, not a gap in coverage. Confirmed
independently that the real API does answer 503 to
`curl "http://localhost:5001/api/v1/products?force_error=true"`.

### Design decisions

| Decision | Why |
|---|---|
| Trim the list, keep the detail whole | Browsing needs a compact result; a detail lookup is a deliberate question and deserves the full record. Reversible with a one-line edit to `SUMMARY_FIELDS`. |
| Return error dicts, never raise | A raised exception is information the agent can't use; a returned `{"error": ..., "message": ...}` dict is. |
| Walk every page of the Product API | Returning only page one would make the agent deny products that exist on later pages — a silent failure by omission. |
| Read the Product API address from the environment | Hard-coding `localhost:5001` breaks inside Docker Compose; `os.environ.get` with a local fallback works in both environments and keeps configuration out of Git. |

### What's next

The two MCP tools are complete and independently verified against the
external Product API. No consuming AI service was built, in accordance with
the agreed final scope (Task 5, AI Query Service, is excluded from this
project).
