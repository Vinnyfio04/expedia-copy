"""Trip business controller and FastAPI routes."""

from fastapi import APIRouter

from .database import get_database_controller
from .models import Trip


router = APIRouter(prefix="/api/trips", tags=["trips"])


def list_trips() -> list[Trip]:
    """Return all offered stays through the database controller contract."""
    return get_database_controller().list_trips()


@router.get("", response_model=list[Trip])
async def get_trips() -> list[Trip]:
    """Return every offered stay."""
    return list_trips()
