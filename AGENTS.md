# Project rules

## Scope

- Keep the project organized as `model/` for application data, `view/` for Vue,
  and `controller/` for FastAPI and application controllers.
- Prefer small, focused changes that are easy to review and test.
- Do not commit generated files, local environments, dependency folders, or secrets.

## MVC responsibilities and contracts

- **Model:** `controller/app/models.py` defines the typed entity and API data
  contracts. `model/seed.sql` is the immutable initial data source.
  `model/expedia.db` is the generated SQLite source of truth after its first seed
  and must not be committed.
- **View:** Vue components, browser state, presentation, and all CSS stay under
  `view/src/`. The View exchanges JSON only through `/api` and must never open the
  seed or SQLite files or call an external provider with a backend credential.
- **Controller:** FastAPI routes and business controllers stay under
  `controller/app/`. `database.py` is the only module that opens SQLite and it
  accepts and returns the typed model objects. Other controllers may call its
  public CRUD methods or one another's typed functions; they must not depend on
  Vue components or CSS.
- Keep boundary contracts explicit: model objects represent database inputs and
  outputs, FastAPI response models define Controller-to-View JSON, and expected
  domain failures are translated into clear HTTP status codes and structured
  errors at the route boundary.
- Database writes must be parameterized and transactional. Enable SQLite foreign
  keys on every connection, preserve the Hotel-to-Trip and User/Trip-to-Booking
  relationships, and verify them with `PRAGMA foreign_key_check`.
- Apply the SQL seed only once. Restarting the application must not duplicate
  records, restore deleted records, or overwrite changes already stored in
  SQLite.

## Controller

- Put FastAPI application code under `controller/app/`.
- Use type hints for public Python functions.
- Keep API routes thin; move reusable business logic into dedicated modules as the project grows.
- Keep entity persistence in the database controller and unrelated business
  logic in focused controllers with agreed typed inputs and outputs.
- Return clear HTTP status codes and structured error responses.
- Add or update tests whenever backend behavior changes.

## View

- Put Vue source files under `view/src/`.
- Use Vue 3 Composition API for new components.
- Keep components focused and extract shared behavior when it is reused.
- Keep API access separate from presentation components as the app grows.
- Add or update tests whenever frontend behavior changes.

## Quality and safety

- Never hard-code credentials or API keys. Use environment variables and document required values.
- Do not install or upgrade dependencies unless the user explicitly asks.
- Run the relevant checks before declaring a change complete; report any checks that could not be run.
- Update `README.md` when setup steps or project structure change.
- Before changing persistence, follow **CHECK → TAKE ACTION → VERIFY**: inspect
  the selected interpreter and existing database capability, explain any needed
  installation and obtain approval, then exercise creation, references, CRUD,
  and reopen/persistence behavior.
