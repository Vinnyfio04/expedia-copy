# expedia-copy

`expedia-copy` is a learning project that recreates the core experience of a travel-booking site. The initial goal is to provide a Vue user interface backed by a FastAPI API, then grow the project in small, testable increments.

## Project structure

```text
.
|-- controller/       Controller: FastAPI routes, business logic, and persistence
|   |-- app/
|   |   |-- database.py       SQLite schema, initialization, and CRUD
|   |   |-- models.py         Typed entity and API contracts
|   |   |-- bookings.py       Booking business logic and routes
|   |   |-- hotels.py         Hotel controller and routes
|   |   |-- trips.py          Trip controller and routes
|   |   |-- users.py          User controller and routes
|   |   |-- search.py         Hotel-search business logic and route
|   |   |-- geocoding.py      Strict U.S. ZIP resolution through Geoapify
|   |   |-- nearby_hotels.py  Nearby Places request, normalization, and route
|   |   |-- liteapi.py        Live rate lookup and conservative hotel matching
|   |   |-- saved_hotels.py   Local save, ZIP lookup, and removal routes
|   |   `-- main.py           FastAPI application and startup lifecycle
|   |-- tests/                Backend persistence, API, and provider tests
|   `-- requirements.txt
|-- model/            Model data: seed.sql, ignored expedia.db, and relationship assets
|-- view/             View: Vue screens, browser state, API client, and CSS
|   |-- src/
|   |   |-- components/       Booking, history, ZIP search, and Leaflet map
|   |   |-- api.js            Browser-to-FastAPI JSON boundary
|   |   |-- localHotels.js    Local-first nearby-hotel search coordination
|   |   |-- postcode.js       Pure five-digit ZIP validation
|   |   |-- App.vue           Top-level view coordination
|   |   `-- style.css         All application presentation
|   |-- tests/
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- docs/             Requirements, architecture, reports, and branch summaries
|-- prompts/          Selected implementation and verification prompts
|-- handoffs/         Current project handoff
`-- AGENTS.md          Project rules for coding agents
```

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- npm 10 or newer

## Controller setup

Dependencies are not installed as part of this scaffold. When you are ready to install them:

```powershell
cd controller
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Its interactive documentation will be at `http://localhost:8000/docs`.

### Database persistence

The tracked `model/seed.sql` file contains the initial data. On the first database
operation, `controller/app/database.py` creates `model/expedia.db`, enables
SQLite foreign-key enforcement, creates the Hotel, User, Trip, and Booking
tables, applies the SQL seed, and records that initialization completed. Later
starts use the database without reapplying the seed, so database changes are
not duplicated, overwritten, or restored after deletion.

Python's standard-library `sqlite3` module provides the database driver; no
separate SQLite server or Python package is required. The generated `.db` and
SQLite sidecar files are ignored by Git. The database controller exposes typed
create, read, update, and delete operations and checks references with
`PRAGMA foreign_key_check`.

The Vue application continues to use the existing `/api` JSON contracts and
does not access SQLite or the seed files directly.

Assignment 2 adds two additive persistence tables without changing the original
Hotel, User, Trip, or Booking records. `saved_hotels` maps a Geoapify result's
`provider_place_id`, `name`, `formatted_address`, `latitude`, and `longitude` to
`hotel_id`, `name`, `address`, `latitude`, and `longitude`. `demo_hotel_nights`
stores one fictional classroom rate and room count per saved hotel and ISO date;
its SQL defaults are 10,000 cents ($100.00) and 20 rooms. These values do not
come from Geoapify or LiteAPI. The schema uses repeatable `CREATE TABLE IF NOT
EXISTS` statements, so startup adds the tables to an existing database and also
creates them for a fresh database without replaying the immutable seed.

`saved_hotel_locations` separately associates a saved provider ID with the ZIP,
resolved search center, locality, and result distance where it was found. Its
composite key prevents duplicate hotel/ZIP associations, and its foreign key
keeps every association tied to a saved hotel.

### Backend environment configuration

Backend environment settings belong in the project-root `.env` file. The helper at
`controller/app/config.py` loads that file using an explicit path derived from the
helper's location. Restart the backend after editing `.env` so the running process
loads the updated configuration.

`GET /api/health` reports whether the Geoapify and LiteAPI keys are configured
without returning either value. Neither provider is called by the health check.

### Live nearby-hotel contract

`controller/app/geocoding.py` provides the async function
`lookup_us_postcode(postcode)`. It sends a backend-only Geoapify forward-geocoding
request constrained to U.S. postcode results and uses a five-second timeout.
The live route is:

```text
GET /api/hotels/nearby?postcode=16802
```

