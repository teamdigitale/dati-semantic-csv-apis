# 23. Catalog search uses `q` instead of a dedicated `description` parameter

Date: 2026-04-03

## Status

Accepted

## Context

The catalog endpoints (`GET /vocabularies` and `GET /vocabularies/{agencyId}`)
expose filters for `title`, `author`, `hreflang`, `concept`.

An user-friendly search mechanism for generic metadata
should be implemented.
A dedicated `description` query parameter was considered to let callers
search exclusively on the description field, while callers do
not know in what field the information is.

## Decision

- [x] Add a generic `q` parameter instead of a `description` query parameter to the catalog endpoints.
- [x] `q` matches against both `title`, `description` and other metadata.
- [x] The `title` parameter remains a dedicated substring filter for clients
  that need strict title-only matching.

## Consequences

Pros:

- Simpler API surface: one `q` parameter covers all free-text metadata fields.

Cons:

- Callers cannot restrict a query to the description field only; `q` always
  searches across all indexed columns.
