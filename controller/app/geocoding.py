"""Geoapify-backed postcode lookup logic, independent of API routes."""

from math import isfinite
from typing import Any

import httpx

from .config import get_geoapify_api_key
from .models import PostcodeLocation


GEOAPIFY_ENDPOINT = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_TIMEOUT_SECONDS = 5.0
PROVIDER_RATE_LIMITED = "provider_rate_limited"
PROVIDER_UNAVAILABLE = "provider_unavailable"


class PostcodeNotFoundError(LookupError):
    """Raised when Geoapify has no valid match for the requested postcode."""


class GeocodingProviderError(RuntimeError):
    """Raised when Geoapify is unavailable or returns an invalid response."""

    def __init__(
        self,
        message: str,
        *,
        code: str = PROVIDER_UNAVAILABLE,
    ) -> None:
        super().__init__(message)
        self.code = code


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
