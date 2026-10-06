"""SQLite persistence and CRUD contracts for application models."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator

from .models import (
    Booking,
    DemoHotelNight,
    Hotel,
    PostcodeLocation,
    SaveNearbyHotelRequest,
    SavedHotel,
    SavedHotelLocation,
    SavedHotelSearchResponse,
    SavedNearbyHotel,
    Trip,
    User,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "model"
DATABASE_PATH = DATA_DIRECTORY / "expedia.db"
SEED_SQL_PATH = DATA_DIRECTORY / "seed.sql"
SEED_VERSION = "initial_seed_v1"
LEGACY_SEED_VERSION = "csv_seed_v1"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hotels (
    hotel_id TEXT PRIMARY KEY,
    hotel_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    nightly_rate_usd INTEGER NOT NULL CHECK (nightly_rate_usd >= 0)
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    trip_name TEXT NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    CHECK (check_out > check_in),
    FOREIGN KEY (hotel_id) REFERENCES hotels (hotel_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    trip_id TEXT NOT NULL,
    booked_on TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('confirmed', 'cancelled', 'canceled')
    ),
    FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS saved_hotels (
    hotel_id TEXT NOT NULL PRIMARY KEY,
    name TEXT,
    address TEXT,
    latitude REAL NOT NULL CHECK (
        typeof(latitude) IN ('real', 'integer')
        AND latitude BETWEEN -90.0 AND 90.0
    ),
    longitude REAL NOT NULL CHECK (
        typeof(longitude) IN ('real', 'integer')
        AND longitude BETWEEN -180.0 AND 180.0
    )
);

CREATE TABLE IF NOT EXISTS demo_hotel_nights (
    hotel_id TEXT NOT NULL,
    stay_date TEXT NOT NULL CHECK (
        stay_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND stay_date IS date(stay_date)
    ),
    nightly_rate_cents INTEGER NOT NULL DEFAULT 10000 CHECK (
        typeof(nightly_rate_cents) = 'integer'
        AND nightly_rate_cents >= 0
    ),
    rooms_available INTEGER NOT NULL DEFAULT 20 CHECK (
        typeof(rooms_available) = 'integer'
        AND rooms_available >= 0
    ),
    PRIMARY KEY (hotel_id, stay_date),
    FOREIGN KEY (hotel_id) REFERENCES saved_hotels (hotel_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS saved_hotel_locations (
    hotel_id TEXT NOT NULL,
    postcode TEXT NOT NULL CHECK (
        postcode GLOB '[0-9][0-9][0-9][0-9][0-9]'
    ),
    country_code TEXT NOT NULL CHECK (country_code = 'US'),
    search_latitude REAL NOT NULL CHECK (
        typeof(search_latitude) IN ('real', 'integer')
        AND search_latitude BETWEEN -90.0 AND 90.0
    ),
    search_longitude REAL NOT NULL CHECK (
        typeof(search_longitude) IN ('real', 'integer')
        AND search_longitude BETWEEN -180.0 AND 180.0
    ),
    locality TEXT,
    distance_meters REAL CHECK (
        distance_meters IS NULL
        OR (
            typeof(distance_meters) IN ('real', 'integer')
            AND distance_meters >= 0.0
        )
    ),
    PRIMARY KEY (hotel_id, postcode),
    FOREIGN KEY (hotel_id) REFERENCES saved_hotels (hotel_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saved_hotel_locations_postcode
    ON saved_hotel_locations (postcode, hotel_id);
"""


class DatabaseControllerError(RuntimeError):
    """Base exception for persistence contract failures."""


class DuplicateRecordError(DatabaseControllerError):
    """Raised when a create operation reuses a primary key."""


class ReferencedRecordError(DatabaseControllerError):
    """Raised when a write would violate a model relationship."""


class RecordNotFoundError(DatabaseControllerError, LookupError):
    """Raised when an update or delete target does not exist."""


