"""Booking data access and FastAPI routes."""

from fastapi import APIRouter

from .csv_store import read_csv_rows
from .hotels import list_hotels
from .models import Booking, BookingHistoryItem
from .trips import list_trips
from .users import list_users


router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def list_bookings() -> list[Booking]:
    """Read all simulated bookings from the supplied CSV file."""
    return [Booking(**row) for row in read_csv_rows("bookings.csv")]


def list_booking_history() -> list[BookingHistoryItem]:
    """Return bookings joined to their traveler, trip, and hotel details."""
    users_by_id = {user.user_id: user for user in list_users()}
    trips_by_id = {trip.trip_id: trip for trip in list_trips()}
    hotels_by_id = {hotel.hotel_id: hotel for hotel in list_hotels()}

    history: list[BookingHistoryItem] = []
    for booking in list_bookings():
        user = users_by_id[booking.user_id]
        trip = trips_by_id[booking.trip_id]
        hotel = hotels_by_id[trip.hotel_id]
        nights = (trip.check_out - trip.check_in).days

        history.append(
            BookingHistoryItem(
                booking_id=booking.booking_id,
                user_id=user.user_id,
                display_name=user.display_name,
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
                booked_on=booking.booked_on,
                status=booking.status,
            )
        )

    return history


@router.get("/history", response_model=list[BookingHistoryItem])
async def get_booking_history() -> list[BookingHistoryItem]:
    """Return every booking with related display details."""
    return list_booking_history()


@router.get("", response_model=list[Booking])
async def get_bookings() -> list[Booking]:
    """Return every simulated booking."""
    return list_bookings()
