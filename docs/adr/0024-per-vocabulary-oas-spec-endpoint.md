# 24. Per-vocabulary OpenAPI spec endpoint

Date: 2026-04-09

## Status

Accepted

## Context

The Data API exposes a single global OpenAPI spec covering all vocabularies.
Vocabulary consumers need a self-contained spec scoped to a specific vocabulary,
with the correct base URL and without unrelated paths or parameters.

Browsers send `Accept: text/*` by default, so serving `application/openapi+yaml`
causes a download dialog instead of inline display.

## Decision

- [x] Expose a vocabulary-scoped OpenAPI spec derived from the global spec
  at runtime, with paths and parameters trimmed to the vocabulary context.
- [x] Return `text/plain; charset=utf-8` when the client prefers `text/*`,
  to allow browsers to display the spec inline.
- [x] CORS is applied to redirect responses,
  so the OAS endpoint is accessible from any origin.

## Consequences

Pros:

- Vocabulary consumers get a focused, directly usable spec.
- Browser-friendly without requiring a dedicated UI.
- The OAS endpoint can be easily integrated in schema.gov.it.

Cons:

- The `text/plain` content type is a browser accommodation, not semantically
  correct for an OpenAPI document.