On success, the function returns the dedicated `PostcodeLocation` model with the
postcode, uppercase country code, latitude, longitude, and an optional locality.
A response is accepted only when its postcode exactly matches the request, its
country code is U.S., and both coordinates are finite and within valid ranges.

`controller/app/nearby_hotels.py` then requests the Geoapify Places
`accommodation.hotel` category using a hard 5,000-meter circle, proximity bias,
and a limit of 20. It skips malformed features, deduplicates by provider place
ID without changing provider order, and returns the typed
`NearbyHotelSearchResponse` contract. The results are nearby place matches, not
an exhaustive hotel inventory, and do not claim prices, ratings, availability,
or booking support.

Malformed input returns HTTP 400. An unresolved or mismatched ZIP returns HTTP
404 without making a Places request. Provider rate limiting returns HTTP 429;
other configuration, connection, timeout, or invalid-provider-response failures
return HTTP 502. All provider errors are sanitized: responses never include the
API key, credential-bearing URL, raw body, or underlying exception text.

The root `.env` must define `GEOAPIFY_API_KEY` for live nearby-hotel searches:

```dotenv
GEOAPIFY_API_KEY=your_geoapify_key
LITEAPI_API_KEY=your_liteapi_sandbox_key
```

Both keys remain backend-only. Vue calls FastAPI through the Vite `/api` proxy.
Copy `.env.example` to `.env` for the expected variable names, keep the real
values uncommitted, and restart FastAPI after changing them.

### Date-specific nearby hotel rates

The original Geoapify-only route remains unchanged. The rate-enriched route is:

```text
POST /api/hotels/nearby/rates
```

Its JSON body supplies `postcode`, `check_in`, `check_out`, and `adults`.
Geoapify remains responsible for ZIP resolution, the nearby hotel list, distance,
and map coordinates. The Controller sends the same center and 5,000-meter radius
to LiteAPI with one room, USD, U.S. guest nationality, and one cheapest rate per
hotel. It conservatively matches exact normalized hotel names and uses address or
coordinates to reject ambiguous matches.

LiteAPI returns a stay total. The API exposes that total and calculates an
`average_nightly_rate` by dividing it by the number of nights. Rates are live,
date-specific presentation data and are not written to SQLite. Unmatched or
unavailable rates are `null`. A LiteAPI configuration or provider failure does
not remove the Geoapify list or map; the response reports `rates_status` and
continues with unpriced Geoapify results.

### Local saved-hotel demo

The local saved-hotel endpoints are:

```text
GET    /api/hotels/saved?postcode=16802
POST   /api/hotels/saved
DELETE /api/hotels/saved?hotel_id={provider_place_id}
```

The POST body contains one unchanged Geoapify hotel object and the resolved
`search_location` returned by the nearby search. Saving is idempotent by provider
ID. It preserves a separate ZIP/location association and creates fictional demo
night rows for October 10–14, 2026 only when each row is missing. Existing rates
and availability are never overwritten by a repeated save. DELETE removes only
the selected saved hotel, its ZIP associations, and its demo nights in one
transaction.

The stays screen checks the local GET route first. Matching local hotels are
shown with their stored map context and labeled as a saved subset, not a complete
list for the area. Their $100.00 nightly rate and 20-room availability are
explicitly labeled as simulated classroom data. Geoapify is called only after a
successful local response containing no hotels; a failed local lookup does not
fall through to the provider.

## View setup

In a separate terminal, when you are ready to install dependencies:

```powershell
cd view
npm install
npm run dev
```

Vite will print the local frontend URL, typically `http://localhost:5173`.
`npm install` installs the pinned `leaflet` 1.9.4 runtime dependency recorded in
`package.json` and `package-lock.json`; do not install a Vue Leaflet wrapper.

The stays screen provides a five-digit ZIP form, a scrollable list of up to 20
nearby Geoapify matches, and a Leaflet map. One provider place ID synchronizes
list-card and marker selection. A successful search with no matches still shows
the resolved center with no hotel markers. LiteAPI rate enrichment is available
through the backend route but is not displayed by the frontend.

The map uses the OpenStreetMap Standard HTTPS tile URL and visibly displays
`© OpenStreetMap contributors`. Public OpenStreetMap tiles are appropriate for
this low-volume coursework demonstration, are best-effort, and must not be
prefetched, bulk-downloaded, proxied, or served with browser caching disabled.

## View checks

From the `view` directory, run:

```powershell
npm run lint
npm test
npm run build
```

## Project context

- [Design and request pipeline](docs/design-pipeline.md)
- [SQLite MVC branch summary](docs/sqlite-mvc-branch-summary.md)
- [Selected project prompts](prompts/)
- [Current project handoff](handoffs/current.md)
