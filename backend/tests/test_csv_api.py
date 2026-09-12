"""Tests for the CSV readers and hotel-stay search calculations."""

import unittest

from app.bookings import list_bookings
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


if __name__ == "__main__":
    unittest.main()
