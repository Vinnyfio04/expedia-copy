"""Hotel data access and FastAPI routes."""

from fastapi import APIRouter

from .csv_store import read_csv_rows
from .models import Hotel


router = APIRouter(prefix="/api/hotels", tags=["hotels"])


def list_hotels() -> list[Hotel]:
    """Read all hotels from the supplied CSV file."""
    return [Hotel(**row) for row in read_csv_rows("hotels.csv")]


@router.get("", response_model=list[Hotel])
async def get_hotels() -> list[Hotel]:
    """Return every hotel."""
    return list_hotels()
