"""Response models shared by the expedia-copy API endpoints."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


NonBlankString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class Hotel(BaseModel):
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: int


class Trip(BaseModel):
    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: date
    check_out: date


class User(BaseModel):
    user_id: str
    display_name: str


class Booking(BaseModel):
    booking_id: str
    user_id: str
    trip_id: str
    booked_on: date
    status: str


class BookingCreate(BaseModel):
    hotel_id: str
    full_name: str
    check_in: date
    check_out: date


class BookingHistoryItem(BaseModel):
    booking_id: str
    user_id: str
    display_name: str
    trip_id: str
    trip_name: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    check_in: date
    check_out: date
    nights: int
    nightly_rate_usd: int
    stay_price_usd: int
    booked_on: date
    status: str


class HotelStay(BaseModel):
    trip_id: str
    trip_name: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    check_in: date
    check_out: date
    nights: int
    nightly_rate_usd: int
    stay_price_usd: int


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[HotelStay]


class PostcodeLocation(BaseModel):
    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: str | None = None


class NearbyHotel(BaseModel):
    """One external hotel place returned by Geoapify."""

    provider: Literal["geoapify"]
    provider_place_id: NonBlankString
    name: str | None = None
    formatted_address: str | None = None
    latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)
    distance_meters: float | None = Field(
        default=None,
        ge=0.0,
        allow_inf_nan=False,
    )


class NearbyHotelSearchResponse(BaseModel):
    """Typed Controller-to-View contract for a nearby-hotel search."""

    requested_postcode: str
    center: PostcodeLocation
    radius_meters: Literal[5000] = 5000
    count: int = Field(ge=0)
    results: list[NearbyHotel]
