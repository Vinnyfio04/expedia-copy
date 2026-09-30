# Current project handoff

Updated: 2026-09-29

## Repository state

- Current branch: `map-search-implementation`.
- Assignment 2 Part 1 ZIP search and map implementation is complete and
  verified, but the branch changes are not yet committed.
- `docs/report.md` contains a pre-existing user-owned modification. It was
  preserved exactly during implementation, verification, and documentation.
- `docs/images/10-zip-code-search-mockup.jpg` is tracked and remains the visual
  reference for this feature.
- Generated `model/expedia.db`, SQLite sidecars, frontend build output,
  dependency directories, local environments, and secrets remain ignored.

## Implemented Assignment 2 Part 1 feature

- Installed and pinned plain `leaflet` 1.9.4 without adding a Vue wrapper or
  another HTTP library.
- Added typed external-place contracts separate from the priced SQLite Hotel
  model: `NearbyHotel` and `NearbyHotelSearchResponse`.
- Added `GET /api/hotels/nearby?postcode=16802`.
- Reused strict `lookup_us_postcode()` behavior for an exact five-ASCII-digit
  U.S. ZIP match, including leading-zero preservation and coordinate checks.
- Added a focused Geoapify Places controller using:
  - category `accommodation.hotel`;
  - hard `circle:<longitude>,<latitude>,5000` filtering;
  - proximity bias for ordering; and
  - a limit of 20 nearby matches.
- Provider features are normalized, malformed records are skipped, and
  provider place IDs are deduplicated in provider order.
- Errors remain structured and sanitized: HTTP 400 `invalid_postcode`, HTTP 404
  `postcode_not_found`, HTTP 429 `provider_rate_limited`, and HTTP 502
  `provider_unavailable`.
- Replaced the fixed ZIP demonstration with a live Vue ZIP form, result list,
  and Leaflet map.
- `NearbyHotelSearch.vue` owns request and selection state;
  `HotelMap.vue` owns map lifecycle, markers, text-safe popups, and cleanup.
- One `selectedPlaceId` synchronizes selected cards and markers in both
  directions, including card scrolling and popup focus.
- The map uses the exact OpenStreetMap Standard HTTPS tile URL with visible
  attribution.
- Existing SQLite hotel-name search, booking, history, and cancellation flows
  were preserved. No SQLite schema, seed, or database-controller change was
  made for nearby external places.

## Current contracts

### Nearby search response

- `requested_postcode`
- `center`: existing `PostcodeLocation`
- `radius_meters`: 5000
- `count`
- `results`: list of `NearbyHotel`

### NearbyHotel

- `provider`: `geoapify`
- `provider_place_id`: required nonblank string
- optional `name`
- optional `formatted_address`
- valid finite `latitude`
- valid finite `longitude`
- optional nonnegative finite `distance_meters`

External nearby matches have no invented price, rating, availability,
description, or booking claim.

## Verification completed

- Backend: 38 tests passed with Python `unittest`.
- Frontend: 20 tests passed with Node's built-in `node:test`.
- `npm run lint` passed.
- `npm run build` passed.
- Browser smoke testing covered:
  - invalid ZIP and keyboard submission;
  - unresolved ZIP `00000`;
  - live configured-key ZIP `16802`;
  - successful zero results with a centered map and no markers;
  - distinct rate-limit and sanitized unavailable states;
  - card-to-marker and marker-to-card synchronization;
  - popup and keyboard result selection;
  - responsive single-column layout at 390 px; and
  - existing local hotel search, booking screen, and history screen.
- The live ZIP `16802` observation on 2026-09-29 returned 20 capped nearby
  matches. Provider data is live, so that count is not a fixed assertion.
- Browser console inspection found no warnings or errors.
- Automated tests did not contact Geoapify or consume quota.

## Important files

- `AGENTS.md`: MVC and repository rules.
- `README.md`: current setup, route, key requirement, provider limitations, and
  map policy.
- `docs/design-pipeline.md`: implemented MVC structure and request flow.
- `docs/images/10-zip-code-search-mockup.jpg`: early visual reference.
- `controller/app/geocoding.py`: strict exact-U.S.-ZIP resolution.
- `controller/app/nearby_hotels.py`: Places request, normalization, errors, and
  route.
- `controller/app/models.py`: typed local and external API contracts.
- `controller/tests/test_nearby_hotels.py`: provider and route contract tests.
- `view/src/components/NearbyHotelSearch.vue`: form, results, and shared
  selection state.
- `view/src/components/HotelMap.vue`: Leaflet lifecycle and marker behavior.
- `view/src/api.js`: frontend API boundary and structured `ApiError`.
- `view/src/postcode.js`: pure five-digit ASCII ZIP validation.

## Next action

Review the accumulated branch diff, then commit and push only when explicitly
requested. Do not modify or discard the user's existing `docs/report.md` edit.
