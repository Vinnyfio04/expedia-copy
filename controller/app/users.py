"""Demo traveler data access and FastAPI routes."""

from fastapi import APIRouter

from .csv_store import read_csv_rows
from .models import User


router = APIRouter(prefix="/api/users", tags=["users"])


def list_users() -> list[User]:
    """Read all demo travelers from the supplied CSV file."""
    return [User(**row) for row in read_csv_rows("users.csv")]


@router.get("", response_model=list[User])
async def get_users() -> list[User]:
    """Return every demo traveler."""
    return list_users()
