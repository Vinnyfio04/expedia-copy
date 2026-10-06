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


class SavedHotel(BaseModel):
    """A Geoapify hotel persisted with its provider identity unchanged."""

    hotel_id: str = Field(min_length=1)
    name: str | None = None
    address: str | None = None
    latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)

    @classmethod
    def from_nearby_hotel(cls, hotel: NearbyHotel) -> "SavedHotel":
        """Map the frozen nearby-hotel API contract to persistence columns."""
        return cls(
            hotel_id=hotel.provider_place_id,
            name=hotel.name,
            address=hotel.formatted_address,
            latitude=hotel.latitude,
            longitude=hotel.longitude,
        )


class DemoHotelNight(BaseModel):
    """Fictional classroom rate and inventory for one saved-hotel night."""

    hotel_id: str = Field(min_length=1)
    stay_date: date
    nightly_rate_cents: int = Field(default=10_000, ge=0)
    rooms_available: int = Field(default=20, ge=0)


class SavedHotelLocation(BaseModel):
    """One saved hotel's association with a resolved ZIP search location."""

    hotel_id: str = Field(min_length=1)
    postcode: str = Field(pattern=r"^[0-9]{5}$")
    country_code: Literal["US"] = "US"
    search_latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    search_longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)
    locality: str | None = None
    distance_meters: float | None = Field(
        default=None,
        ge=0.0,
        allow_inf_nan=False,
    )

    @classmethod
    def from_search(
        cls,
        hotel: NearbyHotel,
        location: PostcodeLocation,
    ) -> "SavedHotelLocation":
        """Map one API result to the ZIP/location where it was discovered."""
        return cls(
            hotel_id=hotel.provider_place_id,
            postcode=location.postcode,
            country_code=location.country_code,
            search_latitude=location.latitude,
            search_longitude=location.longitude,
            locality=location.locality,
            distance_meters=hotel.distance_meters,
        )


class SavedNearbyHotel(NearbyHotel):
    """A saved Geoapify result with fictional classroom nightly data."""

    demo_nights: list[DemoHotelNight] = Field(default_factory=list)


class SaveNearbyHotelRequest(BaseModel):
    """API hotel and resolved search context to persist atomically."""

    hotel: NearbyHotel
    search_location: PostcodeLocation


class SavedHotelSearchResponse(BaseModel):
    """Saved hotels associated with one ZIP plus global saved identities."""

    requested_postcode: str
    center: PostcodeLocation | None = None
    count: int = Field(ge=0)
    results: list[SavedNearbyHotel]
    saved_hotel_ids: list[str]


class SavedHotelDeleteResponse(BaseModel):
    """Confirmation that one saved hotel and its related rows were removed."""

    hotel_id: str
    removed: Literal[True] = True


class NearbyHotelSearchResponse(BaseModel):
    """Typed Controller-to-View contract for a nearby-hotel search."""

    requested_postcode: str
    center: PostcodeLocation
    radius_meters: Literal[5000] = 5000
    count: int = Field(ge=0)
    results: list[NearbyHotel]


class NearbyHotelRateSearchRequest(BaseModel):
    """Dates and occupancy for a rate-enriched nearby-hotel search."""

    postcode: str
    check_in: date
    check_out: date
    adults: int = Field(default=2, ge=1, le=8)


class HotelRateQuote(BaseModel):
    """One LiteAPI quote matched to a Geoapify hotel place."""

    provider: Literal["liteapi"] = "liteapi"
    provider_hotel_id: NonBlankString
    currency: NonBlankString
    stay_total: float = Field(ge=0.0, allow_inf_nan=False)
    average_nightly_rate: float = Field(ge=0.0, allow_inf_nan=False)
    nights: int = Field(ge=1)
    taxes_included: bool | None = None


class RatedNearbyHotel(NearbyHotel):
    """A Geoapify hotel place with an optional live LiteAPI quote."""

    rate: HotelRateQuote | None = None


class NearbyHotelRateSearchResponse(BaseModel):
    """Geoapify nearby results enriched with date-specific LiteAPI rates."""

    requested_postcode: str
    center: PostcodeLocation
    radius_meters: Literal[5000] = 5000
    check_in: date
    check_out: date
    adults: int = Field(ge=1, le=8)
    currency: Literal["USD"] = "USD"
    rates_status: Literal[
        "available",
        "partial",
        "no_availability",
        "not_configured",
        "provider_unavailable",
    ]
    count: int = Field(ge=0)
    results: list[RatedNearbyHotel]
