# Current project handoff

Updated: 2026-09-29

## Repository state

- Current branch: `map-search-implementation`.
- The working tree currently contains user-owned, uncommitted changes to
  `docs/report.md` and a new `docs/images/10-zip-code-search-mockup.jpg`.
  Preserve both and do not overwrite or discard them.
- Generated `model/expedia.db` and SQLite sidecar files are ignored by Git.

## Completed work

- `controller/app/models.py` defines the typed Hotel, User, Trip, Booking, and
  API response contracts.
- `controller/app/database.py` owns SQLite connections, schema initialization,
  foreign-key checks, and CRUD for all four application models.
- `model/seed.sql` contains the tracked initial data. It is applied transactionally
  to a new database and protected by a one-time metadata marker.
- Application reads, booking creation, history, and cancellation use SQLite;
  there is no CSV runtime or bootstrap dependency.
- The original API response shapes remain unchanged, and Vue accesses data only
  through `/api`.
- The existing fixed Geoapify ZIP demonstration remains backend-only and keeps
  provider credentials out of the browser.
- MVC responsibilities and verification rules are recorded in `AGENTS.md`.
- Research and design for the live ZIP-radius hotel search are complete, but
  the live Geoapify Places search, Leaflet map, and dependency installation
  have not been implemented yet.

## Current data model

- 8 hotels
- 11 users
- 18 trips
- 12 bookings
- `trips.hotel_id` references `hotels.hotel_id`.
- `bookings.user_id` references `users.user_id`.
- `bookings.trip_id` references `trips.trip_id`.

## Verification

- Backend: 24 tests pass, including CRUD, reference rejection, one-time seed
  behavior, concurrent initialization, booking flows, API contracts, Geoapify,
  and health reporting.
- The populated local database reports `PRAGMA integrity_check = ok` and no
  rows from `PRAGMA foreign_key_check`.
- HTTP smoke testing returned the expected 8 hotels, 11 users, 18 trips, and 12
  bookings, including the `B001 → U001 + T001 → H001` joined history record.

## Important files

- `AGENTS.md`: MVC and repository rules.
- `README.md`: setup, persistence, and Geoapify contracts.
- `model/seed.sql`: tracked initial relational data.
- `controller/app/database.py`: SQLite schema, initialization, and CRUD.
- `controller/app/models.py`: entity and API models.
- `controller/app/bookings.py`: booking business logic and routes.
- `controller/tests/test_database_api.py`: persistence and API verification.
- `docs/sqlite-mvc-branch-summary.md`: file-by-file branch change and prompt
  inventory.
- `docs/assignment_instructions.md`: authoritative Assignment 2 requirements.
- `docs/images/10-zip-code-search-mockup.jpg`: user-owned early mockup for the
  ZIP search/map feature.

## Assignment 2 Part 1 requirements summarized

- Accept a five-digit U.S. ZIP code as a string so leading zeros are preserved.
- FastAPI must use Geoapify to resolve the requested ZIP to a U.S. postcode
  point and then obtain hotels within 5 km of that exact returned point.
- Do not silently search a different location when the requested ZIP is not
  established by the provider.
- Vue must show the returned hotels in both a list and a Leaflet map. Selecting
  a hotel in one representation must identify the same hotel in the other.
- Distinguish loading, results, invalid input, unresolved ZIP, successful zero
  results, provider failure, and rate-limit/quota failure. Never describe a
  provider failure as a successful empty search.
- Display only fields supported by the provider response. Missing data requires
  an honest label or omission. Do not invent prices, ratings, room availability,
  or booking confirmations.
- Geoapify requests must pass through FastAPI. Keep `GEOAPIFY_API_KEY` in the
  ignored root `.env`; never copy the backend key into frontend configuration.
- Keep map attribution visible and comply with the selected tile provider's
  usage policy.

## Research conclusion

### Adopted provider and map stack

Use this stack:

1. Geoapify Forward Geocoding resolves the exact U.S. postcode.
2. Geoapify Places retrieves nearby hotel place listings.
3. FastAPI owns both provider calls, validation, response normalization, and
   structured error translation.
4. Vue owns the ZIP form, loading/error/result state, list selection, and map
   presentation.
5. Plain Leaflet renders the map and markers.
6. OpenStreetMap Standard raster tiles provide the basemap for this low-volume
   coursework demonstration.

Geoapify has hotel place listings built into the Places API through the
`accommodation.hotel` category. These are points of interest, not live booking
inventory. Results can provide a name, address, coordinates, provider
`place_id`, categories, and distance when requested. They do not establish room
availability, nightly rates, ratings, or exhaustive hotel coverage.

Official sources:

- Geoapify Forward Geocoding:
  https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/
- Geoapify Places and accommodation categories:
  https://apidocs.geoapify.com/docs/places/
- Geoapify pricing:
  https://www.geoapify.com/pricing/
