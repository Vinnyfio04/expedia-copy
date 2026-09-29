# Current project handoff

Updated: 2026-09-29

## Repository state

- Current branch: `main`
- Current HEAD: `f71c3189afb4973b44258aeec63c3e11ba39fefc`
- Last verified feature commit: `f71c3189afb4973b44258aeec63c3e11ba39fefc`
  (`Implemented fixed data zip code button`)
- `main`, `origin/main`, `codex/geoapify-implementation`, and
  `origin/codex/geoapify-implementation` all pointed to that commit immediately
  before this documentation update.
- The working tree was clean and `main` matched `origin/main` immediately before
  this update. This update is expected to leave only
  `docs/design-pipeline.md`, `prompts/07-geoapify-implementation.md`, and
  `handoffs/current.md` modified or untracked until the user chooses whether to
  commit them.

Repository root:

`C:/Users/Owner/Desktop/School Work/5 Fall 2026/IST 402 - Vibe Coding/assignment1`

## Completed work

- The Vue 3 stays interface loads all hotels and preserves case-insensitive
  hotel-name search through the FastAPI `/api` boundary.
- Booking creation, joined booking history, and retained-record cancellation are
  implemented with the current CSV persistence layer.
- The project-root `.env` is ignored. `controller/app/config.py` loads it through
  an explicit path and treats an absent, empty, or whitespace-only Geoapify key
  as unconfigured.
- `GET /api/health` preserves `{"status": "ok"}` and adds only the Geoapify
  configuration status, never the key.
- `controller/app/geocoding.py` uses `httpx` with a five-second timeout for
  Geoapify forward geocoding. It sends postcode `16802`, `type=postcode`,
  `format=json`, and `filter=countrycode:us` from the backend only.
- Provider results are accepted only for the exact requested U.S. postcode with
  finite coordinates in valid latitude and longitude ranges.
- `GET /api/demo/zip-location` returns the dedicated `PostcodeLocation` model and
  maps unresolved and provider-failure outcomes to distinct, sanitized errors.
- `view/src/components/ZipLookupDemo.vue` provides one fixed ZIP button with
  loading, disabled, success, and backend-error states. It uses
  `view/src/api.js` and the existing Vite `/api` proxy; no key or provider request
  exists in frontend code.
- README and design documentation describe the configuration and route contract.
- Feature commit `f71c318` was pushed, fast-forwarded into `main`, and pushed to
  `origin/main` at the user's direction.

## Unfinished work and intentional scope limits

Assignment Part 2 remains incomplete against
`docs/assignment_instructions.md`:

- Replace CSV runtime persistence with SQLite.
- Seed the supplied hotel, trip, user, and booking data exactly once while
  preserving IDs.
- Move all subsequent reads and writes to SQLite without duplicating starter
  records after restarts.
- Add deletion of a test booking through FastAPI and the Vue frontend.
- Demonstrate create, read, update/cancel, and delete through the browser.
- Verify persisted changes after a browser refresh and full frontend/backend
  restarts.
- Update `docs/report.md` for the final Part 2 submission.

The Geoapify feature is intentionally a fixed demonstration. Arbitrary ZIP
input, maps, hotel creation, and direct browser-to-provider requests were not
requested and should not be added without a new requirement.

## Checks actually run

The following checks were run against the code contained in feature commit
`f71c318`; they are recorded here rather than inferred from configuration files.

Backend:

```powershell
cd controller
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Observed: 19 tests passed. Coverage included CSV reads/search/booking behavior,
blank and configured key states, Geoapify success, mismatched location,
sanitized provider failure, and the demo route's 200/404/502 behavior.

Frontend:

```powershell
cd view
npm run lint
npm test
npm run build
```

Observed: lint passed; 18 Node tests passed; Vite 7.3.6 production build passed
after rerunning it with the filesystem access required by esbuild.

Live verification:

- The frontend returned HTTP 200 at `http://127.0.0.1:5173/`.
- Backend health returned HTTP 200 at `http://127.0.0.1:8000/api/health`.
- A visible-browser click requested `/api/demo/zip-location` and displayed
  postcode `16802`, locality `State College`, latitude `40.803167822`, and
  longitude `-77.861384958`; those values matched the backend JSON.
- Browser resource evidence identified the request as a fetch to
  `http://127.0.0.1:5173/api/demo/zip-location` with no key or query string.
- The backend response contained only `country_code`, `latitude`, `locality`,
  `longitude`, and `postcode` fields.
- An in-memory mocked provider failure displayed `The location provider is
  unavailable.` and cleared the prior result without calling Geoapify. Normal
  backend behavior was restored afterward and the success state was rechecked.
- Hotel search for `Harbor Lantern` still returned the single hotel card
  `Harbor Lantern Hotel`.
- No browser console warnings or errors were observed during the demonstration.

Not directly verified: the literal browser DevTools Network panel was not
available through the in-app browser automation, and the live loading frame was
too brief to capture visually. The request resource, response fields, unit tests,
and success/failure UI states were verified through the available browser and
test interfaces.

During this documentation update, source paths and FastAPI's registered OpenAPI
paths were inspected. Application tests were not rerun because this update
changes documentation only.

## Important files

- `AGENTS.md`: repository rules.
- `README.md`: setup and Geoapify configuration/route contract.
- `docs/assignment_instructions.md`: authoritative Part 1 and Part 2 criteria.
- `docs/design-pipeline.md`: current frontend/backend and request-flow design.
- `controller/app/config.py`: project-root environment loading.
- `controller/app/geocoding.py`: Geoapify controller and demo route.
- `controller/app/bookings.py`: current CSV-backed booking behavior.
- `controller/app/csv_store.py`: current runtime persistence helper.
- `view/src/components/ZipLookupDemo.vue`: ZIP demonstration presentation state.
- `view/src/api.js`: frontend HTTP boundary.
- `prompts/07-geoapify-implementation.md`: reusable feature prompt.

## Next task

Implement Assignment 1 Part 2 persistence: design one-time SQLite seeding, move
the existing hotel/search/booking/history/cancellation paths from CSV runtime
storage to SQLite, and add deletion of a test booking through FastAPI and Vue.
Then run backend tests, frontend lint/tests/build, and a browser CRUD sequence
that proves changes survive both refresh and complete service restarts without
duplicating seed data.

Do not add dependencies, rewrite committed sample data, or perform Git operations
without the user's approval.
