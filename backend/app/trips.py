"""Trip data access and FastAPI routes."""

from fastapi import APIRouter

from .csv_store import read_csv_rows
from .models import Trip


router = APIRouter(prefix="/api/trips", tags=["trips"])


def list_trips() -> list[Trip]:
    """Read all offered stays from the supplied CSV file."""
    return [Trip(**row) for row in read_csv_rows("trips.csv")]


@router.get("", response_model=list[Trip])
async def get_trips() -> list[Trip]:
    """Return every offered stay."""
    return list_trips()
