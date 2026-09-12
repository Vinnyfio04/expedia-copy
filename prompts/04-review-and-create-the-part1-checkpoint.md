# Review and create the Part 1 checkpoint

Purpose: Turn reviewed Part 1 work into a traceable GitHub checkpoint without
including generated or local files.

## Prompt

```text
Review the current expedia-copy Part 1 work before committing it. Read AGENTS.md
and docs/assignment_instructions.md. Inspect the Git diff and changed-file list.
Confirm that local environments, node_modules, caches, build output, and secrets
are ignored and unstaged.

Run the backend tests and the frontend lint, tests, and production build. Stop if
a check fails or the diff exceeds the expected Part 1 scope. If all checks pass,
commit the reviewed source, tests, data, and documentation to main with the
approved commit message and push it to the configured GitHub origin without
overwriting remote history. Verify the remote branch points to the new commit.

Report the exact commit hash, commit link, branch, check results, and final
working-tree status.
```
