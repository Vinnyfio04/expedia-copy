# Add the Assignment 2 saved-hotel schema

Purpose: Extend the existing SQLite database additively for API hotel identity
and fictional daily classroom availability while preserving Assignment 1 and
the frozen Assignment 2 Part 1 behavior.

## Prompt

```text
Read AGENTS.md, README.md, and the existing database code.

I have completed the manual comparison in DB Explorer. Now add the
schema needed to store API hotels and their daily demo rates and
availability.

1. Add a saved_hotels table containing:
   - hotel_id: the API's provider ID, used as the primary key
   - name: nullable when missing from the API
   - address: nullable when missing from the API
   - latitude: required, valid latitude
   - longitude: required, valid longitude

   Map these columns to the existing API response fields. Preserve
   provider IDs exactly and prevent duplicate saved hotels.

2. Add a demo_hotel_nights table containing:
   - hotel_id: foreign key referencing saved_hotels
   - stay_date: date in YYYY-MM-DD format
   - nightly_rate_cents: nonnegative integer, DEFAULT 10000
     ($100.00 per night)
   - rooms_available: nonnegative integer, DEFAULT 20

Note that these rates and room counts are fictional classroom defaults,
not information supplied by the hotel API.

Use (hotel_id, stay_date) as the composite primary key so each hotel
has at most one entry per night. Enforce the foreign-key relationship.

Keep Assignment 1 tables and supplied records unchanged. Preserve the frozen
Assignment 2 Part 1 API, ZIP search, and list/map behavior. Do not add frontend
controls, chatbot features, or dependencies.

Use an additive, repeatable migration that works with the existing database and
a fresh database.

Afterward, show the database file path, summarize the changes. Stop so I can
verify them.
```

## Resulting decisions

- `saved_hotels.hotel_id` stores `NearbyHotel.provider_place_id` unchanged.
- SQL `CHECK` constraints enforce latitude, longitude, rate, and availability
  ranges; the composite night key prevents duplicates.
- Startup uses repeatable `CREATE TABLE IF NOT EXISTS` statements rather than
  changing or replaying `model/seed.sql`.
- Persistence tests use temporary database files and verify both existing and
  fresh initialization plus `PRAGMA foreign_key_check`.

