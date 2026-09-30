# expedia-copy Design Pipeline

## MVC boundary

The repository follows the MVC responsibilities recorded in `AGENTS.md`:

- **Model:** `controller/app/models.py` defines database entities and API
  contracts. `model/seed.sql` is the immutable first-run SQLite seed, while the
  generated `model/expedia.db` is ignored.
- **View:** Vue components, browser state, Leaflet behavior, API helpers, and all
  CSS stay under `view/src/`. The browser exchanges JSON only through `/api` and
  never reads SQLite or receives the Geoapify credential.
- **Controller:** FastAPI routes and business controllers stay under
  `controller/app/`. `database.py` alone opens SQLite. `geocoding.py` resolves a
  strict U.S. ZIP, and `nearby_hotels.py` owns the Geoapify Places request,
  normalization, and nearby-search route.

`App.vue` coordinates stays, booking, and booking-history screens.
`NearbyHotelSearch.vue` owns ZIP input and result state, while `HotelMap.vue`
owns Leaflet map creation, markers, popups, view changes, and cleanup.

## Current project-file map

Generated output, dependency directories, caches, the ignored `.env`, and the
generated SQLite database are omitted.

```text
assignment1/
|-- AGENTS.md
|-- README.md
|-- controller/
|   |-- requirements.txt
|   |-- app/
|   |   |-- bookings.py
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- geocoding.py
|   |   |-- hotels.py
|   |   |-- main.py
|   |   |-- models.py
|   |   |-- nearby_hotels.py
|   |   |-- search.py
|   |   |-- trips.py
|   |   `-- users.py
|   `-- tests/
|       |-- test_database_api.py
|       |-- test_geocoding.py
|       |-- test_health.py
|       `-- test_nearby_hotels.py
|-- model/
|   |-- README.md
|   `-- seed.sql
|-- view/
|   |-- package.json
|   |-- package-lock.json
|   |-- vite.config.js
|   |-- src/
|   |   |-- App.vue
|   |   |-- api.js
|   |   |-- booking.js
|   |   |-- history.js
|   |   |-- main.js
|   |   |-- navigation.js
|   |   |-- postcode.js
|   |   |-- style.css
|   |   |-- travelLinks.js
|   |   `-- components/
|   |       |-- BookingHistory.vue
|   |       |-- BookingScreen.vue
|   |       |-- HotelMap.vue
|   |       `-- NearbyHotelSearch.vue
|   `-- tests/
|       |-- api.test.js
|       |-- booking.test.js
|       |-- history.test.js
|       |-- navigation.test.js
|       |-- postcode.test.js
|       `-- travelLinks.test.js
|-- docs/
|   |-- assignment_instructions.md
|   |-- design-pipeline.md
|   |-- report.md
|   |-- sqlite-mvc-branch-summary.md
|   `-- images/
|       `-- 10-zip-code-search-mockup.jpg
|-- prompts/
`-- handoffs/
    `-- current.md
```

## Live ZIP-to-map flow

```text
User submits a five-character ZIP string
                    |
                    v
NearbyHotelSearch.vue + postcode.js
  require exactly five ASCII digits
  clear stale results and selectedPlaceId
                    |
                    v
view/src/api.js searchNearbyHotels()
                    |
                    v
GET /api/hotels/nearby?postcode=... through the Vite proxy
                    |
                    v
controller/app/nearby_hotels.py
  validates again and calls lookup_us_postcode()
                    |
                    v
controller/app/geocoding.py -> Geoapify Forward Geocoding
  accept only the exact requested U.S. postcode
  reject invalid or nonfinite coordinates
                    |
           unresolved? -- yes --> 404; do not call Places
                    |
                    no
                    v
Geoapify Places
  categories=accommodation.hotel
  filter=circle:<longitude>,<latitude>,5000
  bias=proximity:<longitude>,<latitude>
  limit=20
                    |
                    v
normalize, skip malformed features, and stable-deduplicate by place_id
                    |
                    v
NearbyHotelSearchResponse JSON
  requested_postcode, center, radius_meters, count, results
                    |
                    v
NearbyHotelSearch.vue renders a result list
HotelMap.vue renders the center and Leaflet markers
                    |
                    v
selectedPlaceId synchronizes card highlight, marker focus, and popup
```

