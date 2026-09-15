# expedia-copy — Part 1

## Repository and commit

Repository: [github.com/Vinnyfio04/expedia-copy](https://github.com/Vinnyfio04/expedia-copy)

Part 1 implementation checkpoint: [`9227f0548bab06e6edc6e9ea814f8a3bedb3d00e`](https://github.com/Vinnyfio04/expedia-copy/commit/9227f0548bab06e6edc6e9ea814f8a3bedb3d00e)

Commit message: `Added basic working expedia...`

Documentation commit: `88c7b96b8627bf1d603bf5915181e2c951ca9178`

## Implementation

The Vue frontend provides a hotel-name search field, Search button, result count,
no-results message, and a table containing hotel IDs, names, cities, states, and
nightly rates. API requests are kept separate from presentation code in
`frontend/src/api.js`.

The frontend communicates with FastAPI through JSON. It initially requests all
hotels from `GET /api/hotels`. Hotel-name searches use
`GET /api/search?hotel_name=...`.

The Python backend reads the supplied CSV files. It joins hotels and trips through
`hotel_id`, performs case-insensitive hotel-name matching, calculates the number
of nights and estimated stay price, and returns structured JSON. The frontend
converts matching stays into unique hotel rows for the current table.

## Verification

- **Initial page load**
  - Action: Started FastAPI and Vue, then opened the application in a browser.
  - Expected: The supplied hotels should appear with a result count and labeled
    table columns.
  - Observed: The page displayed `8 hotels found.` followed by all eight supplied
    hotels. The table showed Hotel ID, Hotel Name, City, State, and Nightly Rate
    (USD).

- **Successful search**
  - Action: Searched for `Harbor Lantern`.
  - Expected: Harbor Lantern Hotel should be returned.
  - Observed: The page displayed `1 hotel found.` and showed `H001`, Harbor
    Lantern Hotel, Boston, MA, and `$150`.

- **No-results search**
  - Action: Searched for `Not A Real Hotel`.
  - Expected: No table records should be returned and a clear no-results message
    should appear.
  - Observed: The page displayed `0 hotels found.` and
    `No hotels match that name.`

- **Automated checks**
  - Backend: Four tests passed.
  - Frontend: Two tests passed.
  - Frontend lint: Passed.
  - Production build: Passed with Vite.

No verification screenshots are currently stored in the repository. Screenshots
must be captured, committed, and linked here before submission.

## Project context and next steps

- [README.md](https://github.com/Vinnyfio04/expedia-copy/blob/main/README.md)
- [AGENTS.md](https://github.com/Vinnyfio04/expedia-copy/blob/main/AGENTS.md)
- [Design and request pipeline](https://github.com/Vinnyfio04/expedia-copy/blob/main/docs/design-pipeline.md)
- [Selected project prompts](https://github.com/Vinnyfio04/expedia-copy/tree/main/prompts)
- [Current handoff](https://github.com/Vinnyfio04/expedia-copy/blob/main/handoffs/current.md)
- [Assignment instructions](https://github.com/Vinnyfio04/expedia-copy/blob/main/docs/assignment_instructions.md)

The design note, selected prompts, current handoff, and this report were added in
documentation commit `88c7b96b8627bf1d603bf5915181e2c951ca9178`.
That commit is currently local and must be pushed before its GitHub links will be
accessible to the instructor.

Verification screenshots and `docs/verification.md` have not been created. The
current table also summarizes hotels rather than showing each available stay's
trip name, dates, night count, and estimated stay price.

The next task is to add the available-stay fields required by Part 1, repeat the
automated and browser checks, capture repository-accessible screenshots, record
the final verification evidence, and push the reviewed documentation. SQLite
persistence and booking CRUD remain Part 2 work.
