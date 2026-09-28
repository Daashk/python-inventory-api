from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ItemBase(BaseModel):
    """Fields shared by every item schema."""

    name: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=50)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantity: int = Field(ge=0)


class ItemCreate(ItemBase):
    """Request body for creating an item. All fields are required."""


class ItemUpdate(BaseModel):
    """Request body for a partial update. Send only the fields to change."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    quantity: int | None = Field(default=None, ge=0)

    @field_validator("name", "sku", "price", "quantity")
    @classmethod
    def reject_explicit_null(cls, value):
        # Omitting a field means "don't change it", but sending null would
        # erase a required value, so reject it.
        if value is None:
            raise ValueError("field cannot be null")
        return value


class StockAdjustment(BaseModel):
    """Request body for changing stock. Positive adds, negative removes."""

    amount: int

    @field_validator("amount")
    @classmethod
    def reject_zero(cls, value: int) -> int:
        # Pydantic's Field has no "not equal" constraint, so check it here.
        if value == 0:
            raise ValueError("amount must not be zero")
        return value


class ItemRead(ItemBase):
    """An item as returned by the API."""

    id: int
