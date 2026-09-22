from fastapi import FastAPI

from .bookings import router as bookings_router
from .hotels import router as hotels_router
from .search import router as search_router
from .trips import router as trips_router
from .users import router as users_router


app = FastAPI(
    title="expedia-copy API",
    version="0.1.0",
)

app.include_router(hotels_router)
app.include_router(trips_router)
app.include_router(users_router)
app.include_router(bookings_router)
app.include_router(search_router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Report whether the API is running."""
    return {"status": "ok"}