The Geoapify key is read only by Python from the ignored project-root `.env`.
The frontend never calls Geoapify directly. A successful empty result still
returns the resolved center, allowing the map to display the search area with no
hotel markers.

## Nearby-hotel contract and errors

`NearbyHotel` is deliberately separate from the priced SQLite `Hotel` entity.
It contains only the provider, nonblank provider place ID, optional name and
formatted address, valid coordinates, and an optional nonnegative provider
distance. The application does not invent prices, ratings, availability,
descriptions, or booking claims for external places.

The route uses these externally meaningful error codes:

- `invalid_postcode` with HTTP 400;
- `postcode_not_found` with HTTP 404;
- `provider_rate_limited` with HTTP 429; and
- `provider_unavailable` with HTTP 502.

Provider messages are sanitized. Credentials, credential-bearing URLs, raw
provider bodies, and underlying exception text are never returned.

## Leaflet and selection behavior

The View uses plain Leaflet 1.9.4. `HotelMap.vue` imports no credentials and uses
the replaceable HTTPS tile constant:

```text
https://tile.openstreetmap.org/{z}/{x}/{y}.png
```

The map keeps `© OpenStreetMap contributors` visible. Standard Leaflet marker
assets are used through Vite. The application does not prefetch, bulk-download,
proxy, or disable browser caching for tiles.

One `selectedPlaceId` in `NearbyHotelSearch.vue` is the selection source of
truth. Selecting a native-button card pans to and opens its marker without
resetting zoom. Selecting a marker emits its place ID, highlights the matching
card, and scrolls it into view. Popup content is built with DOM text nodes rather
than provider-supplied HTML.

## Existing SQLite flows

Hotel-name search remains separate from live nearby matches. It reads the seeded
SQLite Hotel and Trip records through FastAPI and retains its booking behavior.
Selecting a seeded hotel opens `BookingScreen.vue`; booking submission writes
linked user, trip, and booking rows transactionally. `BookingHistory.vue` reads
the joined history, and cancellation updates status without deleting the record.

`database.py` creates and seeds a new database once, enables foreign keys for
every connection, and validates relationships with
`PRAGMA foreign_key_check`. Restarting does not duplicate or restore rows.

## Verification evidence

Verification on 2026-09-29 produced the following observed results:

- 38 backend `unittest` tests passed.
- 20 frontend `node:test` tests passed.
- `npm run lint` and `npm run build` passed.
- Browser smoke tests covered invalid input, unresolved ZIP, successful empty
  results, rate limiting, provider unavailability, keyboard operation,
  responsive layout, and both list-to-marker and marker-to-list selection.
- A live configured-key check of ZIP `16802` returned 20 capped nearby matches
  on that date. This is an observation, not a fixed expected count.
- Existing SQLite hotel search, booking, and history screens still opened and
  worked during regression checking.
- No browser console warnings or errors were observed.

Automated tests mock Geoapify and consume no provider quota. Deterministic empty,
rate-limit, and provider-failure browser states were exercised with a temporary
in-memory mock backend, after which the normal live backend was restored.

## Agentic review loop

```text
DESCRIBE -> PREDICT BLAST RADIUS -> PLAN -> IMPLEMENT
                                              |
                                              v
                          INSPECT DIFF -> VERIFY BEHAVIOR
                                              |
                            +-----------------+-----------------+
                            |                                   |
                       matches scope                     mismatch/failure
                            |                                   |
                            v                                   v
                          COMMIT                       CORRECT AND REVERIFY
```

The diff and observed behavior are separate evidence. A passing automated check
does not excuse an unexpected file change, and an in-scope diff does not replace
live verification of the user-visible flow.
