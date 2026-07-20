# HBntory - Inventory Management Platform
## System Architecture Document

**Projet :** HBntory Inventory Management Platform
**Version :** 1.0
**Équipe :** Rémy, Nicolas, Aleksandre
**Date :** 20/07/2026

---

## 1. Vue d'ensemble du projet

Le projet HBntory est un projet d'équipe permettant d'appliquer tout ce qu'on a vu dans le trimestre. Ce projet simule une plateforme de gestion de marchandise de compagnie.

### Objectifs principaux

- **Interface web client** : permet au client de chercher un objet via un chatbot/IA et d'obtenir un retour de la plateforme indiquant si l'objet est disponible et sa quantité.
- **Backoffice** : interface utilisateur privée permettant aux employés d'accéder aux stocks et informations associées. Un compte admin peut créer, modifier et supprimer des comptes d'utilisateurs employés.

---

## 2. Architecture générale

L'application est découpée en plusieurs services afin de respecter une architecture modulaire.

```
                         ┌─────────────────────┐
                         │   External Product   │
                         │         API          │
                         │       (Docker)       │
                         └──────────┬───────────┘
                                    │ HTTP
                                    ▼
                         ┌──────────────────────┐
                         │   Product MCP        │
                         │      Server          │
                         └──────────┬───────────┘
                                    │ MCP Protocol
                                    ▼
                         ┌──────────────────────┐
                         │   AI Query Service    │
                         │     AI Agent(s)       │
                         └──────────┬───────────┘
                                    │ SQL Queries
                                    ▼
              ┌────────────────────────────────────────┐
              │            PostgreSQL Database          │
              │                                          │
              │      Users | Branches | Stock            │
              └────────────────────▲─────────────────────┘
                                    │ SQLAlchemy
                                    │
                         ┌──────────┴───────────┐
                         │     Backoffice        │
                         │      Service          │
                         └──────────┬───────────┘
                                    │ REST
                                    ▼
                         ┌──────────────────────┐
                         │   Internal Users      │
                         │   Web Interface       │
                         └──────────────────────┘


                         ┌──────────────────────┐
                         │    Client Web         │
                         │     Interface         │
                         └──────────┬───────────┘
                                    │ REST
                                    ▼
                         ┌──────────────────────┐
                         │   AI Query Service    │
                         └──────────────────────┘
```

Chaque composant possède une responsabilité précise, détaillée section 3.

---

## 3. Description des composants

### 3.1 Backoffice

Application utilisée par les employés.

**Responsabilités :**
- authentification
- gestion des utilisateurs
- gestion des agences (branches)
- gestion des stocks
- contrôle des droits d'accès

**Technologies :** FastAPI, SQLAlchemy, PostgreSQL, JWT, bcrypt

### 3.2 Base de données

Stocke uniquement les informations propres à notre application.

**Utilisateurs**
- identifiant
- nom d'utilisateur
- mot de passe chiffré
- rôle
- agence associée
- statut actif/inactif

**Agences**
- identifiant
- nom
- localisation

**Stock**
- agence
- identifiant du produit
- quantité disponible

**Données volontairement absentes**

Conformément au sujet, nous ne stockons jamais :
- le nom du produit
- sa description
- son prix
- son image
- ses caractéristiques

Nous conservons uniquement l'identifiant du produit (`product_id`), qui permet d'interroger l'API externe.

### 3.3 Product API

Fournie dans un conteneur Docker. Unique source d'information concernant les produits.

**Permet de :**
- récupérer la liste des produits
- récupérer le détail d'un produit

Notre application ne modifie jamais ces données.

### 3.4 Product MCP Server

Intermédiaire entre l'intelligence artificielle et la Product API. Expose plusieurs outils que l'agent IA peut utiliser.

**Outils disponibles**

| Outil | Description |
|---|---|
| `list_products()` | Retourne la liste des produits disponibles |
| `get_product_details(product_id)` | Retourne toutes les informations concernant un produit |

Ainsi, l'IA ne dialogue jamais directement avec l'API externe.

### 3.5 AI Query Service

Service indépendant du Backoffice. Son rôle est de comprendre les questions des utilisateurs.

**Exemples :**
- "Dans quelle agence puis-je trouver ce produit ?"
- "Donne-moi les informations sur le produit 125."

**Pour répondre, l'agent IA :**
1. utilise le serveur MCP pour obtenir les informations sur les produits
2. consulte notre base de données pour connaître les stocks disponibles
3. construit ensuite une réponse

L'IA ne doit jamais inventer une information qu'elle ne possède pas.

### 3.6 Interface Web Client

