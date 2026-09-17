"""Tests for the CSV readers and hotel-stay search calculations."""

from datetime import date
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.bookings import cancel_booking, create_booking, list_booking_history, list_bookings
from app.csv_store import DATA_DIRECTORY, read_csv_rows
from app.hotels import list_hotels
from app.models import BookingCreate
from app.search import search_hotel_stays
from app.trips import list_trips
from app.users import list_users


class CsvTableTests(unittest.TestCase):
    def test_reads_all_supplied_tables(self) -> None:
        self.assertEqual(len(list_hotels()), 8)
        self.assertGreaterEqual(len(list_trips()), 12)
        self.assertGreaterEqual(len(list_users()), 6)
        self.assertGreaterEqual(len(list_bookings()), 6)


class HotelSearchTests(unittest.TestCase):
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


class BookingHistoryTests(unittest.TestCase):
    def test_joins_every_booking_to_display_details(self) -> None:
        history = list_booking_history()

        self.assertEqual(len(history), len(list_bookings()))
        self.assertEqual(history[0].booking_id, "B001")
        self.assertEqual(history[0].display_name, "Demo Traveler 1")
        self.assertEqual(history[0].hotel_name, "Harbor Lantern Hotel")
        self.assertEqual(history[0].trip_name, "Boston Harbor Weekend")
        self.assertEqual(history[0].nights, 2)
        self.assertEqual(history[0].stay_price_usd, 300)
        self.assertEqual(
            [booking.status for booking in history[:6]],
            ["confirmed", "cancelled", "confirmed", "confirmed", "confirmed", "cancelled"],
        )


class BookingCreateTests(unittest.TestCase):
    def test_creates_linked_traveler_trip_and_booking_rows(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            temporary_data = Path(temporary_directory)
            for filename in ("hotels.csv", "users.csv", "trips.csv", "bookings.csv"):
                copy2(DATA_DIRECTORY / filename, temporary_data / filename)

            original_counts = {
                filename: len(read_csv_rows(filename))
                for filename in ("users.csv", "trips.csv", "bookings.csv")
            }
            request = BookingCreate(
                hotel_id="H001",
                full_name="CSV Write Test Traveler",
                check_in=date(2027, 1, 10),
                check_out=date(2027, 1, 13),
            )

            with patch("app.csv_store.DATA_DIRECTORY", temporary_data):
                created = create_booking(request, booked_on=date(2026, 9, 16))
                users = read_csv_rows("users.csv")
                trips = read_csv_rows("trips.csv")
                bookings = read_csv_rows("bookings.csv")

            self.assertEqual(created.display_name, "CSV Write Test Traveler")
            self.assertEqual(created.hotel_name, "Harbor Lantern Hotel")
            self.assertEqual(created.nights, 3)
            self.assertEqual(created.stay_price_usd, 450)
            self.assertEqual(len(users), original_counts["users.csv"] + 1)
            self.assertEqual(len(trips), original_counts["trips.csv"] + 1)
            self.assertEqual(len(bookings), original_counts["bookings.csv"] + 1)
            self.assertEqual(users[-1]["user_id"], created.user_id)
            self.assertEqual(trips[-1]["trip_id"], created.trip_id)
            self.assertEqual(bookings[-1]["booking_id"], created.booking_id)
            self.assertEqual(bookings[-1]["booked_on"], "2026-09-16")
            self.assertEqual(bookings[-1]["status"], "confirmed")


class BookingCancelTests(unittest.TestCase):
    def test_updates_status_without_deleting_the_booking(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            temporary_data = Path(temporary_directory)
            for filename in ("hotels.csv", "users.csv", "trips.csv", "bookings.csv"):
                copy2(DATA_DIRECTORY / filename, temporary_data / filename)

            with patch("app.csv_store.DATA_DIRECTORY", temporary_data):
                before = read_csv_rows("bookings.csv")
                updated = cancel_booking("B001")
                after = read_csv_rows("bookings.csv")

            self.assertEqual(len(after), len(before))
            self.assertEqual(updated.booking_id, "B001")
            self.assertEqual(updated.status, "canceled")
            self.assertEqual(after[0]["status"], "canceled")
            self.assertEqual(after[1:], before[1:])


if __name__ == "__main__":
    unittest.main()
