"""Geoapify-backed postcode lookup logic, independent of API routes."""

from math import isfinite
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from .config import get_geoapify_api_key
from .models import PostcodeLocation


GEOAPIFY_ENDPOINT = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_TIMEOUT_SECONDS = 5.0
DEMO_POSTCODE = "16802"

router = APIRouter(prefix="/api/demo", tags=["demo"])


class PostcodeNotFoundError(LookupError):
    """Raised when Geoapify has no valid match for the requested postcode."""


class GeocodingProviderError(RuntimeError):
    """Raised when Geoapify is unavailable or returns an invalid response."""


def _coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None

    coordinate = float(value)
    if not isfinite(coordinate) or not minimum <= coordinate <= maximum:
        return None
    return coordinate


def _locality(result: dict[str, Any]) -> str | None:
    for field in ("city", "town", "village", "municipality"):
        value = result.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


async def lookup_us_postcode(postcode: str) -> PostcodeLocation:
    """Resolve a U.S. postcode through Geoapify or raise a sanitized error."""
    requested_postcode = postcode.strip()
    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeocodingProviderError("Geoapify is not configured.")

    params = {
        "postcode": requested_postcode,
        "type": "postcode",
        "filter": "countrycode:us",
        "format": "json",
        "apiKey": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=GEOAPIFY_TIMEOUT_SECONDS) as client:
            response = await client.get(GEOAPIFY_ENDPOINT, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError):
        raise GeocodingProviderError("Geoapify request failed.") from None

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise GeocodingProviderError("Geoapify returned an invalid response.")

    for result in payload["results"]:
        if not isinstance(result, dict):
            continue
        if result.get("postcode") != requested_postcode:
            continue
        if str(result.get("country_code", "")).casefold() != "us":
            continue

        latitude = _coordinate(result.get("lat"), -90.0, 90.0)
        longitude = _coordinate(result.get("lon"), -180.0, 180.0)
        if latitude is None or longitude is None:
            continue

        return PostcodeLocation(
            postcode=requested_postcode,
            country_code="US",
            latitude=latitude,
            longitude=longitude,
            locality=_locality(result),
        )

    raise PostcodeNotFoundError(
        f"No U.S. location was found for postcode {requested_postcode}."
    )


@router.get("/zip-location", response_model=PostcodeLocation)
async def get_demo_zip_location() -> PostcodeLocation:
    """Resolve the fixed demonstration postcode without exposing credentials."""
    try:
        return await lookup_us_postcode(DEMO_POSTCODE)
    except PostcodeNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail={"code": "postcode_not_found", "message": str(error)},
        ) from None
    except GeocodingProviderError:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "geocoding_provider_error",
                "message": "The location provider is unavailable.",
            },
        ) from None