Publique, aucune authentification nécessaire.

**Contient :**
- une zone de saisie
- un bouton d'envoi
- une zone affichant la réponse de l'IA

---

## 4. Communication entre les services

### 4.1 Backoffice

Architecture choisie : **REST + HTML/CSS/JavaScript**

**Pourquoi ?** Simple, bien adaptée aux opérations CRUD, facile à maintenir.

**Limite :** le développement du frontend demande un peu plus de JavaScript qu'un rendu côté serveur.

### 4.2 Client Web → AI Service

Architecture choisie : **API REST**.

Chaque question étant indépendante, il n'est pas nécessaire de maintenir une connexion permanente.

**Exemple :**
```
POST /ask
```
avec une question. Le serveur répond immédiatement avec une réponse.

**Pourquoi ne pas utiliser WebSocket ?**

Les WebSockets sont particulièrement utiles lorsque :
- une conversation est continue
- les réponses arrivent progressivement (streaming)
- plusieurs utilisateurs communiquent en temps réel

Notre projet ne nécessite aucune de ces fonctionnalités. REST est donc plus simple et plus adapté.

### 4.3 AI → MCP

L'agent IA communique avec le serveur MCP grâce au protocole MCP.

Cela permet de séparer complètement l'intelligence artificielle de l'accès aux produits, rendant le système plus modulaire.

---

## 5. Authentification et sécurité

Tous les utilisateurs du Backoffice doivent être authentifiés.

Les mots de passe sont stockés sous forme chiffrée grâce à **bcrypt**, choisi car :
- spécialement conçu pour le stockage des mots de passe
- ajoute automatiquement un "salt"
- ralentit volontairement les calculs afin de limiter les attaques par force brute

Une fois connecté, l'utilisateur reçoit un **JWT** utilisé pour les requêtes suivantes.

### 5.1 Gestion des rôles

**Administrateur** peut :
- créer un utilisateur
- modifier un utilisateur
- supprimer (soft delete) un utilisateur
- changer un mot de passe
- affecter une agence

Il ne peut en revanche pas gérer les stocks.

**Utilisateur standard**

Chaque utilisateur est rattaché à une seule agence. Il peut uniquement :
- consulter son stock
- ajouter du stock
- retirer du stock

Il ne peut jamais accéder aux stocks d'une autre agence.

Toutes ces vérifications sont effectuées côté serveur, afin d'empêcher toute tentative de contournement.

---

## 6. Circulation des données

### Exemple 1

**Question :** "Donne-moi les informations du produit 152."

1. Le client envoie sa question.
2. L'AI Query Service reçoit la demande.
3. L'agent IA appelle le serveur MCP.
4. Le serveur MCP interroge la Product API.
5. Les informations sont renvoyées à l'IA.
6. L'IA génère une réponse.
7. La réponse est affichée au client.

### Exemple 2

**Question :** "Dans quelle agence puis-je trouver ce produit ?"

1. Le client envoie la question.
2. L'agent récupère les informations produit via le MCP.
3. Il consulte ensuite la table des stocks dans PostgreSQL.
4. Il identifie les agences possédant le produit.
5. Il construit la réponse finale.

---

## 7. MVP (Minimum Viable Product)

Notre priorité est de livrer un projet entièrement fonctionnel avant d'ajouter des fonctionnalités secondaires.

| Étape | Contenu |
|---|---|
| 1 | Base de données, authentification, gestion des utilisateurs, gestion des agences |
| 2 | Gestion des stocks |
| 3 | Connexion à la Product API |
| 4 | Serveur MCP |
| 5 | Service IA |
| 6 | Interface web publique |

---

## 8. Fonctionnalités optionnelles

Si le temps le permet, nous ajouterons :
- une interface plus moderne
- un historique des mouvements de stock
- des recommandations de produits
- des statistiques de stock
- une réponse IA en streaming

---

## 9. Conclusion

Nous avons choisi une architecture composée de plusieurs services indépendants afin de faciliter la maintenance, les tests et l'évolution de l'application.

Les principaux choix techniques sont motivés par la simplicité, la séparation des responsabilités et le respect des exigences du projet.

- REST est utilisé pour les communications HTTP, car il est adapté à des requêtes indépendantes.
- Le serveur MCP sert d'intermédiaire entre l'IA et la Product API, ce qui rend l'accès aux données produit sécurisé et modulaire.
- PostgreSQL stocke uniquement les données locales (utilisateurs, agences et stocks), tandis que toutes les informations produit proviennent exclusivement de la Product API.
- Le Backoffice et le service IA sont volontairement séparés, afin de respecter une architecture claire et évolutive.
