# Expedia Lite: SQLite Data

The model layer contains fictional classroom data for a small travel
application. Hotel names, travelers, bookings, and prices are invented. City
names are real; the records do not represent live availability or reservations.

`seed.sql` is the tracked, reviewable initial data source. On first use, the
database controller creates the schema in the ignored `expedia.db` file and
applies the seed in one transaction. After that, SQLite is the source of truth.
Restarting the application does not reapply the seed, restore deleted records,
or overwrite changes.

| Table | One row represents | Initial rows | Primary key |
| --- | --- | ---: | --- |
| `hotels` | One hotel | 8 | `hotel_id` |
| `users` | One demo traveler | 11 | `user_id` |
| `trips` | One offered hotel stay with fixed dates | 18 | `trip_id` |
| `bookings` | One simulated reservation | 12 | `booking_id` |

## Relationships

- `trips.hotel_id` references `hotels.hotel_id`.
- `bookings.user_id` references `users.user_id`.
- `bookings.trip_id` references `trips.trip_id`.

SQLite enables foreign-key enforcement on every application connection. The
database controller also exposes a reference check backed by
`PRAGMA foreign_key_check`.

One record chain connects all four tables:

**`B001` → `U001` + `T001` → `H001`**

`B001` belongs to Demo Traveler 1 (`U001`) for Boston Harbor Weekend (`T001`)
at Harbor Lantern Hotel (`H001`).

## Data contracts

### `hotels`

- `hotel_id`: unique text identifier
- `hotel_name`: fictional display name
- `city`: searchable destination city
- `state`: state or district abbreviation
- `nightly_rate_usd`: nonnegative whole-dollar nightly rate

### `users`

- `user_id`: unique text identifier
- `display_name`: fictional traveler label; not an authentication account

### `trips`

- `trip_id`: unique text identifier
- `hotel_id`: hotel foreign key
- `trip_name`: offered-stay title
- `check_in`: ISO date for the first stay day
- `check_out`: ISO departure date, which must follow check-in

### `bookings`

- `booking_id`: unique text identifier
- `user_id`: traveler foreign key
- `trip_id`: trip foreign key
- `booked_on`: ISO booking date
- `status`: `confirmed`, `cancelled`, or the legacy spelling `canceled`

Cancellation retains the booking row for history. Deletion removes it. New
bookings receive new identifiers; existing identifiers remain stable.

## Environment check

SQLite is provided by Python's standard-library `sqlite3` module and does not
require a separate server. Before changing persistence, use the project virtual
environment to check the Python interpreter and SQLite version, make the
smallest approved change, then verify CRUD, foreign keys, and reopen behavior.
