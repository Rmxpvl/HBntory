# HBntory - Inventory Management Platform
## System Architecture Document

**Project:** HBntory Inventory Management Platform
**Version:** 1.0
**Team:** Rémy, Nicolas, Aleksandre
**Date:** 20/07/2026

---

## 1. Project Overview

HBntory is a team project applying everything covered this term. It simulates a company merchandise management platform.

### Main objectives

- **Client web interface**: lets the customer search for an item via a chatbot/AI and get feedback on whether the item is available and its quantity.
- **Backoffice**: private interface for employees to access stock and related info. An admin account can create, edit, and delete employee user accounts.

---

## 2. General Architecture

The application is split into several services to follow a modular architecture.

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

Each component has a clear, single responsibility, detailed in section 3.

---

## 3. Component Description

### 3.1 Backoffice

Application used by employees.

**Responsibilities:**
- authentication
- user management
- branch management
- stock management
- access rights control

**Technologies:** FastAPI, SQLAlchemy, PostgreSQL, JWT, bcrypt

### 3.2 Database

Stores only data specific to our application.

**Users**
- id
- username
- hashed password
- role
- associated branch
- active/inactive status

**Branches**
- id
- name
- location

**Stock**
- branch
- product id
- available quantity

**Deliberately excluded data**

Per the project requirements, we never store:
- product name
- product description
- product price
- product image
- product characteristics

We only keep the product identifier (`product_id`), used to query the external API.

### 3.3 Product API

Provided in a Docker container. The single source of truth for product information.

**Allows:**
- retrieving the list of products
- retrieving product details

Our application never modifies this data.

### 3.4 Product MCP Server

Intermediary between the AI and the Product API. Exposes several tools the AI agent can use.

**Available tools**

| Tool | Description |
|---|---|
| `list_products()` | Returns the list of available products |
| `get_product_details(product_id)` | Returns all information about a product |

This way, the AI never talks directly to the external API.

### 3.5 AI Query Service

Service independent from the Backoffice. Its role is to understand user questions.

**Examples:**
- "Which branch has this product in stock?"
- "Give me the details of product 125."

**To answer, the AI agent:**
1. uses the MCP server to get product information
2. queries our database to check available stock
3. builds a response

The AI must never invent information it does not have.

### 3.6 Client Web Interface

Public, no authentication required.

**Contains:**
- an input field
- a send button
- an area displaying the AI's response

---

## 4. Communication Between Services

### 4.1 Backoffice

Chosen architecture: **REST + HTML/CSS/JavaScript**

**Why?** Simple, well suited to CRUD operations, easy to maintain.

**Limitation:** the frontend requires a bit more JavaScript than server-side rendering.

### 4.2 Client Web → AI Service

Chosen architecture: **REST API**.

Since each question is independent, there is no need to maintain a persistent connection.

**Example:**
```
POST /ask
```
with a question. The server responds immediately with an answer.

**Why not WebSocket?**

WebSockets are especially useful when:
- a conversation is continuous
- responses arrive progressively (streaming)
- multiple users communicate in real time

Our project needs none of these. REST is therefore simpler and more appropriate.

### 4.3 AI → MCP

The AI agent communicates with the MCP server via the MCP protocol.

This fully separates the AI logic from product access, making the system more modular.

---

## 5. Authentication and Security

All Backoffice users must be authenticated.

Passwords are stored hashed using **bcrypt**, chosen because it:
- is specifically designed for password storage
- automatically adds a salt
- deliberately slows down computation to limit brute-force attacks

Once logged in, the user receives a **JWT** used for subsequent requests.

### 5.1 Role Management

**Administrator** can:
- create a user
- edit a user
- delete (soft delete) a user
- change a password
- assign a branch

They cannot, however, manage stock.

**Standard user**

Each user belongs to a single branch. They can only:
- view their branch's stock
- add stock
- remove stock

They can never access another branch's stock.

All these checks are performed server-side, to prevent any bypass attempt.

---

## 6. Data Flow

### Example 1

**Question:** "Give me the details of product 152."

1. The client sends the question.
2. The AI Query Service receives the request.
3. The AI agent calls the MCP server.
4. The MCP server queries the Product API.
5. The information is returned to the AI.
6. The AI generates a response.
7. The response is displayed to the client.

### Example 2

**Question:** "Which branch has this product in stock?"

1. The client sends the question.
2. The agent retrieves product information via MCP.
3. It then queries the stock table in PostgreSQL.
4. It identifies the branches holding the product.
5. It builds the final response.

---

## 7. MVP (Minimum Viable Product)

Our priority is to deliver a fully functional project before adding secondary features.

| Step | Content |
|---|---|
| 1 | Database, authentication, user management, branch management |
| 2 | Stock management |
| 3 | Connection to the Product API |
| 4 | MCP server |
| 5 | AI service |
| 6 | Public web interface |

---

## 8. Optional Features

If time allows, we will add:
- a more modern interface
- a stock movement history
- product recommendations
- stock statistics
- streaming AI responses

---

## 9. Conclusion

We chose an architecture made of several independent services to ease maintenance, testing, and evolution of the application.

The main technical choices are driven by simplicity, separation of concerns, and compliance with the project requirements.

- REST is used for HTTP communication, as it fits independent requests well.
- The MCP server acts as an intermediary between the AI and the Product API, making product data access secure and modular.
- PostgreSQL only stores local data (users, branches, and stock), while all product information comes exclusively from the Product API.
- The Backoffice and AI service are deliberately kept separate, to maintain a clear and scalable architecture.