- Geoapify credit calculation:
  https://www.geoapify.com/pricing-details/
- Leaflet reference:
  https://leafletjs.com/reference.html
- Leaflet quick start:
  https://leafletjs.com/examples/quick-start/
- OpenStreetMap tile usage policy:
  https://operations.osmfoundation.org/policies/tiles/

### Free-tier conclusion

- Geoapify's free plan currently provides 3,000 credits per day, up to five
  requests per second, and does not require a credit card.
- A normal search capped at 20 returned places costs about two credits: one
  geocoding request plus one Places request. This gives a theoretical maximum
  of roughly 1,500 searches per day before retries or other API use.
- Keep an explicit result cap and describe the response as nearby matches, not
  a complete hotel inventory.
- Use OpenStreetMap tiles rather than Geoapify tiles for the demonstration so
  map loads do not consume Geoapify search credits or require a browser-visible
  Geoapify key.

### Alternatives considered

- TomTom was the strongest technical fallback. It supports geocoding, hotel POI
  search, circular filters, stable IDs, addresses, and distance, with free
  monthly allowances. It was not selected because the assignment explicitly
  requires Geoapify.
- HERE also supports geocoding and hotel search within a circle and has a useful
  Limited Plan, but it would add a second provider and fail the named-provider
  requirement.
- Foursquare has useful POI data and radius search but needs a separate strict
  ZIP geocoder and has a smaller free allowance.
- Public Nominatim plus Overpass can perform ZIP and hotel searches without a
  paid account, but the public services are rate-limited, best-effort, and have
  no SLA. They also do not satisfy the Geoapify requirement.
- Google Places is not suitable for this design even though free monthly caps
  exist: billing must be enabled, and Google's Places policies require mapped
  Places results to be displayed on a Google map rather than a Leaflet/non-
  Google map.
- Amadeus Hotel List can search around coordinates but requires a separate ZIP
  geocoder and OAuth handling, has limited test data, and is focused on travel
  inventory beyond this assignment's place-discovery needs.

## Proposed backend implementation

### API flow

Proposed route:

`GET /api/hotels/nearby?postcode=16802`

The exact route name may change if an existing controller convention suggests a
better name, but all browser access must stay under `/api`.

Processing sequence:

1. Validate `postcode` as exactly five digits while retaining it as a string.
2. Reuse or extend `lookup_us_postcode(postcode)` in
   `controller/app/geocoding.py`.
3. Accept only a result whose returned postcode exactly matches the request,
   whose country is the U.S., and whose coordinates are valid and finite. This
   strict behavior already exists for the fixed demonstration lookup.
4. Request Geoapify Places using the returned longitude and latitude:

   - `categories=accommodation.hotel`
   - `filter=circle:<longitude>,<latitude>,5000`
   - `bias=proximity:<longitude>,<latitude>` when distance ordering/output is
     desired
   - `limit=20` initially

5. Use the hard `filter=circle` for the required 5 km boundary. A proximity
   bias alone would not guarantee the boundary.
6. Normalize the GeoJSON provider response into typed application models and
   return only the fields Vue needs.

### New typed contracts

Do not reuse the existing local `Hotel` model for external results. It requires
`nightly_rate_usd`, which Geoapify does not provide. Reusing it would encourage
invented data and mix live places with the seeded Hotel/Trip booking model.

Create separate contracts such as:

- `NearbyHotel`
  - `provider`: literal/string identifying Geoapify
  - `provider_place_id`: Geoapify `place_id`
  - `name`: optional string
  - `formatted_address`: optional string
  - `latitude`: float
  - `longitude`: float
  - `distance_meters`: optional nonnegative number
- `NearbyHotelSearchResponse`
  - requested `postcode`
  - resolved search-center latitude and longitude
  - `radius_meters` fixed at 5000
  - result count
  - list of `NearbyHotel`

The provider place ID will later be the natural uniqueness key for the Part 2
shortlist. Saving the same provider place ID twice must not create duplicates.
Saved shortlist records will need a recognizable snapshot of the provider ID,
name/address when present, and coordinates, without a fake nightly rate.

### Provider errors

Keep routes thin and translate expected failures at the HTTP boundary into
structured, sanitized errors. Preserve distinct cases such as:

- invalid five-digit input;
- unresolved or mismatched ZIP;
- successful search with no nearby hotels;
- malformed provider response;
- provider timeout/unavailability;
- provider authentication failure; and
- provider quota/rate limiting.

Do not expose the API key, full request URL, raw provider body, or underlying
exception text.

## Proposed Vue and Leaflet implementation

### Components and state

- Replace or evolve `ZipLookupDemo.vue` into a focused live ZIP-search
  component, or introduce focused ZIP search, result-list, and map components
  if that keeps `App.vue` smaller.
- Put all frontend API access in `view/src/api.js`; components should not call
  Geoapify directly.
