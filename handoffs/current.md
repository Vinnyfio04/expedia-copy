# Current project handoff

Updated: 2026-10-08

## Repository state

- Active branch at this handoff: `chatbot-rag-implementation`.
- `main`, `assignment2_part2_in_class`, and `origin/main` currently point to
  commit `51fc10f` (`feat: add saved hotels and rate lookup`).
- The Assignment 2 Part 1 ZIP/list/map behavior and the Assignment 2 Part 2
  local saved-hotel workflow are implemented and committed.
- The stateless saved-hotel SQL-RAG chatbot is implemented in the current
  uncommitted working tree. It uses backend-only Gemini structured output,
  guarded read-only SQLite retrieval, deterministic stay calculations, a
  second grounded answer request, and a fixed Vue chat window that leaves the
  ZIP search unchanged.
- Existing documentation work and the chatbot implementation are uncommitted.
- Generated `model/expedia.db`, SQLite sidecars, frontend build output,
  dependency directories, local environments, and `.env` secrets remain
  ignored.

## Current user-visible behavior

The stays screen now has a fixed Hotel AI launcher in the lower-right corner.
It opens a stateless chat window and keeps submitted questions and answers in a
local on-screen log. It displays loading, grounded answer, no-match,
insufficient-data, and sanitized failure states. Matching records show saved
hotel context, interpreted dates, checkout-exclusive totals, whole-stay
availability, nightly evidence, missing dates, and a clear
simulated-course-data notice. The chatbot cannot change records or make
bookings.

The stays screen accepts exactly five ASCII digits. A search now follows this
local-first sequence:

1. Vue requests `GET /api/hotels/saved?postcode={postcode}`.
2. If saved matches exist, it renders that saved subset with the stored search
   center, hotel markers, and demo nights. It does not call Geoapify.
3. If the local request succeeds with zero matches, Vue calls the existing
   `GET /api/hotels/nearby?postcode={postcode}` Part 1 route.
4. If local storage fails, the screen reports the failure and does not silently
   fall through to the provider.

Results are labeled `Saved locally` or `API results`. Local results explicitly
state that they are a saved subset rather than a complete list for the area.
The existing `selectedPlaceId` behavior continues to synchronize accessible
hotel cards and Leaflet markers in both directions.

API results expose `Add to Local`. The button is disabled while its request is
pending and after the provider ID is known to be saved. Saved results expose
`Remove from Local`; the UI changes only after a successful response. Success
and failure feedback is announced without marking an operation complete early.

When the last local result is removed, the empty saved state remains visible.
Searching that ZIP again performs a fresh local lookup and then falls through
to API results because no local matches remain.

## Persistence added for Assignment 2 Part 2

Startup applies additive, repeatable `CREATE TABLE IF NOT EXISTS` statements to
both existing and fresh databases. The immutable Assignment 1 seed is still
applied only once and the original Hotel, User, Trip, and Booking records and
relationships are unchanged.

- `saved_hotels` uses the external provider's `provider_place_id` unchanged as
  `hotel_id`, preventing duplicate saved hotels. Name and address are nullable;
  valid latitude and longitude are required.
- `saved_hotel_locations` records the ZIP, resolved center, locality, and result
  distance separately from the hotel so one provider hotel may retain multiple
  searched-location associations.
- `demo_hotel_nights` uses `(hotel_id, stay_date)` as its composite primary key
  and references `saved_hotels`. Rate and availability are nonnegative and
  default to 10,000 cents and 20 rooms.

Saving is transactional and idempotent. It inserts missing demo nights for
October 10–14, 2026 without duplicating rows or overwriting a previously edited
rate or room count. Removing a hotel deletes only that hotel's demo nights, ZIP
associations, and saved row in one transaction.

These nightly values are fictional classroom defaults. They are not Geoapify
or LiteAPI data and the UI labels them as simulated classroom data.

## Current backend contracts

### Nearby Part 1 search

```text
GET /api/hotels/nearby?postcode=16802
```

Geoapify resolves an exact U.S. ZIP and returns up to 20
`accommodation.hotel` matches inside a hard 5,000-meter circle. The controller
skips malformed features, preserves provider ordering, and deduplicates by the
unchanged provider place ID.

### Optional live rate enrichment

```text
POST /api/hotels/nearby/rates
```

The body supplies `postcode`, `check_in`, `check_out`, and `adults`. Geoapify
still owns the nearby list and map coordinates. LiteAPI is queried separately
for USD availability and rates, then conservatively matched by exact normalized
name with coordinate/address checks. An unmatched rate remains `null`.

LiteAPI returns a stay total; the controller also calculates the average nightly
rate. These live values are not persisted and are not currently displayed in
the Vue interface. A LiteAPI failure produces a `rates_status` such as
`not_configured` or `provider_unavailable` while preserving the Geoapify list.

### Local saved hotels

```text
GET    /api/hotels/saved?postcode=16802
POST   /api/hotels/saved
DELETE /api/hotels/saved?hotel_id={provider_place_id}
```

POST accepts one unchanged nearby-hotel object plus its resolved
`search_location`. GET returns matching saved hotels, demo nights, the stored
map context, and all saved provider IDs used to restore button state after a
refresh. DELETE returns 404 when the provider ID is not saved.

Expected local-storage failures use structured, sanitized responses. Provider
credentials, credential-bearing URLs, raw provider payloads, and exception text
must never reach the client.

### Stateless saved-hotel chatbot

```text
POST /api/hotels/chat
{"question":"Which saved hotel is available October 10 through October 12?"}
```

