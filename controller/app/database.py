"""SQLite persistence and CRUD contracts for application models."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterator

from .models import Booking, Hotel, Trip, User


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
