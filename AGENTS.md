# Project rules

## Scope

- Keep the project split into `backend/` for FastAPI and `frontend/` for Vue.
- Prefer small, focused changes that are easy to review and test.
- Do not commit generated files, local environments, dependency folders, or secrets.

## Backend

- Put application code under `backend/app/`.
- Use type hints for public Python functions.
- Keep API routes thin; move reusable business logic into dedicated modules as the project grows.
- Return clear HTTP status codes and structured error responses.
- Add or update tests whenever backend behavior changes.

## Frontend

- Put Vue source files under `frontend/src/`.
- Use Vue 3 Composition API for new components.
- Keep components focused and extract shared behavior when it is reused.
- Keep API access separate from presentation components as the app grows.
- Add or update tests whenever frontend behavior changes.

## Quality and safety

- Never hard-code credentials or API keys. Use environment variables and document required values.
- Do not install or upgrade dependencies unless the user explicitly asks.
- Run the relevant checks before declaring a change complete; report any checks that could not be run.
- Update `README.md` when setup steps or project structure change.

