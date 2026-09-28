from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runs once when the server starts.
    create_db_and_tables()
    yield


app = FastAPI(
    title="Inventory API",
    description="A small REST API for managing inventory items.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(items.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API is running."""
    return {"status": "ok"}
