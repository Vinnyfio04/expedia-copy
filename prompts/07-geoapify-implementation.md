# Implement the Geoapify ZIP demonstration

Purpose: Add a credential-safe, fixed-postcode Geoapify demonstration through
the existing FastAPI and Vue boundaries.

## Prompt

```text
Read AGENTS.md, README.md, and the current controller and view code before
editing. Implement a small ZIP lookup demonstration for the fixed string
"16802".

Load the project-root .env through an explicit path derived from a backend
configuration helper. Read GEOAPIFY_API_KEY only in Python. Use Geoapify forward
geocoding with postcode, type=postcode, filter=countrycode:us, and format=json
through the project's HTTP client with a finite timeout. Accept only an exact
U.S. postcode match with finite, valid coordinates. Return a dedicated location
model containing postcode, country code, latitude, longitude, and locality when
available; do not reuse the priced Hotel model.

Expose GET /api/demo/zip-location for the fixed demonstration ZIP. Distinguish
an unresolved location from a provider or configuration failure with structured,
sanitized responses. Never print or return the key, a credential-bearing request
URL, raw provider data, or raw exception text.

Add a focused Vue panel titled "ZIP lookup demonstration" with one button labeled
"Look up ZIP 16802". Request the backend route through the existing /api proxy;
never call Geoapify from Vue. Clear an earlier result when a request starts,
show loading feedback, disable repeated clicks while loading, and display the
postcode, available locality, labeled latitude and longitude, or the backend
error. Preserve hotel-name search.

Do not add a frontend key, VITE variable, ZIP input, map, hotel record, or new
dependency. Add mocked backend coverage for success, mismatched results, and
provider failure plus frontend API-helper coverage. Run backend tests and the
frontend lint, tests, and production build. Verify the visible success and
sanitized failure states, restore normal behavior after any temporary mock, and
document the final contract without exposing credentials.
```
