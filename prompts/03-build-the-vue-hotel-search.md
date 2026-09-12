# Build the Vue hotel search

Purpose: Connect the Vue interface to the existing FastAPI contract while
keeping transport code separate from presentation code.

## Prompt

```text
Build the first expedia-copy Vue interface from the current repository. Do not
redesign backend behavior or add dependencies.

The interface needs a label reading "Hotel name", a text field with a Search
button to its right, a result sentence such as "3 hotels found.", and an HTML
table with Hotel ID, Hotel Name, City, State, and Nightly Rate (USD). Load the
initial rows from GET /api/hotels. Submit hotel searches through
GET /api/search?hotel_name=..., and adapt repeated stay results into unique hotel
rows without changing the backend response. An empty search should reload all
hotels.

Use Vue 3 Composition API in frontend/src/App.vue. Keep fetch calls and response
adaptation in frontend/src/api.js. Include loading, request-error, and no-results
states, accessible labels, and a usable narrow-screen table. Add or update tests
without adding packages. Run the existing frontend lint, tests, and production
build, then report evidence and changed files.
```
