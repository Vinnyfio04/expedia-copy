"""Booking data access and FastAPI routes."""

from fastapi import APIRouter

from .csv_store import read_csv_rows
from .models import Booking


router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def list_bookings() -> list[Booking]:
    """Read all simulated bookings from the supplied CSV file."""
    return [Booking(**row) for row in read_csv_rows("bookings.csv")]


@router.get("", response_model=list[Booking])
async def get_bookings() -> list[Booking]:
    """Return every simulated booking."""
    return list_bookings()
