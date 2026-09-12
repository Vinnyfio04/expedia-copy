# Build the CSV search API

Purpose: Implement the Part 1 backend boundary and calculation logic without
changing the frontend.

## Prompt

```text
Implement only the Part 1 CSV-backed search API for expedia-copy. Read the
current repository instructions and data guide before editing.

Create readable FastAPI modules for hotels, trips, users, and bookings. Provide
read-only JSON endpoints for all four tables. Add a hotel-name search endpoint
that joins hotels.csv to trips.csv through hotel_id, matches partial hotel names
without case sensitivity, calculates each stay's number of nights and estimated
price, and returns a structured response. Reject blank searches with a clear
structured error and return an empty result list for an unknown hotel.

Keep routes thin and put reusable CSV and calculation behavior in typed Python
functions under backend/app/. Add backend tests for source row counts, successful
search, calculations, empty results, and blank input. Do not change frontend
files or add dependencies. Start the backend only if verification requires it,
and stop only a process you start. Report changed paths, example requests,
example JSON, and verification results.
```
