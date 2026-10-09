"""Response models shared by the expedia-copy API endpoints."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator


NonBlankString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]

HotelRagQuestion = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1_000),
]

HotelRagSqlStatement = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4_000),
]

HotelRagAnswerText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4_000),
]

HotelRagSqlTextParameter = Annotated[
    str,
    StringConstraints(max_length=500),
]

HotelRagSqlParameter = HotelRagSqlTextParameter | int | float | bool | None

HotelRagStatus = Literal["answered", "no_matches", "insufficient_data"]

HotelRagPostcode = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{5}$"),
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


class HotelRagQuestionRequest(BaseModel):
    """One stateless natural-language question about saved local hotels."""

    question: HotelRagQuestion


class HotelRagQueryIntent(BaseModel):
    """Normalized search details returned with an LLM SQL proposal."""

    postcode: HotelRagPostcode | None = None
    check_in: date | None = None
    check_out: date | None = None
    requires_availability: bool = False

    @model_validator(mode="after")
    def validate_stay_dates(self) -> "HotelRagQueryIntent":
        """Require a complete, checkout-exclusive interval when dates are present."""
        if (self.check_in is None) != (self.check_out is None):
            raise ValueError("check_in and check_out must be provided together")
        if (
            self.check_in is not None
            and self.check_out is not None
            and self.check_out <= self.check_in
        ):
            raise ValueError("check_out must be after check_in")
        if (
            self.check_in is not None
            and self.check_out is not None
            and (self.check_out - self.check_in).days > 366
        ):
            raise ValueError("the requested stay cannot exceed 366 nights")
        return self


class HotelRagSqlProposal(BaseModel):
    """Structured output expected from the SQL-planning LLM request."""

    sql: HotelRagSqlStatement
    parameters: list[HotelRagSqlParameter] = Field(
        default_factory=list,
        max_length=50,
    )
    intent: HotelRagQueryIntent


class HotelRagRetrievedRecord(BaseModel):
    """One bounded SQLite row available as context for grounded generation."""

    hotel_id: NonBlankString
    name: str | None = None
    address: str | None = None
    latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)
    postcode: HotelRagPostcode | None = None
    locality: str | None = None
    distance_meters: float | None = Field(
        default=None,
        ge=0.0,
        allow_inf_nan=False,
    )
    stay_date: date | None = None
    nightly_rate_cents: int | None = Field(default=None, ge=0)
    rooms_available: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_optional_relationships(self) -> "HotelRagRetrievedRecord":
        """Keep nullable location and nightly relationship fields together."""
        if self.postcode is None and (
            self.locality is not None or self.distance_meters is not None
        ):
            raise ValueError("location details require a postcode")
        night_values = (
            self.stay_date,
            self.nightly_rate_cents,
            self.rooms_available,
        )
        if any(value is None for value in night_values) and not all(
            value is None for value in night_values
        ):
            raise ValueError("nightly evidence fields must be present together")
        return self


class HotelRagNightEvidence(BaseModel):
    """One simulated nightly record displayed as supporting evidence."""

    stay_date: date
    nightly_rate_cents: int = Field(ge=0)
    rooms_available: int = Field(ge=0)


class HotelRagMatch(BaseModel):
    """Deterministically derived hotel and stay facts returned to the View."""

    hotel_id: NonBlankString
    name: str | None = None
    address: str | None = None
    latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)
    postcodes: list[HotelRagPostcode] = Field(default_factory=list, max_length=20)
    localities: list[str] = Field(default_factory=list, max_length=20)
    distance_meters: float | None = Field(
        default=None,
        ge=0.0,
        allow_inf_nan=False,
    )
    nights: list[HotelRagNightEvidence] = Field(default_factory=list, max_length=366)
    missing_nights: list[date] = Field(default_factory=list, max_length=366)
    stay_complete: bool | None = None
    available_for_entire_stay: bool | None = None
    total_cost_cents: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_stay_summary(self) -> "HotelRagMatch":
        """Prevent incomplete evidence from being presented as a complete stay."""
        if self.missing_nights and self.stay_complete is not False:
            raise ValueError("missing nights require stay_complete to be false")
        if self.stay_complete is True:
            if self.available_for_entire_stay is None:
                raise ValueError("a complete stay requires an availability result")
            if self.total_cost_cents is None:
                raise ValueError("a complete stay requires a complete-stay total")
        if self.stay_complete is False:
            if self.available_for_entire_stay is True:
                raise ValueError("an incomplete stay cannot be reported as available")
            if self.total_cost_cents is not None:
                raise ValueError("an incomplete stay cannot have a complete-stay total")
        if self.stay_complete is None:
            if self.available_for_entire_stay is not None:
                raise ValueError("availability requires a requested stay interval")
            if self.total_cost_cents is not None:
                raise ValueError("a total requires a requested stay interval")
            if self.missing_nights:
                raise ValueError("missing nights require a requested stay interval")
        return self


class HotelRagAnswerClaim(BaseModel):
    """Stay facts the answer model must copy for backend verification."""

    hotel_id: NonBlankString
    missing_nights: list[date] = Field(default_factory=list, max_length=366)
    stay_complete: bool | None = None
    available_for_entire_stay: bool | None = None
    total_cost_cents: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_stay_claim(self) -> "HotelRagAnswerClaim":
        """Apply the same completeness rules as the deterministic match."""
        if self.missing_nights and self.stay_complete is not False:
            raise ValueError("missing nights require stay_complete to be false")
        if self.stay_complete is True:
            if self.available_for_entire_stay is None:
                raise ValueError("a complete stay requires an availability result")
            if self.total_cost_cents is None:
                raise ValueError("a complete stay requires a complete-stay total")
        if self.stay_complete is False:
            if self.available_for_entire_stay is True:
                raise ValueError("an incomplete stay cannot be reported as available")
            if self.total_cost_cents is not None:
                raise ValueError("an incomplete stay cannot have a complete-stay total")
        if self.stay_complete is None:
            if self.available_for_entire_stay is not None:
                raise ValueError("availability requires a requested stay interval")
            if self.total_cost_cents is not None:
                raise ValueError("a total requires a requested stay interval")
            if self.missing_nights:
                raise ValueError("missing nights require a requested stay interval")
        return self


class HotelRagAnswerDraft(BaseModel):
    """Structured output expected from the grounded-answer LLM request."""

    status: HotelRagStatus
    answer: HotelRagAnswerText
    cited_hotel_ids: list[NonBlankString] = Field(
        default_factory=list,
        max_length=20,
    )
    claims: list[NonBlankString] = Field(max_length=20)


class HotelRagResponse(BaseModel):
    """Controller-to-View contract for one stateless hotel RAG request."""

    question: HotelRagQuestion
    status: HotelRagStatus
    answer: HotelRagAnswerText
    requested_check_in: date | None = None
    requested_check_out: date | None = None
    matches: list[HotelRagMatch] = Field(default_factory=list, max_length=20)
    data_notice: Literal[
        "Rates and availability are simulated course data."
    ] = "Rates and availability are simulated course data."

    @model_validator(mode="after")
    def validate_requested_stay(self) -> "HotelRagResponse":
        """Keep the public stay interval complete and checkout-exclusive."""
        if (self.requested_check_in is None) != (self.requested_check_out is None):
            raise ValueError(
                "requested_check_in and requested_check_out must be provided together"
            )
        if (
            self.requested_check_in is not None
            and self.requested_check_out is not None
            and self.requested_check_out <= self.requested_check_in
        ):
            raise ValueError("requested_check_out must be after requested_check_in")
        if (
            self.requested_check_in is not None
            and self.requested_check_out is not None
            and (self.requested_check_out - self.requested_check_in).days > 366
        ):
            raise ValueError("the requested stay cannot exceed 366 nights")
        if self.status == "answered" and not self.matches:
            raise ValueError("an answered response requires at least one hotel match")
        if self.status == "no_matches" and self.matches:
            raise ValueError("a no-match response cannot include hotel matches")
        return self
