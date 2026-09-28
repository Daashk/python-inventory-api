# Inventory API

A small REST API for managing inventory items, built with **FastAPI**, **SQLModel** and **SQLite**.

It supports creating, reading, updating and deleting items, enforces unique SKUs, and
adjusts stock levels without ever letting quantity drop below zero.

## Features

- CRUD endpoints for inventory items, with pagination
- Request validation with Pydantic (e.g. no negative prices or quantities)
- Unique SKUs, enforced by a database constraint and reported as `409 Conflict`
- Stock adjustment endpoint that refuses to take quantity below zero
- Prices stored as exact decimals, not floats
- Interactive API documentation generated automatically at `/docs`
- 38 automated tests, each running against a fresh in-memory database
- Linting and formatting with Ruff, checked in CI with GitHub Actions

## Tech stack

| Purpose | Tool |
|---|---|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Database access | [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic) |
| Database | SQLite |
| Tests | pytest + FastAPI `TestClient` |
| Lint / format | [Ruff](https://docs.astral.sh/ruff/) |
| CI | GitHub Actions |

## Getting started

Requires Python 3.13.

```bash
git clone https://github.com/<your-username>/python-inventory-api.git
cd python-inventory-api

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run the development server:

```bash
fastapi dev app/main.py
```

The API is now available at http://127.0.0.1:8000, and the interactive documentation at
http://127.0.0.1:8000/docs.

Data is stored in `inventory.db` in the project folder. Set the `DATABASE_URL`
environment variable to use a different location.

## Running tests and checks

```bash
pytest              # run the test suite
ruff check .        # lint
ruff format .       # format the code
```

## API

| Method | Path | Description | Success |
|---|---|---|---|
| `GET` | `/health` | Check that the API is running | `200` |
| `POST` | `/items` | Create an item | `201` |
| `GET` | `/items?skip=0&limit=100` | List items | `200` |
| `GET` | `/items/{id}` | Get one item | `200` |
| `PATCH` | `/items/{id}` | Update some fields of an item | `200` |
| `DELETE` | `/items/{id}` | Delete an item | `204` |
| `POST` | `/items/{id}/adjust-stock` | Add or remove stock | `200` |

Errors:

| Status | When |
|---|---|
| `404 Not Found` | The item does not exist |
| `409 Conflict` | The SKU is already used by another item, or there is not enough stock |
| `422 Unprocessable Content` | The request body or query parameters are invalid |

An item looks like this:

```json
{
  "id": 1,
  "name": "USB-C Cable",
  "sku": "CAB-USBC-1M",
  "price": "9.99",
  "quantity": 25
}
```

`price` is returned as a string so no precision is lost. It can be sent as either a
number or a string, with at most 2 decimal places.

### Examples

Create an item:

```bash
curl -X POST http://127.0.0.1:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "USB-C Cable", "sku": "CAB-USBC-1M", "price": 9.99, "quantity": 25}'
```

```json
{"name": "USB-C Cable", "sku": "CAB-USBC-1M", "price": "9.99", "quantity": 25, "id": 1}
```

Creating another item with the same SKU returns `409 Conflict`:

```json
{"detail": "Item with SKU 'CAB-USBC-1M' already exists"}
```

Remove 5 units from stock:

```bash
curl -X POST http://127.0.0.1:8000/items/1/adjust-stock \
  -H "Content-Type: application/json" \
  -d '{"amount": -5}'
```

```json
{"name": "USB-C Cable", "sku": "CAB-USBC-1M", "price": "9.99", "quantity": 20, "id": 1}
```

Trying to remove more than is in stock returns `409 Conflict` and changes nothing:

```json
{"detail": "Insufficient stock: quantity is 20, cannot remove 100"}
```

Change only the price:

```bash
curl -X PATCH http://127.0.0.1:8000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"price": "8.49"}'
```

## Project structure

```
app/
├── main.py           # creates the FastAPI app and registers routes
├── database.py       # database engine and per-request session dependency
├── models.py         # database table definitions
├── schemas.py        # request and response models
└── routers/
    └── items.py      # /items endpoints
tests/
├── conftest.py       # test fixtures: in-memory database and test client
└── test_items.py     # API tests
```

## Design decisions

- **Separate table model and API schemas.** `models.py` describes how an item is stored;
  `schemas.py` describes what clients send and receive. For example, clients never send
  an `id`, and `PATCH` accepts any subset of fields.
- **Uniqueness enforced by the database.** Checking for an existing SKU in Python before
  inserting has a race condition: two simultaneous requests could both pass the check.
  A unique index makes the database reject the duplicate; the API catches the
  `IntegrityError` and returns `409 Conflict`.
- **`409` for insufficient stock.** The request itself is valid; it only fails because of
  the item's current state.
- **Decimal prices.** Floats cannot represent most decimal amounts exactly
  (`0.1 + 0.2 != 0.3`), so prices use `Decimal`.
- **IDs are never reused.** The table uses SQLite `AUTOINCREMENT`, so deleting an item
  never frees its ID for a new item.
- **Tests use dependency injection.** Endpoints receive their database session from
  FastAPI, so tests swap in an in-memory database without changing any endpoint code.

## Known limitations

- **No migrations.** Tables are created with `SQLModel.metadata.create_all()` on startup,
  which does not change tables that already exist. After changing a model, delete
  `inventory.db`. Alembic would be the proper solution.
- **Stock adjustments can race.** The endpoint reads the quantity, checks it and then
  writes it, so two simultaneous requests could together remove more stock than exists.
  A single atomic `UPDATE ... WHERE quantity + :amount >= 0` statement would fix this.
- **SKUs are case-sensitive.** `abc-1` and `ABC-1` are different SKUs.
- **No authentication.** Anyone who can reach the API can change the data.

## Possible next steps

- Categories, as a second table with a relationship to items
- Search and filtering (by name, low stock)
- Alembic migrations
- Docker setup
- Authentication
