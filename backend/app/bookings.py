"""Booking data access and FastAPI routes."""

from datetime import date
from threading import Lock

from fastapi import APIRouter, HTTPException, status

from .csv_store import append_csv_rows, read_csv_rows, update_csv_row
from .hotels import list_hotels
from .models import Booking, BookingCreate, BookingHistoryItem
from .trips import list_trips
from .users import list_users


router = APIRouter(prefix="/api/bookings", tags=["bookings"])
booking_write_lock = Lock()


def _next_identifier(prefix: str, identifiers: list[str]) -> str:
    """Return the next zero-padded identifier for one CSV table."""
    suffixes = [
        int(identifier[len(prefix) :])
        for identifier in identifiers
        if identifier.startswith(prefix) and identifier[len(prefix) :].isdigit()
    ]
    return f"{prefix}{max(suffixes, default=0) + 1:03d}"


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


def create_booking(
    request: BookingCreate,
    booked_on: date | None = None,
) -> BookingHistoryItem:
    """Create a traveler, custom trip when needed, and confirmed booking."""
    full_name = " ".join(request.full_name.split())
    if len(full_name.split()) < 2:
        raise ValueError("Enter both a first and last name.")
    if request.check_out <= request.check_in:
        raise ValueError("Check-out must be after check-in.")

    with booking_write_lock:
        hotels = list_hotels()
        hotel = next(
            (item for item in hotels if item.hotel_id == request.hotel_id),
            None,
        )
        if hotel is None:
            raise LookupError("The selected hotel was not found.")

        users = list_users()
        user = next(
            (item for item in users if item.display_name.casefold() == full_name.casefold()),
            None,
        )

        trips = list_trips()
        trip = next(
            (
                item
                for item in trips
                if item.hotel_id == hotel.hotel_id
                and item.check_in == request.check_in
                and item.check_out == request.check_out
            ),
            None,
        )

        rows_to_append: list[tuple[str, dict[str, str]]] = []
        if user is None:
            user_id = _next_identifier("U", [item.user_id for item in users])
            rows_to_append.append(
                (
                    "users.csv",
                    {"user_id": user_id, "display_name": full_name},
                )
            )
        else:
            user_id = user.user_id

        if trip is None:
            trip_id = _next_identifier("T", [item.trip_id for item in trips])
            trip_name = f"{hotel.hotel_name} stay"
            rows_to_append.append(
                (
                    "trips.csv",
                    {
                        "trip_id": trip_id,
                        "hotel_id": hotel.hotel_id,
                        "trip_name": trip_name,
                        "check_in": request.check_in.isoformat(),
                        "check_out": request.check_out.isoformat(),
                    },
                )
            )
        else:
            trip_id = trip.trip_id
            trip_name = trip.trip_name

        bookings = list_bookings()
        booking_id = _next_identifier(
            "B",
            [item.booking_id for item in bookings],
        )
        booking_date = booked_on or date.today()
        rows_to_append.append(
            (
                "bookings.csv",
                {
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "trip_id": trip_id,
                    "booked_on": booking_date.isoformat(),
                    "status": "confirmed",
                },
            )
        )

        append_csv_rows(rows_to_append)

    nights = (request.check_out - request.check_in).days
    return BookingHistoryItem(
        booking_id=booking_id,
        user_id=user_id,
        display_name=full_name,
        trip_id=trip_id,
        trip_name=trip_name,
        hotel_id=hotel.hotel_id,
        hotel_name=hotel.hotel_name,
        city=hotel.city,
        state=hotel.state,
        check_in=request.check_in,
        check_out=request.check_out,
        nights=nights,
        nightly_rate_usd=hotel.nightly_rate_usd,
        stay_price_usd=nights * hotel.nightly_rate_usd,
        booked_on=booking_date,
        status="confirmed",
    )


def cancel_booking(booking_id: str) -> BookingHistoryItem:
    """Mark one booking as canceled while preserving its CSV row."""
    with booking_write_lock:
        update_csv_row(
            "bookings.csv",
            "booking_id",
            booking_id,
            {"status": "canceled"},
        )
        return next(
            booking
            for booking in list_booking_history()
            if booking.booking_id == booking_id
        )


@router.get("/history", response_model=list[BookingHistoryItem])
async def get_booking_history() -> list[BookingHistoryItem]:
    """Return every booking with related display details."""
    return list_booking_history()


@router.post(
    "",
    response_model=BookingHistoryItem,
    status_code=status.HTTP_201_CREATED,
)
async def post_booking(request: BookingCreate) -> BookingHistoryItem:
    """Persist a confirmed booking and its related CSV records."""
    try:
        return create_booking(request)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/{booking_id}/cancel", response_model=BookingHistoryItem)
async def patch_booking_as_canceled(booking_id: str) -> BookingHistoryItem:
    """Persist a canceled status without deleting the booking."""
    try:
        return cancel_booking(booking_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("", response_model=list[Booking])
async def get_bookings() -> list[Booking]:
    """Return every simulated booking."""
    return list_bookings()
