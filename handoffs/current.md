# Current project handoff

Updated: 2026-09-17

## Current objective and user decisions

The project is an Expedia-inspired local travel application built with Vue 3 and FastAPI. The active feature branch currently supports hotel search, simulated booking creation, booking-history reads, and persistent cancellation in the repository CSV files.

The next project-level objective is to finish Assignment 1 Part 2. The assignment requires all CRUD actions through the frontend, SQLite persistence after one-time seeding, and verification across browser refreshes and full frontend/backend restarts. The current branch is an intermediate CSV-backed implementation: create, read, and cancel/update work, but SQLite migration and deletion of a test booking have not been implemented.

Important product decisions already reflected in the source:

- A hotel listing opens the booking screen without Vue Router; `App.vue` owns the current page and selected hotel.
- The booking screen shows hotel details and nightly rate but not the hotel ID.
- The traveler name is entered in one field, with separate check-in and check-out date controls.
- Confirm creates linked traveler/trip/booking CSV records through FastAPI. The visible success text is exactly `Booking confirmed` and does not expose a booking ID.
- Cancellation retains the booking and writes status `canceled` (one `l`). The frontend also recognizes legacy seeded status `cancelled` (two `l`).
- A canceled booking has a disabled, gray `Cancelled` button.
- The cancellation toast says exactly `Trip has been successfully canceled.`, is fixed at the bottom of the viewport, and disappears after 4 seconds.
- Booking history is reachable from the global navigation and currently assumes access to every booking.
- Do not merge, switch, or push `main` without explicit user direction. The latest requested Git work was committed and pushed on `booking-history`.

## Architecture and important files

### Frontend

- `frontend/src/App.vue`: top-level state-based navigation among stays, booking, and booking history; fetches hotels and stores the selected hotel.
- `frontend/src/api.js`: HTTP boundary for hotel reads, search, booking-history reads, booking creation, and cancellation.
- `frontend/src/components/SearchForm.vue`: hotel-name search input.
- `frontend/src/components/ResultsTable.vue`: search results.
- `frontend/src/components/HotelListings.vue`: all-hotel listing and booking entry point.
- `frontend/src/components/BookingScreen.vue`: booking form, validation feedback, estimated total, POST submission, and confirmation message.
- `frontend/src/components/BookingHistory.vue`: joined booking list, cancellation action, canceled state, loading/error states, and transient notification.
- `frontend/src/booking.js`: booking-form normalization, validation, and total calculations.
- `frontend/src/history.js`: booking-history formatting and cancellation-status compatibility.
- `frontend/src/style.css`: shared stays, booking, history, responsive, and fixed-toast presentation.
- `frontend/tests/api.test.js`, `frontend/tests/booking.test.js`, `frontend/tests/history.test.js`: Node tests for API helpers and pure frontend behavior.
- `frontend/vite.config.js`: Vite development server and `/api` proxy to `http://localhost:8000`.

### Backend and persistence

- `backend/app/main.py`: FastAPI app, CORS configuration, health route, and router registration.
- `backend/app/hotels.py`, `trips.py`, `users.py`: CSV read endpoints.
- `backend/app/search.py`: case-insensitive hotel search and hotel/trip join.
- `backend/app/bookings.py`: booking/history reads, linked CSV booking creation, and retained-record cancellation.
- `backend/app/csv_store.py`: CSV reads, locked multi-file appends with exception rollback, and row updates through a temporary file replacement.
- `backend/app/models.py`: Pydantic response/request models for hotels, trips, users, bookings, searches, booking creation, and joined history.
- `backend/tests/test_csv_api.py`: current backend coverage for reads, search, booking creation, joined history, and cancellation.
- `data/hotels.csv`, `data/trips.csv`, `data/users.csv`, `data/bookings.csv`: committed application data and current persistence layer.

### Project context

- `README.md`: environment setup and basic run/check commands. It does not yet document the newer booking CRUD flow.
- `AGENTS.md`: repository rules; read before editing.
- `docs/assignment_instructions.md`: authoritative local assignment brief, including the unimplemented SQLite and delete requirements.
- `docs/design-pipeline.md`: Part 1 design record; currently stale relative to booking and history work.
- `docs/report.md`: Part 1 report; not yet updated for Part 2.
- `prompts/01-plan-the-implementation.md` through `prompts/06-document-the-design-pipeline.md`: saved Part 1 workflow prompts.
- `docs/verification.md`: required by the reconstruction request but not present in the repository.

