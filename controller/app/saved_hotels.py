"""Local saved-hotel routes and demo nightly-data coordination."""

from datetime import date
import re

from fastapi import APIRouter, HTTPException, status

from .database import (
    DatabaseControllerError,
    RecordNotFoundError,
    get_database_controller,
)
from .models import (
    SaveNearbyHotelRequest,
    SavedHotelDeleteResponse,
    SavedHotelSearchResponse,
    SavedNearbyHotel,
)


POSTCODE_PATTERN = re.compile(r"^[0-9]{5}$")
DEMO_STAY_DATES = tuple(date(2026, 10, day) for day in range(10, 15))

router = APIRouter(prefix="/api/hotels/saved", tags=["saved-hotels"])


def _storage_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=500,
        detail={
            "code": "local_storage_unavailable",
            "message": message,
        },
    )


@router.get("", response_model=SavedHotelSearchResponse)
def get_saved_hotels(postcode: str = "") -> SavedHotelSearchResponse:
    """Return saved hotels associated with one ZIP without provider access."""
    if POSTCODE_PATTERN.fullmatch(postcode) is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_postcode",
                "message": "Enter a five-digit U.S. ZIP code.",
            },
        )
    try:
        return get_database_controller().get_saved_hotel_search(postcode)
    except DatabaseControllerError:
        raise _storage_error("Saved hotels could not be loaded.") from None


@router.post("", response_model=SavedNearbyHotel, status_code=status.HTTP_201_CREATED)
def save_hotel(request: SaveNearbyHotelRequest) -> SavedNearbyHotel:
    """Idempotently save one API hotel, its ZIP context, and demo nights."""
    location = request.search_location
    if (
        POSTCODE_PATTERN.fullmatch(location.postcode) is None
        or location.country_code != "US"
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_search_location",
                "message": "A valid resolved U.S. ZIP location is required.",
            },
        )
    try:
        return get_database_controller().save_nearby_hotel(
            request,
            DEMO_STAY_DATES,
        )
    except DatabaseControllerError:
        raise _storage_error("The hotel could not be saved locally.") from None


@router.delete("", response_model=SavedHotelDeleteResponse)
def remove_saved_hotel(hotel_id: str = "") -> SavedHotelDeleteResponse:
    """Remove one saved hotel and all of its local related records."""
    if not hotel_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_hotel_id",
                "message": "A provider hotel ID is required.",
            },
        )
    try:
        get_database_controller().delete_saved_hotel_with_related(hotel_id)
    except RecordNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "saved_hotel_not_found",
                "message": "The saved hotel was not found.",
            },
        ) from None
    except DatabaseControllerError:
        raise _storage_error("The hotel could not be removed locally.") from None
    return SavedHotelDeleteResponse(hotel_id=hotel_id)
