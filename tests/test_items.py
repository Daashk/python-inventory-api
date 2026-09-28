import pytest

# Prices are returned as strings so no precision is lost (e.g. "9.99").
SAMPLE_ITEM = {"name": "Widget", "sku": "WID-001", "price": "9.99", "quantity": 10}


def create_item(client, **overrides):
    response = client.post("/items", json={**SAMPLE_ITEM, **overrides})
    assert response.status_code == 201
    return response.json()


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- POST /items ---


def test_create_item(client):
    response = client.post("/items", json=SAMPLE_ITEM)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **SAMPLE_ITEM}


def test_create_item_accepts_price_as_number(client):
    response = client.post("/items", json={**SAMPLE_ITEM, "price": 9.99})

    assert response.status_code == 201
    assert response.json()["price"] == "9.99"


def test_create_item_assigns_increasing_ids(client):
    first = create_item(client, sku="A")
    second = create_item(client, sku="B")

    assert first["id"] == 1
    assert second["id"] == 2


def test_create_item_missing_field_returns_422(client):
    payload = {"name": "Widget", "price": 9.99, "quantity": 10}  # no sku

    response = client.post("/items", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", ""),
        ("sku", ""),
        ("price", -1),
        ("price", "9.999"),  # more than 2 decimal places
        ("quantity", -1),
        ("quantity", "many"),
    ],
)
def test_create_item_invalid_value_returns_422(client, field, value):
    response = client.post("/items", json={**SAMPLE_ITEM, field: value})

    assert response.status_code == 422


# --- GET /items ---


def test_list_items_empty(client):
    response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == []


def test_list_items(client):
    create_item(client, sku="A")
    create_item(client, sku="B")

    response = client.get("/items")

    assert response.status_code == 200
    assert [item["sku"] for item in response.json()] == ["A", "B"]


def test_list_items_pagination(client):
    for sku in ["A", "B", "C", "D"]:
        create_item(client, sku=sku)

    response = client.get("/items", params={"skip": 1, "limit": 2})

    assert response.status_code == 200
    assert [item["sku"] for item in response.json()] == ["B", "C"]


def test_list_items_invalid_limit_returns_422(client):
    response = client.get("/items", params={"limit": 0})

    assert response.status_code == 422


# --- GET /items/{id} ---


def test_get_item(client):
    created = create_item(client)

    response = client.get(f"/items/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_item_returns_404(client):
    response = client.get("/items/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Item 999 not found"}


# --- PATCH /items/{id} ---


def test_update_item_changes_only_sent_fields(client):
    created = create_item(client)

    response = client.patch(f"/items/{created['id']}", json={"quantity": 3})

    assert response.status_code == 200
    assert response.json() == {**created, "quantity": 3}
    assert client.get(f"/items/{created['id']}").json()["quantity"] == 3


def test_update_missing_item_returns_404(client):
    response = client.patch("/items/999", json={"quantity": 3})

    assert response.status_code == 404


def test_update_item_invalid_value_returns_422(client):
    created = create_item(client)

    response = client.patch(f"/items/{created['id']}", json={"price": -5})

    assert response.status_code == 422


def test_update_item_null_value_returns_422(client):
    created = create_item(client)

    response = client.patch(f"/items/{created['id']}", json={"name": None})

    assert response.status_code == 422
    assert client.get(f"/items/{created['id']}").json() == created


# --- DELETE /items/{id} ---


def test_delete_item(client):
    created = create_item(client)

    response = client.delete(f"/items/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/items/{created['id']}").status_code == 404


def test_delete_missing_item_returns_404(client):
    response = client.delete("/items/999")

    assert response.status_code == 404


def test_deleted_item_id_is_not_reused(client):
    first = create_item(client, sku="A")
    client.delete(f"/items/{first['id']}")

    second = create_item(client, sku="B")

    assert second["id"] == 2
