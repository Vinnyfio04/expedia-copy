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
  strict U.S. ZIP, `nearby_hotels.py` owns Geoapify search and rate
  orchestration, `liteapi.py` isolates live-rate normalization and matching,
  `saved_hotels.py` exposes local save, ZIP lookup, and removal routes,
  `gemini.py` owns the backend-only structured-output transport, and
  `hotel_rag.py` coordinates SQL planning, guarded retrieval, grounding, and
  the stateless chatbot route.

`App.vue` coordinates stays, booking, and booking-history screens.
`NearbyHotelSearch.vue` owns ZIP input, local/API result state, saved status,
mutation feedback, and selection, while `HotelMap.vue` owns Leaflet map
creation, markers, popups, view changes, and cleanup. `localHotels.js` isolates
the local-first decision so it can be tested without rendering Vue.
`HotelChat.vue` owns the question, loading, answer, and failure states, while
`hotelChat.js` provides independently tested validation and formatting.

## Current project-file map

Generated output, dependency directories, caches, the ignored `.env`, and the
generated SQLite database are omitted.

```text
assignment1/
|-- AGENTS.md
|-- README.md
|-- assignment_instructions.md
|-- controller/
|   |-- requirements.txt
|   |-- app/
|   |   |-- bookings.py
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- geocoding.py
|   |   |-- gemini.py
|   |   |-- hotels.py
|   |   |-- hotel_rag.py
|   |   |-- liteapi.py
|   |   |-- main.py
|   |   |-- models.py
|   |   |-- nearby_hotels.py
|   |   |-- saved_hotels.py
|   |   |-- search.py
|   |   |-- trips.py
|   |   `-- users.py
|   `-- tests/
|       |-- test_database_api.py
|       |-- test_geocoding.py
|       |-- test_health.py
|       |-- test_gemini.py
|       |-- test_hotel_chat_route.py
|       |-- test_hotel_rag.py
|       |-- test_liteapi.py
|       |-- test_nearby_hotels.py
|       |-- test_rag_models.py
|       `-- test_saved_hotels.py
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
|   |   |-- hotelChat.js
|   |   |-- localHotels.js
|   |   |-- main.js
|   |   |-- navigation.js
|   |   |-- postcode.js
|   |   |-- style.css
|   |   |-- travelLinks.js
|   |   `-- components/
|   |       |-- BookingHistory.vue
|   |       |-- BookingScreen.vue
|   |       |-- HotelChat.vue
|   |       |-- HotelMap.vue
|   |       `-- NearbyHotelSearch.vue
|   `-- tests/
|       |-- api.test.js
|       |-- booking.test.js
|       |-- history.test.js
|       |-- hotelChat.test.js
|       |-- localHotels.test.js
|       |-- navigation.test.js
|       |-- postcode.test.js
|       `-- travelLinks.test.js
|-- docs/
|   |-- design-pipeline.md
|   |-- report.md
|   |-- sqlite-mvc-branch-summary.md
|   `-- images/
|       `-- 10-zip-code-search-mockup.jpg
|-- prompts/
`-- handoffs/
    `-- current.md
```

## Local-first ZIP-to-map flow

```text
User submits a five-character ZIP string
                    |
                    v
NearbyHotelSearch.vue + postcode.js
  require exactly five ASCII digits
  clear stale results and selectedPlaceId
                    |
                    v
view/src/localHotels.js searchHotelsLocalFirst()
                    |
                    v
GET /api/hotels/saved?postcode=... through the Vite proxy
                    |
          +---------+----------+
          |                    |
    saved matches        successful empty
          |                    |
          v                    v
render stored subset    GET /api/hotels/nearby?postcode=...
and demo nights                 |
                               v
                    controller/app/nearby_hotels.py
                      validates and calls lookup_us_postcode()
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

If the local request fails, the View reports that failure and does not call the
provider. The Geoapify key is read only by Python from the ignored project-root
`.env`; the frontend never calls Geoapify directly. A successful empty provider
result still returns the resolved center, allowing the map to display the search
area with no hotel markers.

## Save and remove flow

```text
API result + resolved search center
                |
                v
POST /api/hotels/saved
                |
                v
one SQLite transaction
  insert saved_hotels by unchanged provider ID when missing
  insert saved_hotel_locations association when missing
  insert missing demo nights for 2026-10-10 through 2026-10-14
                |
                v
success response -> Vue marks provider ID saved and disables Add

DELETE /api/hotels/saved?hotel_id=...
                |
                v
one SQLite transaction removes only that hotel's
demo nights -> ZIP associations -> saved hotel
                |
                v
success response -> Vue removes the local card
```

