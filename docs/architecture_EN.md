# HBntory — Backoffice Architecture

## 1. Scope

The assessed implementation scope agreed by the team is the non-AI inventory Backoffice. It includes:

- an authenticated Backoffice for internal users;
- a relational database for users, branches and stock;
- integration with the supplied read-only Product API.

AI agents, an AI Query Service, MCP, a public chat interface, WebSockets and conversation history are outside this delivery scope.

## 2. Components

### Backoffice Service

The Backoffice is a FastAPI service with a plain HTML, CSS and JavaScript interface. It:

- authenticates internal users;
- enforces roles and branch restrictions in the backend;
- lets the single `admin` user list, create, modify and soft-delete common users;
- lets `admin` change a common user's password or assigned branch;
- prevents `admin` from managing stock;
- lets common users consult, list, add and remove stock only for their assigned branch;
- accesses local data through SQLAlchemy;
- obtains product information from the external Product API through read-only REST requests.

There is only one administrator, named `admin`. Common users belong to exactly one branch. The backend derives a common user's branch from the authenticated account rather than trusting a branch supplied by the browser.

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

## 3. Data Flow

### Authentication

1. A user submits credentials to the Backoffice.
2. The Backoffice retrieves the active user and verifies the password against its Argon2id hash.
3. Successful authentication creates a signed, HTTP-only session cookie.
4. Every protected request reloads the user and checks role, active status and branch assignment.

### Viewing Stock

1. The common user requests their stock.
2. The backend obtains the branch from the authenticated account.
3. SQLAlchemy retrieves local product IDs and quantities.
4. The Backoffice retrieves the corresponding product details from the Product API.
5. The combined response is displayed without storing the product details locally.

### Changing Stock

1. The backend verifies that the user is an active common user.
2. It derives the user's branch from the authenticated account.
3. It accepts only a positive integer quantity.
4. It validates the product through the Product API.
5. It changes the stock inside a database transaction.
6. Removal fails if the available quantity is insufficient.
7. A database constraint guarantees that quantity cannot become negative.

### Managing Users

1. The backend verifies the `admin` role.
2. It validates the common user's data and selected branch.
3. New passwords are hashed with Argon2id before storage.
4. Deletion sets the account inactive and records `deleted_at`; the row remains in the database.

## 4. Security Rules

- Passwords are never stored in plain text.
- Argon2id is used because it is designed for password storage and resists brute-force attacks through configurable memory and computation costs.
- The browser authenticates with a signed, HTTP-only, same-site session cookie. State-changing requests use CSRF protection.
- Authentication and authorisation are enforced in the backend, not only in the interface.
- `admin` has no branch and cannot use stock operations.
- A common user has exactly one branch and cannot select another branch.
- Soft-deleted users cannot authenticate or retain access.
- Secrets are supplied through environment variables and are not committed.

## 5. Related Deliverables

- [Initial service diagram](initial-service-diagram.md)
- [Communication strategy](communication-strategies.md)
- [MVP definition](mvp-definition.md)
- [Database schema](database-schema.md)
- [Validation rules](validation-rules.md)
