# Document the design pipeline

Purpose: Capture the repository's real architecture and the evidence-driven
agent workflow in a concise project reference.

## Prompt

```text
Create docs/design-pipeline.md from the current expedia-copy repository. Read the
current files before writing.

Include a short explanation of the frontend/backend boundary; an ASCII
project-file map naming files that actually exist; an ASCII request flow from the
Vue interface through JavaScript, FastAPI, the plain Python calculation function,
JSON, and back to the interface; and the agentic review loop: describe, predict
the blast radius, plan, implement, inspect the Git diff, verify behavior, and
then correct or commit.

Do not invent files, functions, paths, API endpoints, or verification commands.
Do not change application code, dependencies, or Git history. When finished,
show the changed-file list and compare it with the expected documentation-only
blast radius.
```
