"""Tests for the CSV readers and hotel-stay search calculations."""

import unittest

from app.bookings import list_booking_history, list_bookings
from app.hotels import list_hotels
from app.search import search_hotel_stays
from app.trips import list_trips
from app.users import list_users


class CsvTableTests(unittest.TestCase):
    def test_reads_all_supplied_tables(self) -> None:
        self.assertEqual(len(list_hotels()), 8)
        self.assertEqual(len(list_trips()), 12)
        self.assertEqual(len(list_users()), 6)
        self.assertEqual(len(list_bookings()), 6)


class HotelSearchTests(unittest.TestCase):
    def test_search_is_case_insensitive_and_calculates_prices(self) -> None:
        response = search_hotel_stays("harbor lantern")

        self.assertEqual(response.count, 2)
        self.assertEqual(
            [stay.trip_id for stay in response.results],
            ["T001", "T009"],
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

        self.assertEqual(len(history), 6)
        self.assertEqual(history[0].booking_id, "B001")
        self.assertEqual(history[0].display_name, "Demo Traveler 1")
        self.assertEqual(history[0].hotel_name, "Harbor Lantern Hotel")
        self.assertEqual(history[0].trip_name, "Boston Harbor Weekend")
        self.assertEqual(history[0].nights, 2)
        self.assertEqual(history[0].stay_price_usd, 300)
        self.assertEqual(
            [booking.status for booking in history],
            ["confirmed", "cancelled", "confirmed", "confirmed", "confirmed", "cancelled"],
        )


if __name__ == "__main__":
    unittest.main()
