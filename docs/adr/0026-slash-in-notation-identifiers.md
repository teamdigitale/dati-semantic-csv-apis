# 26. Support `/` in skos:notation identifiers

Date: 2026-04-02

## Status

Accepted

## Context

Some controlled vocabularies use `skos:notation` values that contain a
forward slash (e.g. ATECO codes like `A/01`).
The previous identifier pattern `^[A-Za-z0-9._-]+$` rejected these values,
making it impossible to round-trip such vocabularies through the API.

## Decision

- [x] Extend the allowed pattern for `skos:notation` / identifier fields to
  include `/`: `^[A-Za-z0-9._/-]+$`.
- [x] The API accepts both slash-containing and non-slash-containing notations, without any special handling.

## Consequences

Pros:

- Vocabularies with slash-containing notations are fully supported.
