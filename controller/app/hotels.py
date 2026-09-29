"""Hotel business controller and FastAPI routes."""

from fastapi import APIRouter

from .database import get_database_controller
from .models import Hotel


router = APIRouter(prefix="/api/hotels", tags=["hotels"])


def list_hotels() -> list[Hotel]:
    """Return all hotels through the database controller contract."""
    return get_database_controller().list_hotels()


@router.get("", response_model=list[Hotel])
async def get_hotels() -> list[Hotel]:
    """Return every hotel."""
    return list_hotels()
