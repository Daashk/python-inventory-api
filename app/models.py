from decimal import Decimal

from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    """The items table in the database."""

    # By default SQLite reuses the ID of the most recently deleted row.
    # AUTOINCREMENT makes it always use a new ID instead.
    __table_args__ = {"sqlite_autoincrement": True}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    # unique=True makes the database itself reject a second row with the
    # same SKU, even if two requests try to create it at the same moment.
    sku: str = Field(max_length=50, unique=True, index=True)
    price: Decimal = Field(max_digits=10, decimal_places=2)
    quantity: int
