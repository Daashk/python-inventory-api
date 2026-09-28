from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import SessionDep
from app.models import Item
from app.schemas import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


def get_item_or_404(session: Session, item_id: int) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, session: SessionDep) -> Item:
    item = Item(**item_in.model_dump())
    session.add(item)
    session.commit()
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
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, session: SessionDep) -> None:
    item = get_item_or_404(session, item_id)
    session.delete(item)
    session.commit()
