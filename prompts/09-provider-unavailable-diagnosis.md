# Diagnose the unavailable hotel provider

Purpose: Reproduce the ZIP-search failure, identify which provider boundary
causes it, and replace a brittle provider dependency with a durable backend
integration and truthful fallback behavior.

## Prompt

```text
Enter zip code 16802 and hit search. Analyze the "the hotel provider is
unavailable" error and report why it occurs. Find a permanent solution and
execute the solution.
```

## Resulting decisions

- Keep all provider credentials in the FastAPI process and load the project-root
  `.env` through an explicit path.
- Preserve Geoapify as the source for exact ZIP resolution, nearby place IDs,
  list ordering, coordinates, and the map.
- Use LiteAPI only for the separate date-specific rate endpoint. A rate-provider
  failure must not discard otherwise valid Geoapify nearby results.
- Return sanitized status values such as `not_configured`,
  `provider_unavailable`, and `no_availability`; never expose keys, raw payloads,
  credential-bearing URLs, or exception text.
- Treat provider outages as recoverable external failures. Do not replace them
  with fabricated hotels, rates, or availability.