## Git state

Repository root:

`C:/Users/Owner/Desktop/School Work/5 Fall 2026/IST 402 - Vibe Coding/assignment1`

State verified immediately before editing this handoff:

- Current branch: `booking-history`
- HEAD: `26b10f1b6bb6577e59be5de94e06d88b17321f40`
- Branch upstream: `origin/booking-history`
- Branch/upstream status: equal at `26b10f1`; no ahead/behind marker was reported.
- Working tree: clean before this handoff edit.
- After this handoff is written, `handoffs/current.md` is expected to be the only modified, unstaged file.

Relevant local and tracking branches from `git branch -vv` and `git branch -r`:

- `booking-history`: `26b10f1`, tracking `origin/booking-history`.
- `booking_screen`: `ebd3ab3`, tracking `origin/booking_screen`.
- `main`: `ebd3ab3`, tracking `origin/main`, locally ahead by one commit.
- `updated_interface`: `f2f6116`, with no upstream shown.
- Local tracking ref `origin/main`: `f2f6116`.
- Remote configured as `origin` for the public GitHub project. No `git fetch` was performed during this reconstruction, so remote-tracking refs are only the locally recorded state.

Recent commits, newest first:

- `26b10f1` — `CRUD operations created and operational...`
- `751f7ea` — `Booking history front end implemented...`
- `ebd3ab3` — `Created UI for booking screen...`
- `f2f6116` — `Updated main UI...`
- `d266232` — `Added docs/design_pipeline.md with a detailed design pipeline, AI role, and manual coding role...`
- `88c7b96` — `Add Part 1 documentation and handoff`
- `9227f05` — `Added basic working expedia with proper frontend and backend connections...`

## Completed work

- Part 1 CSV hotel search and joined stay results were established by `9227f05`; supporting documentation followed in `88c7b96` and `d266232`.
- The reference-inspired primary stays UI was implemented in `f2f6116` (`frontend/src/App.vue`, `HotelListings.vue`, and shared styling).
- The booking screen was implemented in `ebd3ab3` (`BookingScreen.vue`, `booking.js`, tests, API helpers, and styling).
- Booking history frontend/read support was implemented in `751f7ea` (`BookingHistory.vue`, `history.js`, API/backend history support, tests, and styling).
- CSV-backed booking creation and persistent cancellation, plus the final confirmation/toast wording and UI behavior, are committed and pushed in `26b10f1`.
- The current committed data contains 8 hotels, 9 users, 16 trips, and 10 bookings. Booking statuses are 5 `confirmed`, 3 `canceled`, and 2 legacy `cancelled`.
- The requested demonstration traveler exists as `U007`, name `Demo traveler 21457`, connected through `T013` to Harbor Lantern Hotel for 2026-11-21 through 2026-11-28; booking `B007` currently has status `canceled`.

## Incomplete or requested work

Assignment Part 2 is not complete against `docs/assignment_instructions.md`:

- Replace CSV runtime persistence with SQLite.
- Seed hotels, trips, users, and bookings exactly once while preserving existing IDs.
- Route all subsequent reads and writes through SQLite without duplicating starter records after restarts.
- Add deletion of a test booking through the frontend and FastAPI.
- Demonstrate create, read, update/cancel, and delete through the browser.
- Verify persistence after browser refresh and after restarting both services.
- Update `README.md`, `docs/design-pipeline.md`, `docs/report.md`, relevant prompts if needed, and this handoff so they match the final Part 2 commit.
- Review, merge the completed feature branch into `main`, verify the combined app, and push only when the user explicitly authorizes those Git operations.

No application-code change is currently requested beyond this handoff refresh. The next agent should confirm whether the user wants to continue Part 2 on `booking-history` or first review/merge the existing CSV-backed checkpoint.

## Verification performed during this reconstruction

These checks were run fresh on 2026-09-17 without changing dependencies or services.

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Observed: 7 tests ran in 0.188 seconds; all passed (`OK`). Coverage included table reads, case-insensitive search, no-result search, empty-query rejection, joined booking history, linked CSV creation, and cancellation without deletion.

Frontend lint and tests:

```powershell
cd frontend
npm run lint
npm test
```

Observed: lint exited with code 0. Node test runner reported 10 tests, 10 passed, 0 failed, duration 182.8952 ms.

Frontend production build:

```powershell
cd frontend
npm run build
```

Observed: exited with code 0; Vite 7.3.6 transformed 15 modules and completed in 1.18 seconds. Generated `dist/` output is ignored and was not intentionally added to Git.

