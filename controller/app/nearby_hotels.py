"""Geoapify nearby-hotel normalization for the live postcode search."""

from math import isfinite
import re
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from .config import get_geoapify_api_key
from .geocoding import (
    GEOAPIFY_TIMEOUT_SECONDS,
    PROVIDER_RATE_LIMITED,
    PROVIDER_UNAVAILABLE,
    GeocodingProviderError,
    PostcodeNotFoundError,
    lookup_us_postcode,
)
from .models import NearbyHotel, NearbyHotelSearchResponse, PostcodeLocation


GEOAPIFY_PLACES_ENDPOINT = "https://api.geoapify.com/v2/places"
HOTEL_CATEGORY = "accommodation.hotel"
NEARBY_HOTEL_LIMIT = 20
NEARBY_RADIUS_METERS = 5000
POSTCODE_PATTERN = re.compile(r"^[0-9]{5}$")

router = APIRouter(prefix="/api/hotels", tags=["hotels"])


def _number(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None

    number = float(value)
    if not isfinite(number) or not minimum <= number <= maximum:
        return None
    return number


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _distance(value: Any) -> float | None:
    return _number(value, 0.0, float("inf"))


def normalize_geoapify_hotels(payload: Any) -> list[NearbyHotel]:
    """Return valid unique hotel places in the provider's original order."""
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise ValueError("Invalid Geoapify Places response.")

    hotels: list[NearbyHotel] = []
    seen_place_ids: set[str] = set()

    for feature in payload["features"]:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            continue

        place_id = _optional_text(properties.get("place_id"))
        latitude = _number(properties.get("lat"), -90.0, 90.0)
        longitude = _number(properties.get("lon"), -180.0, 180.0)
        if (
            place_id is None
            or latitude is None
            or longitude is None
            or place_id in seen_place_ids
        ):
            continue

        hotels.append(
            NearbyHotel(
                provider="geoapify",
                provider_place_id=place_id,
                name=_optional_text(properties.get("name")),
                formatted_address=_optional_text(properties.get("formatted")),
                latitude=latitude,
                longitude=longitude,
                distance_meters=_distance(properties.get("distance")),
            )
        )
        seen_place_ids.add(place_id)

    return hotels


async def request_geoapify_hotels(center: PostcodeLocation) -> list[NearbyHotel]:
    """Request up to 20 Geoapify hotel matches within the required radius."""
    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeocodingProviderError("Geoapify is not configured.")

    longitude = center.longitude
    latitude = center.latitude
    params = {
        "categories": HOTEL_CATEGORY,
        "filter": f"circle:{longitude},{latitude},{NEARBY_RADIUS_METERS}",
        "bias": f"proximity:{longitude},{latitude}",
        "limit": NEARBY_HOTEL_LIMIT,
        "apiKey": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=GEOAPIFY_TIMEOUT_SECONDS) as client:
            response = await client.get(GEOAPIFY_PLACES_ENDPOINT, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as error:
        code = (
            PROVIDER_RATE_LIMITED
            if error.response.status_code == 429
            else PROVIDER_UNAVAILABLE
        )
        raise GeocodingProviderError(
            "Geoapify request failed.",
            code=code,
        ) from None
    except (httpx.HTTPError, ValueError, TypeError):
        raise GeocodingProviderError("Geoapify request failed.") from None

    try:
        return normalize_geoapify_hotels(payload)
    except ValueError:
        raise GeocodingProviderError("Geoapify returned an invalid response.") from None


def _provider_http_error(error: GeocodingProviderError) -> HTTPException:
    if error.code == PROVIDER_RATE_LIMITED:
        return HTTPException(
            status_code=429,
            detail={
                "code": PROVIDER_RATE_LIMITED,
                "message": "The hotel provider is temporarily rate limited.",
            },
        )
    return HTTPException(
        status_code=502,
        detail={
            "code": PROVIDER_UNAVAILABLE,
            "message": "The hotel provider is unavailable.",
        },
    )


@router.get("/nearby", response_model=NearbyHotelSearchResponse)
async def get_nearby_hotels(postcode: str = "") -> NearbyHotelSearchResponse:
    """Resolve a U.S. postcode and return nearby Geoapify hotel matches."""
    if POSTCODE_PATTERN.fullmatch(postcode) is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_postcode",
                "message": "Enter a five-digit U.S. ZIP code.",
            },
        )

    try:
        center = await lookup_us_postcode(postcode)
        hotels = await request_geoapify_hotels(center)
    except PostcodeNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "postcode_not_found",
                "message": str(error),
            },
        ) from None
    except GeocodingProviderError as error:
        raise _provider_http_error(error) from None

    return NearbyHotelSearchResponse(
        requested_postcode=postcode,
        center=center,
        radius_meters=NEARBY_RADIUS_METERS,
        count=len(hotels),
        results=hotels,
    )
