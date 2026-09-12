# Plan the implementation

Purpose: Define the smallest compliant frontend/backend implementation and its
verification evidence before editing files.

## Prompt

```text
Read AGENTS.md, README.md, and docs/assignment_instructions.md, then plan the
smallest implementation of expedia-copy.

Keep FastAPI application code under backend/app/ and Vue source under
frontend/src/. The backend owns CSV access, joins, validation, calculations, and
API paths. The Vue frontend owns inputs, controls, requests, and presentation.
The layers communicate through JSON.

Do not edit files yet. Identify the files you expect to create or modify, the
order of work, the checks that will prove each layer works, the expected Git
checkpoint, and any decision that requires approval. Call out contradictions or
missing evidence in the assignment materials instead of silently choosing an
interpretation.
```
