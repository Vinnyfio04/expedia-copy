# Connect saved hotels to the local-first UI

Purpose: Complete the Assignment 2 Part 2 save, remove, refresh-state, and
local-first search workflow without changing the established Part 1 list/map
contract.

## Prompt

```text
Read AGENTS.md and README.md. Preserve Assignment 1 records and the
frozen Assignment 2 Part 1 API, ZIP search, and list/map behavior.

1. Connect local storage to the backend:
Update backend operations and FastAPI endpoints to save an API hotel
and retrieve saved hotels for a searched ZIP.

Save the hotel in saved_hotels and separately preserve its searched
ZIP/location association. Prevent duplicate hotels by provider ID.

For this demo, create demo_hotel_nights rows for October 10–14, 2026,
using the defaults of 10000 cents ($100.00/night) and 20 available
rooms. Repeated saves must not duplicate rows or overwrite existing
rates and availability. These are simulated classroom values.

2. Add an "Add to Local" button beside each existing hotel result in the
frontend:
Connect it to the saved-hotel backend endpoint. Include the hotel and
the current result's ZIP/location context. Determine saved status by
provider ID using the database, including after a page refresh.

Disable Add for saved hotels and while a save is pending. Show useful
success or failure feedback; mark a hotel saved only after success.
Preserve accessible card and map selection.

3. Add a "Remove from Local" button:
Add a backend delete operation and a "Remove from Local" button for
saved hotels. Unsaved hotels must not offer removal.

Remove the saved hotel, its ZIP associations, and its demo nightly
records together in one transaction. Preserve unrelated records.
Update the interface only after successful removal. Show useful
feedback if removal fails.

4. Make ZIP lookup local-first:
4.1. Request saved hotels for the entered ZIP from our backend.
4.2. If matching saved hotels exist, display those local results using
     the stored ZIP/location context. Show nightly rates and available
     rooms from demo_hotel_nights, with their dates. Label these values
     as simulated classroom data.
4.3. Only when the local request succeeds with no matching hotels,
     call the existing Part 1 hotel-search endpoint. Show an error
     if the local request fails.

Label results as "Saved locally" or "API results." Keep Add/Remove
states accurate. Do not present local saved results as a complete
list of hotels in the area.

5. Check and restart:
Run relevant automated checks using temporary databases for mutation
tests. Restart this project's backend and frontend after checking
process ownership. Preserve unrelated processes.

Show the running URLs and summarize the changes. Stop so I can
manually verify the browser behavior and database records.
```

## Resulting decisions

- `saved_hotel_locations` separates provider identity from searched ZIP/map
  context and uses a composite key to prevent duplicate associations.
- POST is idempotent and inserts only missing demo dates; DELETE removes the
  selected hotel's three related record sets in one transaction.
- The saved lookup returns all saved provider IDs so Add state survives a page
  refresh even when the searched ZIP has no local result rows.
- `view/src/localHotels.js` contains the independently testable local-first
  decision: provider search occurs only after a successful empty local lookup.
- UI state changes only after successful mutations, and existing keyboard/card
  and map-marker selection remains intact.
