# HBntory — System Architecture

## 1. Scope

HBntory is an inventory platform for a company with several physical branches. The agreed non-AI implementation contains:

- an authenticated Backoffice for internal users;
- PostgreSQL for users, branches and stock;
- the supplied read-only Product API;
- a Product MCP Server that exposes controlled product tools;
- a public Client Web Interface for deterministic product and stock searches.

AI agents and an AI Query Service are treated as a stretch goal. They are implemented only after the mandatory Backoffice, Product MCP Server and deterministic Client Web Interface flows are complete and tested. The Client Web Interface ships in the MVP with deterministic, explicit REST search; a natural-language AI layer is added on top only if time remains.

## 2. Components and Responsibilities

### Backoffice Service

The Backoffice is a FastAPI service with a plain HTML, CSS and JavaScript interface. It:

- authenticates internal users;
- enforces roles and branch restrictions in the backend;
- lets the single `admin` user list, create, modify and soft-delete common users;
- lets `admin` change a common user's password or assigned branch;
- prevents `admin` from managing stock;
- lets common users consult, list, add and remove stock only for their assigned branch;
- accesses local data through SQLAlchemy;
- obtains product information from the Product API through read-only REST requests.

There is only one administrator, named `admin`. Common users belong to exactly one branch. The backend derives a common user's branch from the authenticated account rather than trusting a branch submitted by the browser.

### PostgreSQL Database

The local database contains only:

- `users`: username, password hash, role, branch assignment and soft-deletion state;
- `branches`: branch identity and name;
- `stock`: branch, external numeric product ID and available quantity.

It does not contain product names, SKUs, descriptions, prices, images or metadata.

### External Product API

The supplied API is the authoritative source of product information. It:

- lists products;
- returns product details by numeric ID or SKU;
- is read-only;
- does not own or return HBntory stock quantities.

The Backoffice validates product identifiers against this API before creating stock records. It stores only the canonical numeric product `id` returned by the API.

### Product MCP Server

The Product MCP Server is an independent bridge to the external Product API. It exposes at least:

- `list_products`: return available products with useful identifiers and summaries;
- `get_product_details`: return one product by numeric ID or SKU.

It contains no AI. The public Client Service invokes these tools through MCP over Streamable HTTP. The MCP server never modifies products or stores their metadata.

### Public Client Service and Web Interface

The `client_web` component serves an anonymous search page and a small REST backend. It:

- lets visitors search the product catalogue;
- displays details for a selected product;
- shows which branches hold that product and the available quantities;
- lists products held by a selected branch;
- obtains product data through the Product MCP Server;
- performs controlled, read-only stock queries through SQLAlchemy;
- treats every request independently and stores no search history.

The public service cannot create users or change stock.

If time remains after the mandatory scope, an optional AI Query Service is added in front of this component: an independent backend with one or more AI agents that answer natural-language questions by calling the Product MCP Server and controlled stock queries, instead of the deterministic REST search parameters. It would not replace the deterministic client; it would be an additional entry point.

## 3. Data Flow

### Backoffice Authentication

1. A user submits credentials to the Backoffice.
2. The Backoffice retrieves the active user and verifies the password against its Argon2id hash.
3. Successful authentication creates a signed, HTTP-only session cookie.
4. Every protected request reloads the user and checks role, active status and branch assignment.

### Backoffice Stock Consultation

1. A common user requests their stock.
2. The backend obtains the branch from the authenticated account.
3. SQLAlchemy retrieves local product IDs and quantities.
4. The Backoffice retrieves corresponding product details from the Product API.
5. The combined response is displayed without storing product details locally.

### Backoffice Stock Change

1. The backend verifies that the user is an active common user.
2. It derives the user's branch from the authenticated account.
3. It accepts only a positive integer quantity.
4. It validates the product through the Product API.
5. It changes stock inside a database transaction.
6. Removal fails when the available quantity is insufficient.
7. A database constraint guarantees that quantity cannot become negative.

### Public Product and Stock Search

1. An anonymous visitor submits a product or branch search through REST.
2. The Public Client Service calls the Product MCP Server for product information.
3. The MCP server calls the external Product API through read-only REST.
4. When stock is needed, the Public Client Service performs a controlled read-only database query.
5. The service combines the results and returns structured data to the page.
6. No AI-generated answer or search history is involved.

## 4. Security and Integrity Rules

- Passwords are never stored in plain text.
- Argon2id is used because it is designed for password storage and resists brute-force attacks through configurable memory and computation costs.
- The Backoffice uses a signed, HTTP-only, same-site session cookie. State-changing requests use CSRF protection.
- Authentication and authorisation are enforced in the backend.
- `admin` has no branch and cannot use stock operations.
- A common user has exactly one branch and cannot select another branch.
- Soft-deleted users cannot authenticate or retain access.
- Stock changes require positive integers and cannot make quantity negative.
- Public endpoints and database access are read-only.
- Secrets are supplied through environment variables and are not committed.

## 5. Related Deliverables

- [Initial service diagram](initial-service-diagram.md)
- [Communication strategy](communication-strategies.md)
- [MVP definition](mvp-definition.md)
