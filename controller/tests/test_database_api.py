"""Tests for SQLite CRUD, relationships, and business calculations."""

from datetime import date
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import httpx

from app.bookings import cancel_booking, create_booking, list_booking_history, list_bookings
from app.database import (
    DatabaseController,
    DuplicateRecordError,
    ReferencedRecordError,
    get_database_controller,
)
from app.hotels import list_hotels
from app.main import app
from app.models import (
    Booking,
    BookingCreate,
    DemoHotelNight,
    Hotel,
    NearbyHotel,
    SavedHotel,
    Trip,
    User,
)
from app.search import search_hotel_stays
from app.trips import list_trips
from app.users import list_users


class TemporaryApplicationDatabaseTestCase(unittest.TestCase):
    """Point application controllers at one isolated seeded database."""

    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "expedia.db"
        self.database_path_patcher = patch(
            "app.database.DATABASE_PATH",
            self.database_path,
        )
        self.database_path_patcher.start()

    def tearDown(self) -> None:
        self.database_path_patcher.stop()
        self.temporary_directory.cleanup()


class DatabaseSeedTests(TemporaryApplicationDatabaseTestCase):
    def test_seeds_supplied_tables_and_validates_references(self) -> None:
        self.assertEqual(len(list_hotels()), 8)
        self.assertGreaterEqual(len(list_trips()), 12)
        self.assertGreaterEqual(len(list_users()), 6)
        self.assertGreaterEqual(len(list_bookings()), 6)
        self.assertEqual(get_database_controller().list_saved_hotels(), [])
        self.assertEqual(get_database_controller().list_demo_hotel_nights(), [])
        self.assertEqual(get_database_controller().check_references(), [])

    def test_does_not_restore_a_deleted_seed_record(self) -> None:
        database = get_database_controller()
        database.delete_booking("B001")

        reopened_database = get_database_controller()
        reopened_database.initialize()

        self.assertIsNone(reopened_database.get_booking("B001"))

    def test_concurrent_initialization_is_safe(self) -> None:
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda _index: get_database_controller().initialize(), range(4)))

        self.assertEqual(len(list_hotels()), 8)
        self.assertEqual(get_database_controller().check_references(), [])