Live service probes:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
(Invoke-RestMethod http://127.0.0.1:8000/api/bookings/history).Count
$response = Invoke-WebRequest http://127.0.0.1:5173/
$response.StatusCode
```

Observed: backend health returned `{"status":"ok"}`; booking history returned 10 records; the frontend returned HTTP 200 and its HTML contained the `expedia-copy` title.

The source and Git metadata were also inspected with read-only commands including `git rev-parse --show-toplevel`, `git branch --show-current`, `git rev-parse HEAD`, `git status --short --branch`, `git log --oneline --decorate`, `git branch -vv`, `git branch -r`, and `git remote -v`.

## Active services

- A backend responded on `127.0.0.1:8000` during reconstruction.
- A frontend responded on `127.0.0.1:5173` during reconstruction.
- Process command-line inspection with `Get-CimInstance Win32_Process` failed with `Access denied`, so the exact commands used to launch the currently running processes were not independently verified.
- The repository-documented start commands are `uvicorn app.main:app --reload` from `backend/` after activating the virtual environment, and `npm run dev` from `frontend/`.
- The services were not started, stopped, or restarted during this handoff task.

## Known issues, risks, and assumptions

- `docs/verification.md` is missing. Do not infer historical browser results from it.
- `docs/design-pipeline.md`, `docs/report.md`, and parts of `README.md` describe the earlier Part 1 state and are stale relative to the current branch.
- SQLite and delete are explicit Part 2 requirements and are absent. The current CSV implementation must not be represented as complete Part 2 CRUD.
- Backend tests exercise Python functions, not the live HTTP endpoints. Frontend tests exercise API helpers and pure helper functions, not mounted Vue components or full browser interactions.
- Live probes confirm both services responded, but they do not prove a clean-stop/restart persistence cycle or every visual interaction.
- The exact running process commands are unknown because operating-system process inspection was denied.
- No fetch was performed, so the current state of GitHub beyond the local remote-tracking refs still requires verification before a merge or push.
- Status spelling is intentionally mixed for compatibility: new cancellations write `canceled`; historical seed rows may contain `cancelled`.
- Current CSV write locking is process-local. It is suitable for this local checkpoint but is not a substitute for the required SQLite persistence or robust multi-process transactions.
- Current data includes committed demo-created rows through `B010`/`T016`/`U009`, including a long `T016` stay ending 2027-08-30. Treat them as repository data; do not delete or rewrite them without user direction.

## Recommended next action

Ask the user to choose between reviewing/merging the present CSV-backed checkpoint and continuing Part 2 on `booking-history`. The recommended technical path is to continue on the feature branch: design one-time SQLite seeding, move all read/create/update behavior to the database, add test-booking deletion through the API and frontend, then run backend tests, frontend lint/tests/build, and manual CRUD plus restart-persistence checks. Do not merge or push `main` without explicit authorization.

Read these files first:

1. `AGENTS.md`
2. `docs/assignment_instructions.md`
3. `README.md`
4. `backend/app/bookings.py`
5. `backend/app/csv_store.py`
6. `backend/app/models.py`
7. `backend/tests/test_csv_api.py`
8. `frontend/src/App.vue`
9. `frontend/src/api.js`
10. `frontend/src/components/BookingScreen.vue`
11. `frontend/src/components/BookingHistory.vue`
12. `frontend/tests/`

Expected file-level blast radius for finishing Part 2: backend persistence/business-logic modules and backend tests; booking/history API and components plus frontend tests; project documentation. The CSV files should become seed input rather than the runtime datastore. Dependency changes are not authorized unless the user explicitly approves them.

## Evidence classification

Verified facts:

- The branch, commit, local upstream relationships, pre-edit clean status, recent commits, and local remote-tracking refs listed above were read from Git.
- The described routes and UI wording are present in the current source.
- The CSV row counts and demonstration records were read from the current committed data.
- The fresh backend tests, frontend lint/tests/build, and live HTTP probes produced the observed results above.
- `docs/verification.md` is absent.

Claims still requiring verification:

- Whether GitHub changed since the last fetch/push.
- The exact commands and process IDs behind the currently responding services.
- Full browser behavior after a cold restart, including every create/cancel path and toast timing.
- Persistence across stopping and restarting both services.
- Final Part 2 acceptance, which cannot pass until SQLite-backed CRUD and deletion are implemented and demonstrated.
