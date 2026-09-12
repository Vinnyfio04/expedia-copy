# expedia-copy Current Handoff

## Goal and current scope

Part 1 is a local travel-search application. The committed implementation uses a
Vue 3 frontend and a FastAPI backend. The backend reads the supplied CSV files,
joins hotels to trips through `hotel_id`, searches hotel names without case
sensitivity, calculates stay length and estimated price, and returns JSON. The
frontend owns the search controls, request state, result count, messages, rate
formatting, and hotel table.

Part 2 SQLite persistence and booking CRUD have not started.

## Architecture and data flow

- `frontend/src/App.vue` contains the Vue Composition API state and presentation.
  It loads all hotels on mount and submits trimmed hotel-name searches.
- `frontend/src/api.js` contains `fetchHotels()` and `searchHotels()`. It is the
  frontend HTTP boundary and reduces repeated stay results to unique hotel rows.
- `frontend/vite.config.js` proxies `/api` requests to `http://localhost:8000`.
- `backend/app/main.py` creates the FastAPI app and registers hotel, trip, user,
  booking, and search routers.
- `backend/app/search.py` contains the thin `/api/search` route and the plain
  Python `search_hotel_stays()` function. That function joins hotels and trips,
  calculates nights, and calculates `stay_price_usd`.
- `backend/app/hotels.py`, `trips.py`, `users.py`, and `bookings.py` expose
  read-only table endpoints and convert CSV rows to models.
- `backend/app/csv_store.py` reads the UTF-8 CSV files under `data/`.
- `backend/app/models.py` defines the Pydantic response models. FastAPI serializes
  those models to JSON, which `api.js` returns to `App.vue` for rendering.

The full file map and ASCII request flow are in `docs/design-pipeline.md`.

## What is complete

- Read-only FastAPI endpoints exist for `/api/hotels`, `/api/trips`,
  `/api/users`, and `/api/bookings`.
- `/api/search?hotel_name=...` returns matching hotel stays with trip data,
  nights, nightly rate, and estimated stay price.
- Blank hotel names produce a structured `400` response; unknown names produce a
  successful response with no results.
- The Vue interface contains a hotel-name input, Search button, result count,
  loading and error states, a no-results message, and a five-column hotel table.
- Frontend requests are isolated from presentation code in `frontend/src/api.js`.
- Backend behavior tests exist in `backend/tests/test_csv_api.py`.
- Frontend API-adapter tests exist in `frontend/tests/api.test.js`.
- The initial Part 1 project is committed and pushed to GitHub.
- Draft project-context documentation now exists in `docs/design-pipeline.md`,
  `docs/report.md`, and `prompts/`, but these files are not committed.

## Recorded verification evidence

`docs/report.md` records the following manual browser observations:

- Initial load: expected the supplied hotels and labeled table; observed
  `8 hotels found.` and all eight supplied hotel rows.
- Successful search for `Harbor Lantern`: expected Harbor Lantern Hotel;
  observed `1 hotel found.` and row `H001`, Harbor Lantern Hotel, Boston, MA,
  `$150`.
- No-result search for `Not A Real Hotel`: expected no records and a clear
  message; observed `0 hotels found.` and `No hotels match that name.`

The exact frontend verification commands documented in `README.md` are:

```powershell
cd frontend
npm run lint
npm test
npm run build
```

`docs/report.md` records these observed results:

- `npm run lint`: passed.
- `npm test`: two frontend tests passed.
- `npm run build`: passed with Vite.
- Backend: four tests passed.

The repository does not record the exact command used for the backend test run,
so do not cite a specific backend command as historical evidence. The four test
cases are visible in `backend/tests/test_csv_api.py`.

At handoff inspection, no process was listening on port `5173` or `8000`.
`docs/verification.md` does not exist, and no repository screenshots document
the browser checks.

## Git state

- Branch: `main`
- HEAD: `9227f0548bab06e6edc6e9ea814f8a3bedb3d00e`
- Commit: `9227f05 Added basic working expedia...`
- Upstream: `origin/main` at the same commit
- Remote: `origin` -> `https://github.com/Vinnyfio04/expedia-copy.git`
- Other local branches: none

Working-tree changes at handoff creation:

```text
 M README.md
?? docs/design-pipeline.md
?? docs/report.md
?? handoffs/current.md
?? prompts/
```

Nothing is staged. The application code and dependency files have no uncommitted
changes.

## Relevant prompt records

- `prompts/01-plan-the-implementation.md`: plan scope and verification before
  editing.
- `prompts/02-build-the-csv-search-api.md`: implement and test the CSV/FastAPI
  backend.
- `prompts/03-build-the-vue-hotel-search.md`: implement the Vue search and table.
- `prompts/04-review-and-create-the-part1-checkpoint.md`: review, verify, commit,
  and push the Part 1 checkpoint.
- `prompts/05-write-the-part1-report.md`: write the evidence-based report.
- `prompts/06-document-the-design-pipeline.md`: document architecture and the
  agentic review loop.

## In progress, blockers, and limitations

No application implementation is actively in progress and there is no external
blocker. The uncommitted work is documentation-only.

Known limitations and incomplete requirements:

- `docs/verification.md` is missing.
- Verification screenshots have not been captured or committed.
- `docs/report.md` links to the existing Part 1 commit, which does not contain
  the newer design, report, prompt, or handoff files.
- The frontend converts stay results into unique hotel rows and displays only
  hotel columns. It does not display the available stay's trip name, check-in,
  check-out, night count, or estimated stay price required by the assignment.
- Backend tests exercise CSV readers and the plain search function, not live HTTP
  routes. Frontend tests exercise the API adapter, not the rendered Vue component.
- The current backend is CSV-backed and read-only. There is no SQLite database,
  one-time seed process, booking creation, history view, cancellation update, or
  deletion flow.

## Recommended next task

Finish Part 1 compliance before starting SQLite work:

1. Decide the smallest table change that exposes each available stay and its
   dates/calculated values without changing the existing JSON contract.
2. Update the Vue component and its tests, then inspect the Git diff.
3. Run backend tests, frontend lint/tests/build, and the two browser search cases.
4. Capture accessible repository screenshots and create `docs/verification.md`
   with the exact commands and observed results.
5. Update `docs/report.md` and its links so every referenced artifact exists in
   the submitted commit.
6. Review and commit the complete Part 1 evidence while preserving commit
   `9227f0548bab06e6edc6e9ea814f8a3bedb3d00e` in history.

After that checkpoint is complete, create the required Part 2 feature branch and
implement one-time CSV-to-SQLite seeding plus booking CRUD through FastAPI and
Vue.
