# expedia-copy Design Pipeline

## Frontend and backend boundary

The Vue frontend owns what the user sees and manipulates. `App.vue` holds the
search input and interface state, submits searches, formats nightly rates, and
renders loading, error, result-count, empty, and table states. `api.js` keeps HTTP
requests and response adaptation separate from the presentation component.

The FastAPI backend owns access to the CSV data, API paths, validation, joining
hotels to trips, and calculations. Its routes return JSON; they do not know how
the Vue interface will display that data. The frontend does not open CSV files or
call Python functions directly.

## Current project-file map

Generated and local dependency directories are intentionally omitted. Every path
shown below exists in the current project, including this document.

```text
assignment1/
|-- .gitignore
|-- AGENTS.md
|-- README.md
|-- backend/
|   |-- requirements.txt
|   |-- app/
|   |   |-- __init__.py
|   |   |-- bookings.py
|   |   |-- csv_store.py
|   |   |-- hotels.py
|   |   |-- main.py
|   |   |-- models.py
|   |   |-- search.py
|   |   |-- trips.py
|   |   `-- users.py
|   `-- tests/
|       |-- __init__.py
|       `-- test_csv_api.py
|-- data/
|   |-- README.md
|   |-- bookings.csv
|   |-- hotels.csv
|   |-- relationships.png
|   |-- relationships.svg
|   |-- trips.csv
|   `-- users.csv
|-- docs/
|   |-- assignment_instructions.md
|   |-- design-pipeline.md
|   |-- report.md
|   `-- images/
|       |-- 01-expedia-original.png
|       |-- 02-interface-skeleton.png
|       |-- 03-data-and-logic.png
|       |-- 04-four-layer-system-map.png
|       `-- relationships.png
`-- frontend/
    |-- index.html
    |-- package-lock.json
    |-- package.json
    |-- vite.config.js
    |-- src/
    |   |-- App.vue
    |   |-- api.js
    |   |-- main.js
    |   `-- style.css
    `-- tests/
        `-- api.test.js
```

## Search request flow

The initial page load uses `fetchHotels()` and `GET /api/hotels`. A submitted
hotel-name search follows this longer path:

```text
User enters a hotel name and submits the Vue form
                         |
                         v
frontend/src/App.vue
  submitSearch() trims the input
  loadHotels() owns loading, success, and error state
                         |
                         v
frontend/src/api.js
  searchHotels() builds the encoded request
                         |
                         v
GET /api/search?hotel_name=...
                         |
                         v
backend/app/main.py
  registered FastAPI search router
                         |
                         v
backend/app/search.py
  FastAPI search_hotels() route validates the request boundary
                         |
                         v
  plain Python search_hotel_stays() calculation function
       |                 |                 |
       v                 v                 v
 list_hotels()       list_trips()      calculate nights and
 hotels.py           trips.py          total stay price
       |                 |
       `--------+--------'
                v
      csv_store.py reads hotels.csv and trips.csv
                |
                v
      SearchResponse and HotelStay models
                |
                v
FastAPI serializes the response as JSON
                |
                v
frontend/src/api.js receives JSON and reduces repeated stays
to unique hotel rows for the current table
                |
                v
frontend/src/App.vue updates reactive state
                |
                v
Result count, no-results message, and HTML table render
```

This separation keeps calculation details in Python and transport details in
`api.js`, while `App.vue` remains focused on interaction and presentation.

## Agentic review loop

```text
DESCRIBE
  State the requested behavior and the acceptance evidence.
     |
     v
PREDICT THE BLAST RADIUS
  Name the files and layers expected to change, plus those that must not change.
     |
     v
PLAN
  Order the smallest implementation and verification steps.
     |
     v
IMPLEMENT
  Make focused edits inside the predicted files.
     |
     v
INSPECT THE GIT DIFF
  Compare the actual changed-file list and content with the predicted radius.
     |
     v
VERIFY BEHAVIOR
  Run the relevant automated checks and exercise the user-visible flow.
     |
     v
Does the diff stay in scope and does behavior match the description?
     | yes                              | no
     v                                  v
COMMIT                           CORRECT THE IMPLEMENTATION
  Preserve the verified          Update the description or plan when
  checkpoint.                    the evidence exposes a wrong assumption,
                                 then inspect and verify again.
                                      |
                                      `-------> INSPECT THE GIT DIFF
```

The loop treats the diff and observed behavior as evidence. A passing check does
not excuse an unexpected file change, and an in-scope diff does not replace
behavior verification. Correction continues until both agree with the original
description, after which the work is ready to commit.