- Store the ZIP as a string and validate it with the equivalent of
  `/^\d{5}$/` for immediate feedback. FastAPI must validate it independently.
- Keep one shared reactive value such as `selectedHotelId` containing the
  selected Geoapify `place_id`.
  - Clicking a hotel list button sets this ID and opens/highlights its marker.
  - Clicking a marker sets the same ID and highlights or scrolls to its list
    card.
  - A single source of selection prevents the list and map from disagreeing.
- Clear stale errors and results appropriately when a new search starts.
- Use native buttons for result selection and accessible status regions for
  loading and errors.

### Leaflet choice

Use plain Leaflet rather than `@vue-leaflet/vue-leaflet`. Plain Leaflet is
well documented and sufficient for the feature; the Vue wrapper describes
itself as beta and adds another dependency.

A focused Vue Composition API map component should:

1. create the map in `onMounted`;
2. add the tile layer and visible attribution;
3. create/update markers when the results prop changes;
4. emit the provider place ID when a marker is selected;
5. watch the shared selected ID and open/highlight the matching marker;
6. fit the map to the search center/results or show a sensible 5 km view; and
7. remove the map and listeners in `onBeforeUnmount`.

Expected tile layer for the small demonstration:

`https://tile.openstreetmap.org/{z}/{x}/{y}.png`

Keep `© OpenStreetMap contributors` visible. Do not bulk download or prefetch
tiles. The public tile service is best-effort and has no SLA, so a public or
high-traffic deployment would need a dedicated tile provider. Keep the tile URL
easy to replace.

## Dependency and installation status

- The current frontend runtime dependency is only Vue.
- Leaflet is not installed yet.
- No dependency was installed during the research discussion.
- Under `AGENTS.md`, do not install or upgrade dependencies without explicit
  user approval.
- Before implementation, perform the required CHECK → TAKE ACTION → VERIFY
  sequence:
  1. inspect the existing Node/npm environment and current package state;
  2. explain that the proposed change is `npm install leaflet` in `view/` and
     that it will update `package.json` and `package-lock.json`;
  3. obtain explicit approval;
  4. install Leaflet; and
  5. verify the installed version, import, frontend tests, lint, and build.
- Do not install `@vue-leaflet/vue-leaflet` unless the design is revisited and
  the user explicitly approves the additional dependency.

## Proposed implementation files

Likely files to add or update, subject to inspection before editing:

- `controller/app/models.py`: add live nearby-hotel request/response contracts.
- `controller/app/geocoding.py`: preserve strict ZIP lookup and potentially
  share provider request/error helpers.
- `controller/app/hotels.py` or a focused new controller: Geoapify Places
  request and normalization.
- `controller/app/main.py`: register a new router only if a new controller is
  introduced.
- `controller/tests/`: add provider, validation, error, and route contract
  tests using mocked responses; do not consume live quota in automated tests.
- `view/src/api.js`: add the nearby-hotel request.
- `view/src/components/`: add or update focused ZIP-search, results, and Leaflet
  map components.
- `view/src/App.vue`: integrate the new feature while preserving existing
  booking/history behavior.
- `view/src/style.css`: map, list, selected, loading, and error presentation.
- `view/tests/`: cover validation, API adaptation, state transitions, and
  list/map selection behavior where feasible without a real tile network.
- `README.md`: document Leaflet setup, Geoapify configuration, the new route,
  provider limitations, and attribution.
- `docs/report.md`: preserve the user's current edits and add research/design
  and verification evidence carefully rather than replacing existing content.

## Verification plan

- Unit-test five-digit validation, including a leading-zero ZIP.
- Mock an exact valid U.S. ZIP response and a Geoapify Places response.
- Verify the Places request uses a hard 5,000-meter circle centered on the
  geocoder's returned point.
- Verify mismatched/unresolved ZIP results do not trigger a hotel search.
- Verify provider records are normalized without invented prices or ratings.
- Verify missing names/addresses are honestly labeled or omitted in Vue.
- Verify empty successful results differ from provider failures.
- Simulate timeout, malformed JSON, authentication failure, and quota/rate-limit
  responses without exhausting the live service.
- Verify selecting a list item selects the corresponding marker and selecting a
  marker selects the corresponding list item by the same provider place ID.
- Verify keyboard operation for ZIP submission and hotel selection.
- Run backend tests, frontend tests, frontend lint, and production build.
- For the live demonstration, record the tested ZIP and observation date and do
  not assert a fixed live result count because provider data may change.

## Next task

Begin Assignment 2 Part 1 implementation on `map-search-implementation` after
checking the environment and obtaining explicit approval to install `leaflet`.
Preserve the user-owned `docs/report.md` and mockup changes. Implement the
backend typed Geoapify Places flow first with mocked tests, then add the Vue
search/list/map UI and synchronized `selectedHotelId`, and finally perform the
full verification plan and update the README/report with observed evidence.