The three Assignment 2 tables are created additively with repeatable schema
statements. `saved_hotels` prevents duplicate provider identities;
`saved_hotel_locations` preserves searched ZIP/map context; and
`demo_hotel_nights` has a composite `(hotel_id, stay_date)` key. The default
10,000-cent rate and 20-room count are simulated classroom values, never API
claims. Repeated saves do not overwrite existing nightly values.

## Saved-hotel SQL-RAG flow

```text
User submits one natural-language question
                    |
                    v
HotelChat.vue validates and POSTs /api/hotels/chat
                    |
                    v
hotel_rag.py sends Gemini only:
  question + relevant schema + strict query rules
                    |
                    v
Gemini returns a typed SQL proposal and interpreted stay intent
                    |
                    v
database.py validates and executes locally
  SELECT/WITH only
  read-only + query-only SQLite connection
  table/column/function authorizer
  parameterized values
  operation, row, SQL-size, value-size, and context bounds
  fixed evidence columns and canonical relationship verification
                    |
                    v
Python derives deterministic facts
  checkout excluded
  one row required for every requested night
  missing nights are never available
  totals exist only for complete stays
                    |
                    v
hotel_rag.py sends Gemini only:
  original question + bounded verified rows + derived facts
                    |
                    v
Gemini returns a typed grounded answer citing retrieved hotel IDs
                    |
                    v
backend compares every cited completeness, availability,
missing-night, and total-cost claim with its derived match
                    |
                    v
Vue renders answer, dates, totals, availability, nights, and data notice
```

Gemini never connects to or directly accesses SQLite. Both model requests are
stateless, backend-only, and schema-constrained. The first request may receive
one correction opportunity containing only a safe validation code. The second
answer cannot cite a hotel outside the retrieved context. The route reads only
`saved_hotels`, `saved_hotel_locations`, and `demo_hotel_nights`; it cannot
change records or make bookings.

The simulated course records cover October 10–14, 2026. For a requested stay,
check-in is included and checkout is excluded. A missing requested night makes
the stay incomplete, prevents a complete-stay total, and cannot be presented as
available.

## Optional live-rate flow

`POST /api/hotels/nearby/rates` accepts a ZIP, check-in, check-out, and adult
count. It preserves the Geoapify list, requests one cheapest USD LiteAPI rate
per hotel for the same center and radius, and attaches only conservative
name/location matches. LiteAPI stay totals are converted to average nightly
rates but are not stored. A missing key or provider failure is represented by
`rates_status`; it does not erase valid nearby place results. The current Vue
screen does not call this optional route.

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

The chatbot route additionally uses `llm_not_configured` with HTTP 503,
`llm_rate_limited` with HTTP 429, and `llm_unavailable` with HTTP 502. Unsafe
model queries and invalid grounded answers return distinct sanitized HTTP 502
errors. Proposed SQL, model payloads, and credentials are never returned to the
View.

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
Additive Assignment 2 schema creation runs independently of the immutable seed,
so it also upgrades an existing Assignment 1 database without changing supplied
records.

## Verification evidence

Verification on 2026-10-08 for the `chatbot-rag-implementation` working tree
produced the following observed results:

- 103 backend `unittest` tests passed.
- 33 frontend `node:test` tests passed.
- `npm run lint` and `npm run build` passed.
- A full-chain route test used a temporary SQLite database and mocked two
  typed Gemini responses to exercise HTTP, SQL validation/execution,
  relationship verification, checkout-exclusive totals, grounding, and JSON.
- A live `gemini-3.5-flash-lite` smoke request completed both model stages with
  the production timeout and returned the expected grounded `no_matches`
  response for the empty real saved-hotel table.
- Adversarial backend tests reject mutations, multiple statements, comments,
  unapproved tables/functions, invalid result shapes, expensive queries,
  oversized context, and cross-hotel relationship mismatches.
- Temporary-database tests covered additive initialization, foreign keys,
  idempotent saves, preservation of edited nightly values, ZIP-scoped reads,
  removal, and reopen persistence.
- Browser and HTTP smoke checks covered the running frontend, Vite proxy,
  backend health, Assignment 1 list, local saved lookup, and configured ZIP
  `16802` provider search. Live chatbot checks displayed a no-saved-match result
  for an unsaved Assignment 1 hotel and an insufficient-data result for saved
  hotels outside the demo-night range. Both kept checkout exclusive and labeled
  all rates and availability as simulated course data.
- Existing SQLite hotel search, booking, and history screens still opened and
  worked during regression checking.

Automated tests mock Geoapify, LiteAPI, and Gemini and consume no provider
quota. Live provider counts and LLM wording are time-dependent observations and
are not test assertions.

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
