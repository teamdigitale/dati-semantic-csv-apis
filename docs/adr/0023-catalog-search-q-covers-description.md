# 23. Catalog search uses `q` instead of a dedicated `description` parameter

Date: 2026-04-03

## Status

Accepted

## Context

The catalog endpoints (`GET /vocabularies` and `GET /vocabularies/{agencyId}`)
expose filters for `title`, `author`, `hreflang`, `concept`, and a general
query string `q`. The underlying FTS5 index (`_metadata_fts`) covers both the
OpenAPI `info.title` and `info.description` columns, so a single `q` query
already matches against vocabulary descriptions.

A dedicated `description` query parameter was considered to let callers
search exclusively on the description field. However, in practice callers do
not need to restrict full-text search to one field: a term that appears in a
description but not in a title is still a valid match for `q`.

## Decision

- [x] Do not add a `description` query parameter to the catalog endpoints.
- [x] Document that `q` matches against both `title` and `description` via the
  FTS5 index.
- [x] The `title` parameter remains a dedicated substring filter for clients
  that need strict title-only matching.

## Consequences

Pros:

- Simpler API surface: one `q` parameter covers all free-text metadata fields.
- No duplication between `q` and a `description` parameter that would both hit
  the same FTS5 index columns.

Cons:

- Callers cannot restrict a query to the description field only; `q` always
  searches across all indexed columns (`title`, `description`, `catalog`).
