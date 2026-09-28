from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import Item, ItemCreate, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

# In-memory storage. Data is lost when the server restarts.
# This will be replaced by a database in a later step.
items_db: dict[int, Item] = {}
next_id = 1


def get_item_or_404(item_id: int) -> Item:
    item = items_db.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item


@router.post("", status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate) -> Item:
    global next_id
    item = Item(id=next_id, **item_in.model_dump())
    items_db[item.id] = item
    next_id += 1
    return item


@router.get("")
def list_items(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[Item]:
    items = list(items_db.values())
    return items[skip : skip + limit]


@router.get("/{item_id}")
def get_item(item_id: int) -> Item:
    return get_item_or_404(item_id)


@router.patch("/{item_id}")
def update_item(item_id: int, item_in: ItemUpdate) -> Item:
    item = get_item_or_404(item_id)
    # exclude_unset=True keeps only the fields the client actually sent.
    changes = item_in.model_dump(exclude_unset=True)
    updated_item = item.model_copy(update=changes)
    items_db[item_id] = updated_item
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None:
    get_item_or_404(item_id)
    del items_db[item_id]
