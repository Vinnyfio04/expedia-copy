"""LiteAPI rate lookup and conservative matching to Geoapify hotel places."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import asin, cos, isfinite, radians, sin, sqrt
import re
from typing import Any

import httpx

from .config import get_liteapi_api_key
from .models import HotelRateQuote, NearbyHotel, PostcodeLocation, RatedNearbyHotel


LITEAPI_RATES_ENDPOINT = "https://api.liteapi.travel/v3.0/hotels/rates"
LITEAPI_TIMEOUT_SECONDS = 12.0
LITEAPI_RESULT_LIMIT = 200
MATCH_DISTANCE_METERS = 1000.0


class LiteApiProviderError(RuntimeError):
    """Raised when LiteAPI cannot provide a usable rate response."""

    def __init__(self, message: str, *, code: str = "provider_unavailable") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LiteApiOffer:
    """Normalized minimum data needed to match and display one hotel rate."""

    hotel_id: str
    name: str
    address: str | None
    latitude: float | None
    longitude: float | None
    quote: HotelRateQuote


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if isfinite(value) and value >= 0 else None


def _coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if isfinite(value) and minimum <= value <= maximum else None


def _normalized(value: str | None) -> str:
    return "" if value is None else "".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _location(hotel: dict[str, Any]) -> tuple[float | None, float | None]:
    location = hotel.get("location")
    if not isinstance(location, dict):
        return None, None
    return (
        _coordinate(location.get("latitude"), -90.0, 90.0),
        _coordinate(location.get("longitude"), -180.0, 180.0),
    )


def _price(rate_data: dict[str, Any]) -> tuple[float, str, bool | None] | None:
    room_types = rate_data.get("roomTypes")
    if not isinstance(room_types, list) or not room_types:
        return None
    room_type = room_types[0]
    if not isinstance(room_type, dict):
        return None

    rates = room_type.get("rates")
    rate = rates[0] if isinstance(rates, list) and rates else None
    retail_rate = rate.get("retailRate") if isinstance(rate, dict) else None
    totals = retail_rate.get("total") if isinstance(retail_rate, dict) else None
    total = totals[0] if isinstance(totals, list) and totals else None

    amount = _number(total.get("amount")) if isinstance(total, dict) else None
    currency = _text(total.get("currency")) if isinstance(total, dict) else None
    if amount is None or currency is None:
        offer_total = room_type.get("offerRetailRate")
        if not isinstance(offer_total, dict):
            return None
        amount = _number(offer_total.get("amount"))
        currency = _text(offer_total.get("currency"))
    if amount is None or currency is None:
        return None

    taxes_included: bool | None = None
    taxes = retail_rate.get("taxesAndFees") if isinstance(retail_rate, dict) else None
    if isinstance(taxes, list) and taxes:
        flags = [item.get("included") for item in taxes if isinstance(item, dict)]
        if flags and all(isinstance(flag, bool) for flag in flags):
            taxes_included = all(flags)
    return amount, currency.upper(), taxes_included


def normalize_liteapi_offers(payload: Any, nights: int) -> list[LiteApiOffer]:
    """Return usable LiteAPI offers joined to their included hotel metadata."""
    if not isinstance(payload, dict):
        raise ValueError("Invalid LiteAPI response.")
    rate_rows = payload.get("data")
    hotels = payload.get("hotels")
    if not isinstance(rate_rows, list) or not isinstance(hotels, list):
        raise ValueError("Invalid LiteAPI response.")

    hotels_by_id: dict[str, dict[str, Any]] = {}
    for hotel in hotels:
        if not isinstance(hotel, dict):
            continue
        hotel_id = _text(hotel.get("id")) or _text(hotel.get("hotelId"))
        if hotel_id is not None:
            hotels_by_id[hotel_id] = hotel

    offers: list[LiteApiOffer] = []
    for rate_data in rate_rows:
        if not isinstance(rate_data, dict):
            continue
        hotel_id = _text(rate_data.get("hotelId"))
        hotel = hotels_by_id.get(hotel_id or "")
        price = _price(rate_data)
        if hotel_id is None or hotel is None or price is None:
            continue
        name = _text(hotel.get("name"))
        if name is None:
            continue
        amount, currency, taxes_included = price
        try:
            average = (
                Decimal(str(amount)) / Decimal(nights)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ZeroDivisionError):
            continue
        latitude, longitude = _location(hotel)
        offers.append(
            LiteApiOffer(
                hotel_id=hotel_id,
                name=name,
                address=_text(hotel.get("address")),
                latitude=latitude,
                longitude=longitude,
                quote=HotelRateQuote(
                    provider_hotel_id=hotel_id,
                    currency=currency,
                    stay_total=amount,
                    average_nightly_rate=float(average),
                    nights=nights,
                    taxes_included=taxes_included,
                ),
            )
        )
    return offers


def _distance_meters(hotel: NearbyHotel, offer: LiteApiOffer) -> float | None:
    if offer.latitude is None or offer.longitude is None:
        return None
    earth_radius = 6_371_000.0
    lat1 = radians(hotel.latitude)
    lat2 = radians(offer.latitude)
    delta_lat = lat2 - lat1
    delta_lon = radians(offer.longitude - hotel.longitude)
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return earth_radius * 2 * asin(sqrt(value))


def _match_offer(hotel: NearbyHotel, offers: list[LiteApiOffer]) -> LiteApiOffer | None:
    normalized_name = _normalized(hotel.name)
    if not normalized_name:
        return None
    candidates = [offer for offer in offers if _normalized(offer.name) == normalized_name]
    candidates = [
        offer
        for offer in candidates
        if (_distance_meters(hotel, offer) or 0.0) <= MATCH_DISTANCE_METERS
    ]
    if len(candidates) == 1:
        return candidates[0]

    normalized_address = _normalized(hotel.formatted_address)
    if normalized_address:
        address_matches = [
            offer
            for offer in candidates
            if _normalized(offer.address)
            and (
                _normalized(offer.address) in normalized_address
                or normalized_address in _normalized(offer.address)
            )
        ]
        if len(address_matches) == 1:
            return address_matches[0]
    return None


def attach_liteapi_rates(
    hotels: list[NearbyHotel],
    offers: list[LiteApiOffer],
) -> list[RatedNearbyHotel]:
    """Preserve Geoapify order while attaching only confident LiteAPI matches."""
    return [
        RatedNearbyHotel(
            **hotel.model_dump(),
            rate=(matched.quote if (matched := _match_offer(hotel, offers)) else None),
        )
        for hotel in hotels
    ]


async def request_liteapi_rates(
    center: PostcodeLocation,
    check_in: date,
    check_out: date,
    adults: int,
    radius_meters: int,
) -> list[LiteApiOffer]:
    """Request the cheapest available LiteAPI offer near the Geoapify center."""
    api_key = get_liteapi_api_key()
    if api_key is None:
        raise LiteApiProviderError("LiteAPI is not configured.", code="not_configured")

    nights = (check_out - check_in).days
    payload = {
        "occupancies": [{"adults": adults}],
        "currency": "USD",
        "guestNationality": "US",
        "checkin": check_in.isoformat(),
        "checkout": check_out.isoformat(),
        "latitude": center.latitude,
        "longitude": center.longitude,
        "radius": radius_meters,
        "limit": LITEAPI_RESULT_LIMIT,
        "maxRatesPerHotel": 1,
        "includeHotelData": True,
    }
    try:
        async with httpx.AsyncClient(timeout=LITEAPI_TIMEOUT_SECONDS) as client:
            response = await client.post(
                LITEAPI_RATES_ENDPOINT,
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            if response.status_code == 204:
                return []
            response_payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError):
        raise LiteApiProviderError("LiteAPI request failed.") from None

    try:
        return normalize_liteapi_offers(response_payload, nights)
    except ValueError:
        raise LiteApiProviderError("LiteAPI returned an invalid response.") from None
