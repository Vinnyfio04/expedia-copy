# SQLite MVC Branch Summary

## Scope

The `sqlite-implementation` branch replaces runtime CSV storage with a local
SQLite database while preserving the existing Vue-to-FastAPI JSON contracts.
It also records the project's Model-View-Controller boundaries and updates the
documentation and user-facing copy that referred to CSV persistence.

## Implemented MVC structure

- **Model:** `controller/app/models.py` defines typed entities and API schemas.
  `model/seed.sql` is the tracked initial dataset, while the ignored
  `model/expedia.db` becomes the source of truth after its one-time seed.
- **View:** `view/src/` owns Vue components, browser state, API calls, and CSS.
  It exchanges JSON through `/api` and never opens SQLite or seed files.
- **Controller:** `controller/app/` owns FastAPI routes, business logic, and the
  database boundary. Only `database.py` opens SQLite; other controllers call
  its typed CRUD methods.

The principal runtime flow is:

```text
Vue view -> /api JSON -> FastAPI controller -> database controller
                                               |
                                               v
                         ignored model/expedia.db
                         seeded once from model/seed.sql
```

## File-by-file changes

### Repository rules and top-level documentation

- `.gitignore` — Ignores the generated SQLite database and its journal, WAL,
  and shared-memory sidecar files.
- `AGENTS.md` — Defines the Model, View, and Controller responsibilities;
  boundary contracts; database transaction and foreign-key rules; one-time
  seeding; and the persistence verification loop.
- `README.md` — Documents the current folder layout, SQLite initialization and
  persistence behavior, typed CRUD boundary, and links to this branch summary.

### Controller and backend tests

- `controller/app/database.py` *(added)* — Provides the only SQLite connection
  boundary, creates the relational schema, enables foreign keys on every
  connection, applies `seed.sql` once, validates references, and exposes typed
  CRUD operations for hotels, users, trips, and bookings.
- `controller/app/csv_store.py` *(deleted)* — Removes the obsolete generic CSV
  read, append, and update persistence helper.
- `controller/app/bookings.py` — Replaces CSV reads and writes with database
  controller calls; creates related user, trip, and booking records in one
  transaction; and persists cancellation through typed booking updates.
- `controller/app/hotels.py` — Reads typed hotel records through the database
  controller instead of parsing `hotels.csv`.
- `controller/app/main.py` — Adds a FastAPI lifespan hook that initializes and
  validates SQLite before serving requests.
- `controller/app/trips.py` — Reads typed trip records through the database
  controller instead of parsing `trips.csv`.
- `controller/app/users.py` — Reads typed user records through the database
  controller instead of parsing `users.csv`.
- `controller/tests/test_database_api.py` *(added)* — Covers fresh seeding,
  one-time initialization, concurrent initialization, CRUD, foreign-key
  rejection, reopen persistence, API response contracts, search, booking
  creation, history, and cancellation.
- `controller/tests/test_csv_api.py` *(deleted)* — Removes the test suite tied
  to the deleted CSV persistence implementation.

### Model data and documentation

- `model/seed.sql` *(added)* — Defines the initial 8 hotels, 11 users, 18
  trips, and 12 bookings in a transaction and records the seed-version marker.
- `model/hotels.csv` *(deleted)* — Its initial hotel records now live in
  `model/seed.sql`; runtime reads use SQLite.
- `model/users.csv` *(deleted)* — Its initial traveler records now live in
  `model/seed.sql`; runtime reads use SQLite.
- `model/trips.csv` *(deleted)* — Its initial offered-stay records now live in
  `model/seed.sql`; runtime reads use SQLite.
- `model/bookings.csv` *(deleted)* — Its initial booking records now live in
  `model/seed.sql`; runtime reads and writes use SQLite.
- `model/README.md` — Describes the SQLite source-of-truth lifecycle, table
  fields, initial row counts, keys, relationships, cancellation behavior, and
  persistence checks.
- `model/relationships.svg` — Renames the entities from CSV files to SQLite
  tables and updates the displayed row counts to match the SQL seed.

### View

- `view/src/components/BookingScreen.vue` — Updates the booking disclaimer to
  state that confirmation saves records to the local database instead of CSV.

### Project documentation and handoff

- `docs/assignment_instructions.md` — Contains the supplied Assignment 2 brief
  for live ZIP-based hotel search, a synchronized map, and a later persistent
  shortlist. This was a pre-existing user-owned change and was preserved while
  implementing SQLite.
- `docs/design-pipeline.md` — Updates the file map and request diagrams to show
  typed SQLite access, one-time seeding, transactional booking writes, and MVC
  responsibilities.
- `docs/report.md` — Corrects the cancellation expectation so it refers to a
  database update rather than a CSV-file update.
- `docs/sqlite-mvc-branch-summary.md` *(added)* — Records this branch-wide file
  inventory, MVC structure, prompt history, and verification evidence.
- `handoffs/current.md` — Records the active branch, completed SQLite/MVC work,
  current row counts and relationships, verification evidence, important
  files, and the next Assignment 2 task.

## Significant prompts

The files in `prompts/` are retained as an evidence log. They are historical
records, so superseded CSV-era prompts were not rewritten to pretend they were
SQLite instructions.

- `prompts/01-plan-the-implementation.md` — Established the original
  small-step implementation plan and separation between data, FastAPI, and the
  Vue interface. Its CSV and old folder terminology is historical.
- `prompts/02-build-the-csv-search-api.md` — Directed the first CSV-backed
  hotel-search API. SQLite now supersedes its persistence mechanism, but it
  remains evidence of the original implementation path.
- `prompts/03-build-the-vue-hotel-search.md` — Established the Vue-to-FastAPI
  JSON integration and separation of transport from presentation. Those
  boundary decisions still apply.
- `prompts/04-review-and-create-the-part1-checkpoint.md` — Records the review,
  verification, commit, and push workflow used for the Part 1 checkpoint.
- `prompts/05-write-the-part1-report.md` — Records the requested report format
  and evidence expectations for the completed Part 1 work.
- `prompts/06-document-the-design-pipeline.md` — Requested the architecture
  map, request flow, repository file map, and agentic review loop now maintained
  in `docs/design-pipeline.md`.
- `prompts/07-geoapify-implementation.md` — Defines the fixed ZIP `16802`
  Geoapify demonstration, backend-only credential handling, strict response
  validation, and sanitized provider errors. It is the current foundation for
  the next live ZIP-search feature.

## Verification completed

- All 24 backend tests passed.
- All 18 frontend tests passed, along with frontend lint and production build.
- A fresh database seeded exactly 8 hotels, 11 users, 18 trips, and 12
  bookings, returned `ok` from `PRAGMA integrity_check`, and returned no rows
  from `PRAGMA foreign_key_check`.
- Reopening SQLite preserved mutations without duplicating or restoring seed
  records.
- HTTP and browser smoke tests confirmed that the existing search, booking,
  history, cancellation, and fixed ZIP demonstration remained functional.
