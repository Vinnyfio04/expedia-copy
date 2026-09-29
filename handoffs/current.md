# Current project handoff

Updated: 2026-09-29

## Repository state

- Current branch: `sqlite-implementation`
- The SQLite/MVC migration is present as uncommitted working-tree changes.
- `docs/assignment_instructions.md` contains a pre-existing user change that
  must remain separate from persistence work.
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

## Next task

Continue Assignment 2 Part 1 on its feature branch: replace the fixed ZIP
button with validated five-digit ZIP input, fetch nearby Geoapify hotel places
through FastAPI, and synchronize the result list with a Leaflet map. Keep the
SQLite work isolated from that feature until it is reviewed and integrated.