@dataclass(frozen=True)
class ReferenceViolation:
    """One row returned by SQLite's foreign-key reference check."""

    table: str
    row_id: int | None
    parent_table: str
    foreign_key_index: int


def _translate_integrity_error(error: sqlite3.IntegrityError) -> None:
    message = str(error)
    if "FOREIGN KEY" in message:
        raise ReferencedRecordError(
            "The record references missing data or is still in use."
        ) from error
    if "UNIQUE" in message:
        raise DuplicateRecordError("A record with that identifier already exists.") from error
    raise DatabaseControllerError("The record failed database validation.") from error


class DatabaseController:
    """Open SQLite and exchange validated application model objects."""

    def __init__(
        self,
        database_path: Path,
        seed_path: Path | None = SEED_SQL_PATH,
    ) -> None:
        self.database_path = database_path
        self.seed_path = seed_path

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            self._initialize(connection)
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self, connection: sqlite3.Connection) -> None:
        connection.executescript(SCHEMA_SQL)
        seeded = connection.execute(
            "SELECT key FROM app_metadata WHERE key IN (?, ?)",
            (SEED_VERSION, LEGACY_SEED_VERSION),
        ).fetchone()
        if seeded is not None:
            if seeded[0] == LEGACY_SEED_VERSION:
                connection.execute(
                    "UPDATE app_metadata SET key = ? WHERE key = ?",
                    (SEED_VERSION, LEGACY_SEED_VERSION),
                )
            return
        if self.seed_path is None:
            return

        connection.executescript(self.seed_path.read_text(encoding="utf-8"))

        violations = self._reference_violations(connection)
        if violations:
            raise ReferencedRecordError(
                "The initial database records contain invalid references."
            )

    def initialize(self) -> None:
        """Create the schema and apply the SQLite seed exactly once."""
        with self._connection() as connection:
            if self._reference_violations(connection):
                raise ReferencedRecordError(
                    "The database contains invalid model references."
                )

    def _reference_violations(
        self,
        connection: sqlite3.Connection,
    ) -> list[ReferenceViolation]:
        return [
            ReferenceViolation(
                table=row[0],
                row_id=row[1],
                parent_table=row[2],
                foreign_key_index=row[3],
            )
            for row in connection.execute("PRAGMA foreign_key_check").fetchall()
        ]

    def check_references(self) -> list[ReferenceViolation]:
        """Return every foreign-key violation; an empty list means valid data."""
        with self._connection() as connection:
            return self._reference_violations(connection)

    def _insert_hotel(
        self,
        connection: sqlite3.Connection,
        hotel: Hotel,
    ) -> None:
        connection.execute(
            "INSERT INTO hotels "
            "(hotel_id, hotel_name, city, state, nightly_rate_usd) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                hotel.hotel_id,
                hotel.hotel_name,
                hotel.city,
                hotel.state,
                hotel.nightly_rate_usd,
            ),
        )

    def create_hotel(self, hotel: Hotel) -> Hotel:
        """Persist and return a new hotel."""
        try:
            with self._connection() as connection:
                self._insert_hotel(connection, hotel)
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return hotel

    def get_hotel(self, hotel_id: str) -> Hotel | None:
        """Return one hotel by identifier, or None when it does not exist."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM hotels WHERE hotel_id = ?",
                (hotel_id,),
            ).fetchone()
        return Hotel(**dict(row)) if row is not None else None

    def list_hotels(self) -> list[Hotel]:
        """Return every hotel in identifier order."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM hotels ORDER BY hotel_id"
            ).fetchall()
        return [Hotel(**dict(row)) for row in rows]

    def update_hotel(self, hotel: Hotel) -> Hotel:
        """Replace the mutable fields of an existing hotel."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE hotels SET hotel_name = ?, city = ?, state = ?, "
                    "nightly_rate_usd = ? WHERE hotel_id = ?",
                    (
                        hotel.hotel_name,
                        hotel.city,
                        hotel.state,
                        hotel.nightly_rate_usd,
                        hotel.hotel_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(
                        f"Hotel {hotel.hotel_id} was not found."
                    )
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return hotel

    def delete_hotel(self, hotel_id: str) -> None:
        """Delete an unreferenced hotel."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "DELETE FROM hotels WHERE hotel_id = ?",
                    (hotel_id,),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(f"Hotel {hotel_id} was not found.")
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)

    def _insert_saved_hotel(
        self,
        connection: sqlite3.Connection,
        hotel: SavedHotel,
    ) -> None:
        connection.execute(
            "INSERT INTO saved_hotels "
            "(hotel_id, name, address, latitude, longitude) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                hotel.hotel_id,
                hotel.name,
                hotel.address,
                hotel.latitude,
                hotel.longitude,
            ),
        )

    def create_saved_hotel(self, hotel: SavedHotel) -> SavedHotel:
        """Persist one API hotel without changing its provider identifier."""
        try:
            with self._connection() as connection:
                self._insert_saved_hotel(connection, hotel)
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return hotel

    def get_saved_hotel(self, hotel_id: str) -> SavedHotel | None:
        """Return one saved API hotel by exact provider identifier."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM saved_hotels WHERE hotel_id = ?",
                (hotel_id,),
            ).fetchone()
        return SavedHotel(**dict(row)) if row is not None else None

    def list_saved_hotels(self) -> list[SavedHotel]:
        """Return saved API hotels in provider-identifier order."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM saved_hotels ORDER BY hotel_id"
            ).fetchall()
        return [SavedHotel(**dict(row)) for row in rows]

    def update_saved_hotel(self, hotel: SavedHotel) -> SavedHotel:
        """Update API hotel details without changing its provider identifier."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE saved_hotels SET name = ?, address = ?, "
                    "latitude = ?, longitude = ? WHERE hotel_id = ?",
                    (
                        hotel.name,
                        hotel.address,
                        hotel.latitude,
                        hotel.longitude,
                        hotel.hotel_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(
                        f"Saved hotel {hotel.hotel_id} was not found."
                    )
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return hotel

    def delete_saved_hotel(self, hotel_id: str) -> None:
        """Delete a saved API hotel that has no demo-night references."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "DELETE FROM saved_hotels WHERE hotel_id = ?",
                    (hotel_id,),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(
                        f"Saved hotel {hotel_id} was not found."
                    )
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)

    def _insert_demo_hotel_night(
        self,
        connection: sqlite3.Connection,
        night: DemoHotelNight,
    ) -> None:
        connection.execute(
            "INSERT INTO demo_hotel_nights "
            "(hotel_id, stay_date, nightly_rate_cents, rooms_available) "
            "VALUES (?, ?, ?, ?)",
            (
                night.hotel_id,
                night.stay_date.isoformat(),
                night.nightly_rate_cents,
                night.rooms_available,
            ),
        )

    def create_demo_hotel_night(self, night: DemoHotelNight) -> DemoHotelNight:
        """Persist fictional rate and availability for one saved-hotel night."""
        try:
            with self._connection() as connection:
                self._insert_demo_hotel_night(connection, night)
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return night

    def get_demo_hotel_night(
        self,
        hotel_id: str,
        stay_date: date,
    ) -> DemoHotelNight | None:
        """Return one demo night by its composite identifier."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM demo_hotel_nights "
                "WHERE hotel_id = ? AND stay_date = ?",
                (hotel_id, stay_date.isoformat()),
            ).fetchone()
        return DemoHotelNight(**dict(row)) if row is not None else None

    def list_demo_hotel_nights(
        self,
        hotel_id: str | None = None,
    ) -> list[DemoHotelNight]:
        """Return every demo night, optionally limited to one saved hotel."""
        with self._connection() as connection:
            if hotel_id is None:
                rows = connection.execute(
                    "SELECT * FROM demo_hotel_nights "
                    "ORDER BY hotel_id, stay_date"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM demo_hotel_nights "
                    "WHERE hotel_id = ? ORDER BY stay_date",
                    (hotel_id,),
                ).fetchall()
        return [DemoHotelNight(**dict(row)) for row in rows]

    def update_demo_hotel_night(
        self,
        night: DemoHotelNight,
    ) -> DemoHotelNight:
        """Update fictional values without changing the hotel/date key."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE demo_hotel_nights SET nightly_rate_cents = ?, "
                    "rooms_available = ? WHERE hotel_id = ? AND stay_date = ?",
                    (
                        night.nightly_rate_cents,
                        night.rooms_available,
                        night.hotel_id,
                        night.stay_date.isoformat(),
                    ),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(
                        "Demo hotel night "
                        f"{night.hotel_id}/{night.stay_date.isoformat()} was not found."
                    )
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return night

    def delete_demo_hotel_night(self, hotel_id: str, stay_date: date) -> None:
        """Delete one fictional nightly-rate and availability record."""
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM demo_hotel_nights "
                "WHERE hotel_id = ? AND stay_date = ?",
                (hotel_id, stay_date.isoformat()),
            )
            if cursor.rowcount != 1:
                raise RecordNotFoundError(
                    "Demo hotel night "
                    f"{hotel_id}/{stay_date.isoformat()} was not found."
                )

    def _insert_saved_hotel_location(
        self,
        connection: sqlite3.Connection,
        location: SavedHotelLocation,
    ) -> None:
        connection.execute(
            "INSERT INTO saved_hotel_locations "
            "(hotel_id, postcode, country_code, search_latitude, "
            "search_longitude, locality, distance_meters) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (hotel_id, postcode) DO NOTHING",
            (
                location.hotel_id,
                location.postcode,
                location.country_code,
                location.search_latitude,
                location.search_longitude,
                location.locality,
                location.distance_meters,
            ),
        )

    def save_nearby_hotel(
        self,
        request: SaveNearbyHotelRequest,
        stay_dates: Iterable[date],
    ) -> SavedNearbyHotel:
        """Idempotently save an API hotel, search context, and demo nights."""
        hotel = SavedHotel.from_nearby_hotel(request.hotel)
        location = SavedHotelLocation.from_search(
            request.hotel,
            request.search_location,
        )
        dates = tuple(stay_dates)

        try:
            with self._connection() as connection:
                connection.execute(
                    "INSERT INTO saved_hotels "
                    "(hotel_id, name, address, latitude, longitude) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT (hotel_id) DO NOTHING",
                    (
                        hotel.hotel_id,
                        hotel.name,
                        hotel.address,
                        hotel.latitude,
                        hotel.longitude,
                    ),
                )
                self._insert_saved_hotel_location(connection, location)
                connection.executemany(
                    "INSERT INTO demo_hotel_nights (hotel_id, stay_date) "
                    "VALUES (?, ?) "
                    "ON CONFLICT (hotel_id, stay_date) DO NOTHING",
                    [(hotel.hotel_id, stay_date.isoformat()) for stay_date in dates],
                )
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)

        search = self.get_saved_hotel_search(location.postcode)
        saved = next(
            (
                result
                for result in search.results
                if result.provider_place_id == hotel.hotel_id
            ),
            None,
        )
        if saved is None:
            raise DatabaseControllerError("The saved hotel could not be reloaded.")
        return saved

    def get_saved_hotel_search(self, postcode: str) -> SavedHotelSearchResponse:
        """Return local saved results for one ZIP and all saved provider IDs."""
        with self._connection() as connection:
            hotel_rows = connection.execute(
                "SELECT h.hotel_id, h.name, h.address, h.latitude, h.longitude, "
                "l.postcode, l.country_code, l.search_latitude, "
                "l.search_longitude, l.locality, l.distance_meters "
                "FROM saved_hotel_locations AS l "
                "JOIN saved_hotels AS h ON h.hotel_id = l.hotel_id "
                "WHERE l.postcode = ? ORDER BY h.hotel_id",
                (postcode,),
            ).fetchall()
            saved_hotel_ids = [
                row[0]
                for row in connection.execute(
                    "SELECT hotel_id FROM saved_hotels ORDER BY hotel_id"
                ).fetchall()
            ]

            results: list[SavedNearbyHotel] = []
            for row in hotel_rows:
                nights = [
                    DemoHotelNight(**dict(night_row))
                    for night_row in connection.execute(
                        "SELECT * FROM demo_hotel_nights "
                        "WHERE hotel_id = ? ORDER BY stay_date",
                        (row["hotel_id"],),
                    ).fetchall()
                ]
                results.append(
                    SavedNearbyHotel(
                        provider="geoapify",
                        provider_place_id=row["hotel_id"],
                        name=row["name"],
                        formatted_address=row["address"],
                        latitude=row["latitude"],
                        longitude=row["longitude"],
                        distance_meters=row["distance_meters"],
                        demo_nights=nights,
                    )
                )

        center = None
        if hotel_rows:
            first = hotel_rows[0]
            center = PostcodeLocation(
                postcode=first["postcode"],
                country_code=first["country_code"],
                latitude=first["search_latitude"],
                longitude=first["search_longitude"],
                locality=first["locality"],
            )
        return SavedHotelSearchResponse(
            requested_postcode=postcode,
            center=center,
            count=len(results),
            results=results,
            saved_hotel_ids=saved_hotel_ids,
        )

    def delete_saved_hotel_with_related(self, hotel_id: str) -> None:
        """Atomically delete one saved hotel, its locations, and demo nights."""
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM demo_hotel_nights WHERE hotel_id = ?",
                (hotel_id,),
            )
            connection.execute(
                "DELETE FROM saved_hotel_locations WHERE hotel_id = ?",
                (hotel_id,),
            )
            cursor = connection.execute(
                "DELETE FROM saved_hotels WHERE hotel_id = ?",
                (hotel_id,),
            )
            if cursor.rowcount != 1:
                raise RecordNotFoundError(
                    f"Saved hotel {hotel_id} was not found."
                )

    def _insert_user(
        self,
        connection: sqlite3.Connection,
        user: User,
    ) -> None:
        connection.execute(
            "INSERT INTO users (user_id, display_name) VALUES (?, ?)",
            (user.user_id, user.display_name),
        )

    def create_user(self, user: User) -> User:
        """Persist and return a new user."""
        try:
            with self._connection() as connection:
                self._insert_user(connection, user)
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return user

    def get_user(self, user_id: str) -> User | None:
        """Return one user by identifier, or None when it does not exist."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return User(**dict(row)) if row is not None else None

    def list_users(self) -> list[User]:
        """Return every user in identifier order."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM users ORDER BY user_id"
            ).fetchall()
        return [User(**dict(row)) for row in rows]

    def update_user(self, user: User) -> User:
        """Replace the mutable fields of an existing user."""
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE users SET display_name = ? WHERE user_id = ?",
                (user.display_name, user.user_id),
            )
            if cursor.rowcount != 1:
                raise RecordNotFoundError(f"User {user.user_id} was not found.")
        return user

    def delete_user(self, user_id: str) -> None:
        """Delete an unreferenced user."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "DELETE FROM users WHERE user_id = ?",
                    (user_id,),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(f"User {user_id} was not found.")
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)

    def _insert_trip(
        self,
        connection: sqlite3.Connection,
        trip: Trip,
    ) -> None:
        connection.execute(
            "INSERT INTO trips "
            "(trip_id, hotel_id, trip_name, check_in, check_out) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                trip.trip_id,
                trip.hotel_id,
                trip.trip_name,
                trip.check_in.isoformat(),
                trip.check_out.isoformat(),
            ),
        )

    def create_trip(self, trip: Trip) -> Trip:
        """Persist and return a new trip with a valid hotel reference."""
        try:
            with self._connection() as connection:
                self._insert_trip(connection, trip)
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return trip

    def get_trip(self, trip_id: str) -> Trip | None:
        """Return one trip by identifier, or None when it does not exist."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM trips WHERE trip_id = ?",
                (trip_id,),
            ).fetchone()
        return Trip(**dict(row)) if row is not None else None

    def list_trips(self) -> list[Trip]:
        """Return every trip in identifier order."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM trips ORDER BY trip_id"
            ).fetchall()
        return [Trip(**dict(row)) for row in rows]

    def update_trip(self, trip: Trip) -> Trip:
        """Replace an existing trip while checking its hotel reference."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE trips SET hotel_id = ?, trip_name = ?, check_in = ?, "
                    "check_out = ? WHERE trip_id = ?",
                    (
                        trip.hotel_id,
                        trip.trip_name,
                        trip.check_in.isoformat(),
                        trip.check_out.isoformat(),
                        trip.trip_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(f"Trip {trip.trip_id} was not found.")
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return trip

    def delete_trip(self, trip_id: str) -> None:
        """Delete an unreferenced trip."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "DELETE FROM trips WHERE trip_id = ?",
                    (trip_id,),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(f"Trip {trip_id} was not found.")
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)

    def _insert_booking(
        self,
        connection: sqlite3.Connection,
        booking: Booking,
    ) -> None:
        connection.execute(
            "INSERT INTO bookings "
            "(booking_id, user_id, trip_id, booked_on, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                booking.booking_id,
                booking.user_id,
                booking.trip_id,
                booking.booked_on.isoformat(),
                booking.status,
            ),
        )

    def create_booking(self, booking: Booking) -> Booking:
        """Persist and return a booking with valid user and trip references."""
        try:
            with self._connection() as connection:
                self._insert_booking(connection, booking)
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return booking

    def create_booking_records(
        self,
        *,
        user: User | None,
        trip: Trip | None,
        booking: Booking,
    ) -> Booking:
        """Atomically persist optional related records and one booking."""
        try:
            with self._connection() as connection:
                if user is not None:
                    self._insert_user(connection, user)
                if trip is not None:
                    self._insert_trip(connection, trip)
                self._insert_booking(connection, booking)
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return booking

    def get_booking(self, booking_id: str) -> Booking | None:
        """Return one booking by identifier, or None when it does not exist."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM bookings WHERE booking_id = ?",
                (booking_id,),
            ).fetchone()
        return Booking(**dict(row)) if row is not None else None

    def list_bookings(self) -> list[Booking]:
        """Return every booking in identifier order."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM bookings ORDER BY booking_id"
            ).fetchall()
        return [Booking(**dict(row)) for row in rows]

    def update_booking(self, booking: Booking) -> Booking:
        """Replace an existing booking while checking its references."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "UPDATE bookings SET user_id = ?, trip_id = ?, booked_on = ?, "
                    "status = ? WHERE booking_id = ?",
                    (
                        booking.user_id,
                        booking.trip_id,
                        booking.booked_on.isoformat(),
                        booking.status,
                        booking.booking_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RecordNotFoundError(
                        f"Booking {booking.booking_id} was not found."
                    )
        except sqlite3.IntegrityError as error:
            _translate_integrity_error(error)
        return booking

    def delete_booking(self, booking_id: str) -> None:
        """Delete one booking."""
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM bookings WHERE booking_id = ?",
                (booking_id,),
            )
            if cursor.rowcount != 1:
                raise RecordNotFoundError(f"Booking {booking_id} was not found.")


def get_database_controller() -> DatabaseController:
    """Return the configured database controller for one application operation."""
    return DatabaseController(DATABASE_PATH, SEED_SQL_PATH)
