# 22. Cursor pagination with has-more signal

Date: 2026-04-03

## Status

Accepted

## Context

The `GET /vocabularies/{agencyId}/{keyConcept}` endpoint returned a
`totalResults` field that clients could use to detect the end of a dataset.
Computing an accurate total count requires an extra query on every paginated
request, adding overhead with no benefit for cursor-based clients.

With cursor pagination, clients already discover the last page naturally.
A dedicated has-more signal is both cheaper and more explicit.

This change affects only the vocabulary data endpoint
(`/vocabularies/{agencyId}/{keyConcept}`). The linkset catalog endpoints
(`/vocabularies` and `/vocabularies/{agencyId}`) retain their existing
offset-based pagination: this can be migrated to cursor-based pagination in the future.

## Decision

- [x] Remove `totalResults` and `offset` from the `PaginatedResponse` schema.
- [x] Add an optional `next_cursor` field to `PaginatedResponse`. When present,
  it contains the `id` to pass as the `cursor` parameter to retrieve the next
  page. When absent, the current page is the last one.
- [x] Defer the cursor migration of /vocabularies to a future ADR.

## Consequences

Pros:

- No extra count query per paginated request.
- Clients get an unambiguous has-more signal and a ready-to-use cursor value.

Cons:

- When `id` is not unique (which is not supported), `next_cursor` may result in infinite loops.
- Clients that relied on `totalResults` to display a total count or compute
  page numbers must be updated.
- Offset-based navigation is no longer supported on the data endpoint; sequential
  cursor traversal is required to reach a specific position in the dataset.