The first Gemini request receives only the question, relevant saved-hotel
schema, and query rules. `database.py` validates the typed SQL proposal and
executes it on a read-only/query-only connection with table, column, function,
operation, row, SQL-size, value-size, context-size, and result-shape bounds. It
then verifies every returned hotel/location/night relationship against SQLite.
Gemini never accesses SQLite directly.

Python derives requested nights, missing dates, availability, and complete-stay
totals before the second Gemini request. Check-in is included and checkout is
excluded. Missing nights are not treated as available and never receive a
complete-stay total. The second request receives only the original question,
bounded verified records, and these deterministic facts. The answer must cite
retrieved hotel IDs and echo structured completeness, availability,
missing-night, and total-cost claims. The backend rejects any claim that differs
from the corresponding deterministic match.

## Provider configuration and error behavior

The project-root `.env` may define:

```dotenv
GEOAPIFY_API_KEY=...
LITEAPI_API_KEY=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.1-flash-lite
```

All keys are read only by FastAPI. The browser calls `/api` through Vite and
never receives a credential. Restart FastAPI after changing `.env`.

The earlier `The hotel provider is unavailable.` state occurs when the
Geoapify-backed nearby search cannot complete—for example, the key is missing,
invalid, the request times out, or the provider returns an unusable response.
The permanent project-side fix was to load the root environment explicitly,
keep provider access in the backend, sanitize failures, and preserve the
Geoapify Part 1 route while adding separate LiteAPI and local-storage paths.
External provider outages can still occur and should remain a recoverable,
truthful error rather than being hidden with fabricated results.

`GET /api/health` reports only whether each provider key is configured; it does
not expose a value or contact a provider. Chatbot configuration, rate-limit,
provider, unsafe-query, and invalid-grounding failures use distinct sanitized
codes without returning SQL or provider payloads.

## Verification completed

Verification for the `chatbot-rag-implementation` working tree completed on
2026-10-08:

- 103 backend `unittest` tests passed using temporary databases for mutations.
- 33 frontend `node:test` tests passed.
- `npm run lint` passed.
- `npm run build` passed.
- `PRAGMA foreign_key_check` returned no violations.
- The original database counts remained 8 hotels, 11 users, 18 trips, and 12
  bookings before local saves.
- Fresh and existing database initialization, idempotent repeated saves,
  preservation of edited demo values, ZIP-scoped reads, transactional removal,
  and reopen persistence were exercised.
- Live smoke checks returned HTTP 200 for the backend health route, frontend,
  Vite proxy, and OpenAPI chatbot route. Browser inspection confirmed the fixed
  lower-right chat window, a growing question/answer log, accessible controls,
  and clear no-saved-match and insufficient-nightly-data result cards.
- A full-chain test exercised HTTP, both typed Gemini stages, guarded real
  SQLite retrieval, relationship verification, checkout-exclusive totals,
  grounding, response serialization, and no-write behavior.
- A live `gemini-3.5-flash-lite` request completed both stages with the
  production timeout and returned a grounded `no_matches` result for the empty
  real saved-hotel table. Full-size 3.8 and 3.7 Flash probes returned temporary
  high-demand 503 responses, which is why Flash-Lite is the default while
  `GEMINI_MODEL` remains configurable.

Automated provider tests use mocks and do not consume Geoapify, LiteAPI, or
Gemini quota. Live provider results and model wording are time-dependent and
must not be asserted exactly.

## Run and verify

From the project root, start FastAPI:

```powershell
cd controller
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In a second terminal, start Vue:

```powershell
cd view
npm run dev
```

Expected local URLs are `http://localhost:8000`,
`http://localhost:8000/docs`, and `http://localhost:5173`.

Before persistence work, continue to follow CHECK → TAKE ACTION → VERIFY:
confirm the interpreter and SQLite capability, make the smallest scoped change,
then test fresh creation, references, CRUD, repeated initialization, and reopen
persistence. Keep mutation tests on temporary database files.

## Important files

- `AGENTS.md`: authoritative project and MVC rules.
- `README.md`: setup, routes, configuration, behavior, and limitations.
- `controller/app/database.py`: the only SQLite boundary and all local hotel
  transactions.
- `controller/app/models.py`: database entities and Controller-to-View schemas.
- `controller/app/gemini.py`: stateless, backend-only structured Gemini
  transport.
- `controller/app/hotel_rag.py`: query rules, two-stage orchestration,
  deterministic stay facts, grounding validation, and chatbot route.
- `controller/app/nearby_hotels.py`: Geoapify search and optional LiteAPI rate
  orchestration.
- `controller/app/liteapi.py`: LiteAPI normalization and conservative matching.
- `controller/app/saved_hotels.py`: saved-hotel HTTP routes and demo date range.
- `view/src/components/NearbyHotelSearch.vue`: ZIP, local/API results,
  add/remove state, feedback, and shared list/map selection.
- `view/src/components/HotelChat.vue`: chatbot question, loading, answer,
  evidence, no-match, insufficient-data, and failure states.
- `view/src/hotelChat.js`: tested question validation and evidence formatting.
- `view/src/localHotels.js`: independently tested local-first decision logic.
- `docs/design-pipeline.md`: current end-to-end architecture and request flows.
- `model/README.md`: SQLite lifecycle, tables, and relationships.
- `prompts/09-provider-unavailable-diagnosis.md` through
  `prompts/11-local-first-saved-hotels.md`: latest significant prompt evidence.

## Next action

The complete chatbot implementation and documentation passed the final
acceptance review against `AGENTS.md`, `README.md`, and
`assignment_instructions.md`. Do not commit or push until explicitly requested.
For any additional live Gemini smoke test, use a saved API hotel and dates within
October 10–15, 2026; model wording and free-tier availability may vary while the
returned deterministic facts remain the source of truth.
