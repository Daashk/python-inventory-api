from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import SessionDep
from app.models import Item
from app.schemas import ItemCreate, ItemRead, ItemUpdate, StockAdjustment

router = APIRouter(prefix="/items", tags=["items"])


def get_item_or_404(session: Session, item_id: int) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item


def commit_or_409(session: Session, sku: str) -> None:
    """Commit, turning a unique-SKU violation into HTTP 409 Conflict.

    The only constraint the API can violate is the unique SKU, because
    Pydantic rejects every other invalid value before it reaches the database.
    """
    try:
        session.commit()
    except IntegrityError as exc:
        # A failed commit leaves the session unusable until it is rolled back.
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item with SKU '{sku}' already exists",
        ) from exc


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, session: SessionDep) -> Item:
    item = Item(**item_in.model_dump())
    session.add(item)
    commit_or_409(session, item_in.sku)
    session.refresh(item)  # load the ID the database assigned
    return item


@router.get("", response_model=list[ItemRead])
def list_items(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[Item]:
    statement = select(Item).order_by(Item.id).offset(skip).limit(limit)
    return list(session.exec(statement).all())


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, session: SessionDep) -> Item:
    return get_item_or_404(session, item_id)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(item_id: int, item_in: ItemUpdate, session: SessionDep) -> Item:
    item = get_item_or_404(session, item_id)
    # exclude_unset=True keeps only the fields the client actually sent.
    changes = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(changes)
    session.add(item)
    commit_or_409(session, item.sku)
    session.refresh(item)
    return item


@router.post("/{item_id}/adjust-stock", response_model=ItemRead)
def adjust_stock(
    item_id: int, adjustment: StockAdjustment, session: SessionDep
) -> Item:
    item = get_item_or_404(session, item_id)
    new_quantity = item.quantity + adjustment.amount
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Insufficient stock: quantity is {item.quantity}, "
                f"cannot remove {-adjustment.amount}"
            ),
        )
    # Known limitation: this reads, checks, then writes in separate steps, so
    # two simultaneous requests could both pass the check (a "lost update").
    # A single atomic statement would fix it:
    #   UPDATE item SET quantity = quantity + :amount
    #   WHERE id = :id AND quantity + :amount >= 0
    item.quantity = new_quantity
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, session: SessionDep) -> None:
    item = get_item_or_404(session, item_id)
    session.delete(item)
    session.commit()
