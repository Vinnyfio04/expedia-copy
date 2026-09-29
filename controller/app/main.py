from fastapi import FastAPI

from .bookings import router as bookings_router
from .config import is_geoapify_key_configured
from .geocoding import router as geocoding_router
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
app.include_router(geocoding_router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Report whether the API and required configuration are ready."""
    key_status = (
        "key is configured"
        if is_geoapify_key_configured()
        else "key is not configured"
    )
    return {"status": "ok", "geoapify_api_key": key_status}
