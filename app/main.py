from fastapi import FastAPI

app = FastAPI(
    title="Inventory API",
    description="A small REST API for managing inventory items.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API is running."""
    return {"status": "ok"}