class DatabaseCrudTests(unittest.TestCase):
    def test_crud_contracts_and_foreign_keys_for_every_model(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "crud.db"
            database = DatabaseController(database_path, seed_path=None)
            hotel = Hotel(
                hotel_id="H900",
                hotel_name="Contract Hotel",
                city="Test City",
                state="PA",
                nightly_rate_usd=125,
            )
            user = User(user_id="U900", display_name="Contract Traveler")
            trip = Trip(
                trip_id="T900",
                hotel_id=hotel.hotel_id,
                trip_name="Contract Stay",
                check_in=date(2026, 10, 10),
                check_out=date(2026, 10, 12),
            )
            booking = Booking(
                booking_id="B900",
                user_id=user.user_id,
                trip_id=trip.trip_id,
                booked_on=date(2026, 9, 29),
                status="confirmed",
            )

            self.assertEqual(database.create_hotel(hotel), hotel)
            self.assertEqual(database.create_user(user), user)
            self.assertEqual(database.create_trip(trip), trip)
            self.assertEqual(database.create_booking(booking), booking)
            self.assertEqual(database.get_hotel(hotel.hotel_id), hotel)
            self.assertEqual(database.get_user(user.user_id), user)
            self.assertEqual(database.get_trip(trip.trip_id), trip)
            self.assertEqual(database.get_booking(booking.booking_id), booking)

            updated_hotel = Hotel(
                hotel_id=hotel.hotel_id,
                hotel_name="Updated Contract Hotel",
                city=hotel.city,
                state=hotel.state,
                nightly_rate_usd=150,
            )
            updated_user = User(user_id=user.user_id, display_name="Updated Traveler")
            updated_trip = Trip(
                trip_id=trip.trip_id,
                hotel_id=hotel.hotel_id,
                trip_name="Updated Contract Stay",
                check_in=trip.check_in,
                check_out=trip.check_out,
            )
            updated_booking = Booking(
                booking_id=booking.booking_id,
                user_id=user.user_id,
                trip_id=trip.trip_id,
                booked_on=booking.booked_on,
                status="canceled",
            )

            self.assertEqual(database.update_hotel(updated_hotel), updated_hotel)
            self.assertEqual(database.update_user(updated_user), updated_user)
            self.assertEqual(database.update_trip(updated_trip), updated_trip)
            self.assertEqual(database.update_booking(updated_booking), updated_booking)
            self.assertEqual(database.list_hotels(), [updated_hotel])
            self.assertEqual(database.list_users(), [updated_user])
            self.assertEqual(database.list_trips(), [updated_trip])
            self.assertEqual(database.list_bookings(), [updated_booking])
            self.assertEqual(database.check_references(), [])

            with self.assertRaises(ReferencedRecordError):
                database.delete_hotel(hotel.hotel_id)

            database.delete_booking(booking.booking_id)
            database.delete_trip(trip.trip_id)
            database.delete_user(user.user_id)
            database.delete_hotel(hotel.hotel_id)
            self.assertIsNone(database.get_booking(booking.booking_id))
            self.assertIsNone(database.get_trip(trip.trip_id))
            self.assertIsNone(database.get_user(user.user_id))
            self.assertIsNone(database.get_hotel(hotel.hotel_id))

    def test_rejects_a_missing_foreign_key(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database = DatabaseController(
                Path(temporary_directory) / "references.db",
                seed_path=None,
            )
            invalid_trip = Trip(
                trip_id="T901",
                hotel_id="H404",
                trip_name="Missing Hotel",
                check_in=date(2026, 10, 10),
                check_out=date(2026, 10, 12),
            )

            with self.assertRaises(ReferencedRecordError):
                database.create_trip(invalid_trip)


class SavedHotelPersistenceTests(unittest.TestCase):
    def test_maps_api_hotel_and_enforces_demo_night_relationships(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "saved-hotels.db"
            database = DatabaseController(database_path, seed_path=None)
            api_hotel = NearbyHotel(
                provider="geoapify",
                provider_place_id="geo:Case-Sensitive/001",
                name=None,
                formatted_address=None,
                latitude=40.7982,
                longitude=-77.8599,
            )
            saved_hotel = SavedHotel.from_nearby_hotel(api_hotel)
            night = DemoHotelNight(
                hotel_id=saved_hotel.hotel_id,
                stay_date=date(2026, 11, 10),
            )

            self.assertEqual(saved_hotel.hotel_id, api_hotel.provider_place_id)
            self.assertIsNone(saved_hotel.name)
            self.assertIsNone(saved_hotel.address)
            self.assertEqual(database.create_saved_hotel(saved_hotel), saved_hotel)
            self.assertEqual(database.create_demo_hotel_night(night), night)
            self.assertEqual(night.nightly_rate_cents, 10_000)
            self.assertEqual(night.rooms_available, 20)

            with self.assertRaises(DuplicateRecordError):
                database.create_saved_hotel(saved_hotel)
            with self.assertRaises(DuplicateRecordError):
                database.create_demo_hotel_night(night)
            with self.assertRaises(ReferencedRecordError):
                database.create_demo_hotel_night(
                    DemoHotelNight(
                        hotel_id="missing-provider-id",
                        stay_date=date(2026, 11, 11),
                    )
                )

            updated_hotel = saved_hotel.model_copy(
                update={"name": "Classroom Hotel", "address": "1 Demo Way"}
            )
            updated_night = night.model_copy(
                update={"nightly_rate_cents": 12_500, "rooms_available": 7}
            )
            self.assertEqual(
                database.update_saved_hotel(updated_hotel),
                updated_hotel,
            )
            self.assertEqual(
                database.update_demo_hotel_night(updated_night),
                updated_night,
            )

            reopened = DatabaseController(database_path, seed_path=None)
            reopened.initialize()
            self.assertEqual(reopened.get_saved_hotel(saved_hotel.hotel_id), updated_hotel)
            self.assertEqual(
                reopened.get_demo_hotel_night(night.hotel_id, night.stay_date),
                updated_night,
            )
            self.assertEqual(reopened.list_saved_hotels(), [updated_hotel])
            self.assertEqual(reopened.list_demo_hotel_nights(), [updated_night])
            self.assertEqual(reopened.check_references(), [])

            with self.assertRaises(ReferencedRecordError):
                reopened.delete_saved_hotel(saved_hotel.hotel_id)
            reopened.delete_demo_hotel_night(night.hotel_id, night.stay_date)
            reopened.delete_saved_hotel(saved_hotel.hotel_id)
            self.assertEqual(reopened.list_demo_hotel_nights(), [])
            self.assertEqual(reopened.list_saved_hotels(), [])

    def test_schema_is_repeatable_and_enforces_defaults_and_checks(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database = DatabaseController(
                Path(temporary_directory) / "schema.db",
                seed_path=None,
            )
            database.initialize()
            database.initialize()

            with database._connection() as connection:
                columns = {
                    row["name"]: row
                    for row in connection.execute(
                        "PRAGMA table_info(demo_hotel_nights)"
                    ).fetchall()
                }
                primary_key = [
                    row["name"]
                    for row in sorted(columns.values(), key=lambda row: row["pk"])
                    if row["pk"]
                ]
                foreign_keys = connection.execute(
                    "PRAGMA foreign_key_list(demo_hotel_nights)"
                ).fetchall()

            self.assertEqual(columns["nightly_rate_cents"]["dflt_value"], "10000")
            self.assertEqual(columns["rooms_available"]["dflt_value"], "20")
            self.assertEqual(primary_key, ["hotel_id", "stay_date"])
            self.assertTrue(
                any(
                    row["table"] == "saved_hotels"
                    and row["from"] == "hotel_id"
                    and row["to"] == "hotel_id"
                    for row in foreign_keys
                )
            )

            with self.assertRaises(sqlite3.IntegrityError):
                with database._connection() as connection:
                    connection.execute(
                        "INSERT INTO saved_hotels "
                        "(hotel_id, latitude, longitude) VALUES (?, ?, ?)",
                        ("invalid-latitude", 91.0, 0.0),
                    )

            database.create_saved_hotel(
                SavedHotel(
                    hotel_id="valid-provider-id",
                    latitude=40.8,
                    longitude=-77.86,
                )
            )
            with self.assertRaises(sqlite3.IntegrityError):
                with database._connection() as connection:
                    connection.execute(
                        "INSERT INTO demo_hotel_nights "
                        "(hotel_id, stay_date) VALUES (?, ?)",
                        ("valid-provider-id", "2026-2-3"),
                    )
            with self.assertRaises(sqlite3.IntegrityError):
                with database._connection() as connection:
                    connection.execute(
                        "INSERT INTO demo_hotel_nights "
                        "(hotel_id, stay_date, nightly_rate_cents, rooms_available) "
                        "VALUES (?, ?, ?, ?)",
                        ("valid-provider-id", "2026-11-10", -1, 20),
                    )


class DatabaseApiContractTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path_patcher = patch(
            "app.database.DATABASE_PATH",
            Path(self.temporary_directory.name) / "api.db",
        )
        self.database_path_patcher.start()

    def tearDown(self) -> None:
        self.database_path_patcher.stop()
        self.temporary_directory.cleanup()

    async def test_view_json_contract_survives_database_migration(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            hotels_response = await client.get("/api/hotels")
            create_response = await client.post(
                "/api/bookings",
                json={
                    "hotel_id": "H001",
                    "full_name": "API Contract Traveler",
                    "check_in": "2027-02-10",
                    "check_out": "2027-02-12",
                },
            )
            booking_id = create_response.json()["booking_id"]
            cancel_response = await client.patch(
                f"/api/bookings/{booking_id}/cancel"
            )

        self.assertEqual(hotels_response.status_code, 200)
        self.assertEqual(
            set(hotels_response.json()[0]),
            {"hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"},
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.json()["status"], "confirmed")
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.json()["status"], "canceled")


class HotelSearchTests(TemporaryApplicationDatabaseTestCase):
    def test_search_is_case_insensitive_and_calculates_prices(self) -> None:
        response = search_hotel_stays("harbor lantern")

        self.assertEqual(response.count, 3)
        self.assertEqual(
            [stay.trip_id for stay in response.results],
            ["T001", "T009", "T013"],
        )
        self.assertEqual(response.results[0].nights, 2)
        self.assertEqual(response.results[0].stay_price_usd, 300)

    def test_unknown_hotel_returns_empty_results(self) -> None:
        response = search_hotel_stays("Not A Real Hotel")

        self.assertEqual(response.count, 0)
        self.assertEqual(response.results, [])

    def test_empty_hotel_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            search_hotel_stays("   ")


class BookingHistoryTests(TemporaryApplicationDatabaseTestCase):
    def test_joins_every_booking_to_display_details(self) -> None:
        history = list_booking_history()

        self.assertEqual(len(history), len(list_bookings()))
        self.assertEqual(history[0].booking_id, "B001")
        self.assertEqual(history[0].display_name, "Demo Traveler 1")
        self.assertEqual(history[0].hotel_name, "Harbor Lantern Hotel")
        self.assertEqual(history[0].trip_name, "Boston Harbor Weekend")
        self.assertEqual(history[0].nights, 2)
        self.assertEqual(history[0].stay_price_usd, 300)


class BookingCreateTests(TemporaryApplicationDatabaseTestCase):
    def test_creates_linked_traveler_trip_and_booking_rows(self) -> None:
        original_counts = (
            len(list_users()),
            len(list_trips()),
            len(list_bookings()),
        )
        request = BookingCreate(
            hotel_id="H001",
            full_name="Database Test Traveler",
            check_in=date(2027, 1, 10),
            check_out=date(2027, 1, 13),
        )

        created = create_booking(request, booked_on=date(2026, 9, 16))

        self.assertEqual(created.display_name, "Database Test Traveler")
        self.assertEqual(created.hotel_name, "Harbor Lantern Hotel")
        self.assertEqual(created.nights, 3)
        self.assertEqual(created.stay_price_usd, 450)
        self.assertEqual(len(list_users()), original_counts[0] + 1)
        self.assertEqual(len(list_trips()), original_counts[1] + 1)
        self.assertEqual(len(list_bookings()), original_counts[2] + 1)
        self.assertEqual(
            get_database_controller().get_booking(created.booking_id).booked_on,
            date(2026, 9, 16),
        )


class BookingCancelTests(TemporaryApplicationDatabaseTestCase):
    def test_updates_status_without_deleting_the_booking(self) -> None:
        before = list_bookings()

        updated = cancel_booking("B001")
        after = list_bookings()

        self.assertEqual(len(after), len(before))
        self.assertEqual(updated.booking_id, "B001")
        self.assertEqual(updated.status, "canceled")
        self.assertEqual(after[0].status, "canceled")
        self.assertEqual(after[1:], before[1:])


if __name__ == "__main__":
    unittest.main()
