# expedia-copy Design Pipeline

## View and controller boundary

The Vue frontend owns page state, user input, loading and error feedback, and
presentation. `App.vue` coordinates the stays, booking, and booking-history
views. Focused components handle booking, history, and the fixed ZIP lookup
demonstration. `api.js` is the frontend HTTP boundary and sends every application
request through the Vite `/api` proxy.

The FastAPI backend owns API paths, validation, SQLite access, joins, booking
calculations and writes, one-time SQL seeding, and the Geoapify integration. The
browser never reads seed or database files, calls Python directly, or receives
the Geoapify key. Backend
configuration is loaded from the ignored project-root `.env` through
`controller/app/config.py`.

## Current project-file map

Generated output, dependency directories, caches, and the ignored `.env` file
are intentionally omitted.

```text
assignment1/
|-- .gitignore
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
|   |   |-- search.py
|   |   |-- trips.py
|   |   `-- users.py
|   `-- tests/
|       |-- test_database_api.py
|       |-- test_geocoding.py
|       `-- test_health.py
|-- model/
|   |-- README.md
|   `-- seed.sql
|-- view/
|   |-- index.html
|   |-- package-lock.json
|   |-- package.json
|   |-- vite.config.js
|   |-- src/
|   |   |-- App.vue
|   |   |-- api.js
|   |   |-- booking.js
|   |   |-- history.js
|   |   |-- main.js
|   |   |-- navigation.js
|   |   |-- style.css
|   |   |-- travelLinks.js
|   |   `-- components/
|   |       |-- BookingHistory.vue
|   |       |-- BookingScreen.vue
|   |       `-- ZipLookupDemo.vue
|   `-- tests/
|       |-- api.test.js
|       |-- booking.test.js
|       |-- history.test.js
|       |-- navigation.test.js
|       `-- travelLinks.test.js
|-- docs/
|   |-- assignment_instructions.md
|   |-- design-pipeline.md
|   |-- report.md
|   |-- sqlite-mvc-branch-summary.md
|   |-- images/
|   `-- video/
|-- prompts/
|   |-- 01-plan-the-implementation.md
|   |-- 02-build-the-csv-search-api.md
|   |-- 03-build-the-vue-hotel-search.md
|   |-- 04-review-and-create-the-part1-checkpoint.md
|   |-- 05-write-the-part1-report.md
|   |-- 06-document-the-design-pipeline.md
|   `-- 07-geoapify-implementation.md
`-- handoffs/
    `-- current.md
```

## Hotel-search request flow

The initial page load uses `fetchHotels()` and `GET /api/hotels`. A submitted
hotel-name search follows this path:

```text
Hotel name submitted in view/src/App.vue
                    |
                    v
view/src/api.js searchHotels()
                    |
                    v
GET /api/search?hotel_name=... through the Vite proxy
                    |
                    v
controller/app/search.py
  search_hotels() handles the HTTP boundary
  search_hotel_stays() owns reusable search calculations
                    |
           +--------+--------+
           v                 v
   hotels.py             trips.py
           |                 |
           +--------+--------+
                    v
 database.py reads typed records from SQLite
 (and applies model/seed.sql only on first use)
                    |
                    v
    SearchResponse and HotelStay models
                    |
                    v
FastAPI JSON -> api.js unique-hotel adaptation
                    |
                    v
App.vue reactive state -> result count and hotel cards
```

This separation leaves transport and presentation in Vue while Python owns
database access, joins, validation, and stay-price calculations.

## Database initialization and persistence flow

```text
FastAPI startup or first database operation
                    |
                    v
controller/app/database.py opens model/expedia.db
  enables PRAGMA foreign_keys = ON
  creates Hotel, User, Trip, and Booking tables when absent
                    |
                    v
Is the seed metadata marker present?
          | yes                         | no
          v                             v
 use stored SQLite state       apply model/seed.sql
                                        |
                                        v
                             run PRAGMA foreign_key_check
                             and record the seed marker
```

The database controller accepts and returns the Pydantic entity models from
`controller/app/models.py`. It exposes CRUD for all four entities and enforces
`hotels -> trips -> bookings` and `users -> bookings` through SQLite foreign
keys. Business controllers use that contract and do not issue SQL themselves.

## Geoapify ZIP demonstration flow

The demonstration is intentionally fixed to ZIP `16802`; there is no ZIP input
form or direct provider request from the browser.

```text
User clicks "Look up ZIP 16802"
                    |
                    v
view/src/components/ZipLookupDemo.vue
  clears the previous result
  owns loading, success, and error state
                    |
                    v
view/src/api.js lookupDemoZip()
                    |
                    v
GET /api/demo/zip-location through view/vite.config.js
                    |
                    v
controller/app/geocoding.py get_demo_zip_location()
                    |
                    v
lookup_us_postcode("16802")
  reads the key through controller/app/config.py
  sends postcode, type=postcode, format=json,
  and filter=countrycode:us to Geoapify with a finite timeout
                    |
                    v
accept only an exact U.S. postcode match with valid coordinates
                    |
                    v
PostcodeLocation JSON: postcode, country code,
latitude, longitude, and optional locality
                    |
                    v
ZipLookupDemo.vue renders fields or a sanitized backend error
```

The API key is used only in the backend-to-Geoapify request. The health endpoint
reports only whether it is configured. The demo route distinguishes an
unresolved postcode from a failed provider request and never returns provider
request details, raw exception text, or credentials.

## Booking and history flows

Selecting a hotel changes `App.vue` state to show `BookingScreen.vue`. Booking
submission uses `POST /api/bookings`; Python validates the request and writes
linked user, trip, and booking rows in one SQLite transaction. The history view calls
`GET /api/bookings/history`, joins the database records, and renders them through
`BookingHistory.vue`. Cancellation uses
`PATCH /api/bookings/{booking_id}/cancel` and retains the booking record with an
updated status.

These flows are SQLite-backed. `model/seed.sql` is applied only to a new
database and is not used by normal application operations.

## Agentic review loop

```text
DESCRIBE
  State the requested behavior and acceptance evidence.
     |
     v
PREDICT THE BLAST RADIUS
  Name expected files and protected layers.
     |
     v
PLAN -> IMPLEMENT -> INSPECT THE DIFF -> VERIFY BEHAVIOR
                                         |
                         +---------------+---------------+
                         |                               |
                    matches scope                   mismatch/failure
                         |                               |
                         v                               v
                       COMMIT                    CORRECT AND REVERIFY
```

The diff and observed behavior are separate evidence. A passing automated check
does not excuse an unexpected file change, and an in-scope diff does not replace
live verification of the user-visible flow.
