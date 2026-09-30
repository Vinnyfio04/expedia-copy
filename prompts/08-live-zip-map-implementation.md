# Implement and verify the live ZIP hotel map

Purpose: Replace the fixed ZIP demonstration with the Assignment 2 Part 1 live
Geoapify nearby-hotel search and synchronized Leaflet list/map interface.

## Prompt

```text
Work one approved step at a time and keep the change strictly within Assignment
2 Part 1. Preserve the existing seeded hotel search, booking, history, and
cancellation behavior. Do not change the SQLite schema, seed, database
controller, or add Part 2 persistence.

Install exactly leaflet@1.9.4 in view/ and verify the lockfile and build. Keep
Geoapify credentials in the backend. Add typed external-place contracts rather
than reusing the priced SQLite Hotel model. Implement
GET /api/hotels/nearby?postcode=16802 with exact five-ASCII-digit validation,
strict U.S. ZIP resolution, a hard 5,000-meter Geoapify Places circle,
accommodation.hotel category, proximity bias, and a limit of 20.

Skip malformed provider features, deduplicate by nonblank provider place ID,
and return only name/address, coordinates, and valid provider distance when
available. Distinguish invalid_postcode, postcode_not_found,
provider_rate_limited, and provider_unavailable without exposing keys, URLs,
raw bodies, or exceptions.

Use one Vue parent component for the ZIP form, request/results state, and
selectedPlaceId, plus one Leaflet component for map lifecycle, markers, popups,
view changes, and cleanup. Synchronize card and marker selection in both
directions, use native keyboard-operable buttons, construct popup content from
text nodes, and keep OpenStreetMap attribution visible. Call results nearby
matches or up to 20 results; do not claim exhaustive coverage or invent prices,
ratings, availability, descriptions, or booking support.

Use the existing Python unittest and Node node:test tooling. Mock provider calls
in automated tests. Run the full backend suite, npm test, npm run lint, and npm
run build. Browser-smoke-test invalid, unresolved, valid, empty, rate-limited,
and unavailable states; list/map synchronization; keyboard behavior; responsive
layout; and existing local search, booking, and history screens. Make a live
Geoapify observation only when a key is configured and never assert a fixed
live result count.

Update documentation only from observed results. Preserve docs/report.md
exactly and do not modify it.
```

## Observed verification

- 38 backend tests and 20 frontend tests passed.
- Frontend lint and production build passed.
- Browser smoke testing covered every required state and interaction.
- A configured-key check of ZIP `16802` on 2026-09-29 returned 20 capped nearby
  matches; the count was recorded only as a dated observation.
- Existing local hotel search, booking, and history views passed regression
  checks.
