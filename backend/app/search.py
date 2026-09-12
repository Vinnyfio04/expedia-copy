"""Hotel-stay search logic and its FastAPI route."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from .hotels import list_hotels
from .models import HotelStay, SearchResponse
from .trips import list_trips


router = APIRouter(prefix="/api/search", tags=["search"])


def search_hotel_stays(hotel_name: str) -> SearchResponse:
    """Find stays whose hotel names contain the query, ignoring case."""
    query = hotel_name.strip()
    if not query:
        raise ValueError("Hotel name must not be empty.")

    matching_hotels = {
        hotel.hotel_id: hotel
        for hotel in list_hotels()
        if query.casefold() in hotel.hotel_name.casefold()
    }

    results: list[HotelStay] = []
    for trip in list_trips():
        hotel = matching_hotels.get(trip.hotel_id)
        if hotel is None:
            continue

        nights = (trip.check_out - trip.check_in).days
        results.append(
            HotelStay(
                trip_id=trip.trip_id,
                trip_name=trip.trip_name,
                hotel_id=hotel.hotel_id,
                hotel_name=hotel.hotel_name,
                city=hotel.city,
                state=hotel.state,
                check_in=trip.check_in,
                check_out=trip.check_out,
                nights=nights,
                nightly_rate_usd=hotel.nightly_rate_usd,
                stay_price_usd=nights * hotel.nightly_rate_usd,
            )
        )

    return SearchResponse(query=query, count=len(results), results=results)


@router.get("", response_model=SearchResponse)
async def search_hotels(
    hotel_name: Annotated[str, Query(description="Full or partial hotel name")],
) -> SearchResponse:
    """Return offered stays for hotels matching a name."""
    try:
        return search_hotel_stays(hotel_name)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail={"code": "empty_hotel_name", "message": str(error)},
        ) from error
