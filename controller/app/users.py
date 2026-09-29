"""Traveler business controller and FastAPI routes."""

from fastapi import APIRouter

from .database import get_database_controller
from .models import User


router = APIRouter(prefix="/api/users", tags=["users"])


def list_users() -> list[User]:
    """Return all travelers through the database controller contract."""
    return get_database_controller().list_users()


@router.get("", response_model=list[User])
async def get_users() -> list[User]:
    """Return every demo traveler."""
    return list_users()
