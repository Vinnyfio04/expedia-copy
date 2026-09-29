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
|   |   |-- geocoding.py      Geoapify integration and demo route
|   |   `-- main.py           FastAPI application and startup lifecycle
|   |-- tests/                Backend persistence, API, and provider tests
|   `-- requirements.txt
|-- model/            Model data: seed.sql, ignored expedia.db, and relationship assets
|-- view/             View: Vue screens, browser state, API client, and CSS
|   |-- src/
|   |   |-- components/
|   |   |-- api.js
|   |   |-- App.vue
|   |   `-- style.css
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

### Backend environment configuration

Backend environment settings belong in the project-root `.env` file. The helper at
`controller/app/config.py` loads that file using an explicit path derived from the
helper's location. Restart the backend after editing `.env` so the running process
loads the updated configuration.

`GET /api/health` reports whether the Geoapify API key is configured without
returning its value. Geoapify is not called by the health check.

### ZIP lookup controller contract

`controller/app/geocoding.py` provides the async function
`lookup_us_postcode(postcode)`. It sends a backend-only Geoapify forward-geocoding
request constrained to U.S. postcode results and uses a five-second timeout. The
`GET /api/demo/zip-location` endpoint calls it with the fixed demonstration input
`"16802"`.

On success, the function returns the dedicated `PostcodeLocation` model with the
postcode, uppercase country code, latitude, longitude, and an optional locality.
A response is accepted only when its postcode exactly matches the request, its
country code is U.S., and both coordinates are finite and within valid ranges.

An unresolved or mismatched postcode raises `PostcodeNotFoundError`. Missing
configuration, request failures, and malformed provider responses raise
`GeocodingProviderError` with a sanitized message. The function does not expose
the API key, provider response, request URL, or underlying exception text. The
demo route returns HTTP 404 for an unresolved postcode and HTTP 502 with a
sanitized message when the provider is unavailable. The Vue stays screen includes
a small demonstration panel that calls this route through the existing `/api`
development proxy.

## View setup

In a separate terminal, when you are ready to install dependencies:

```powershell
cd view
npm install
npm run dev
```

Vite will print the local frontend URL, typically `http://localhost:5173`.

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
