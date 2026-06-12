# 27. Pin dependencies with compiled lockfiles

<!-- In vim, use !!date -I to get current date. -->

Date: 2026-06-12

## Status

<!-- Proposed, Accepted, Deprecated, Superseded, or Rejected -->

Accepted

## Context

We want one source of truth for the abstract
dependencies and a separate, fully pinned set used
for reproducible installs in CI and the container.

One direct dependency, `pyld`, is pinned to a Git
commit that contains a JSON-LD framing fix not yet
released on PyPI.

## Decision

- [x] Keep abstract direct dependencies in `*.in` files
  (`requirements.in`, `requirements-dev.in`, and the
  `apiv1/` equivalents).
- [x] Compile each `*.in` into a fully pinned, hashed
  `*.txt` lockfile via pre-commit.
- [x] Compile the `*-dev.txt` lockfiles with the base
  `*.txt` as a constraint (`-c`), so versions stay
  consistent when installed together.
- [x] Read package metadata in `pyproject.toml` from
  the `*.in` files, not the lockfiles.

## Consequences

Pros:

- Installs are reproducible: the whole transitive
  closure is pinned and hash-verified.
- Lockfiles are generated, never edited by hand;
  changing a dependency means editing one `*.in` file
  and re-running the hook.
- `--universal` produces a single lockfile valid
  across the supported Python versions.

Cons:

- Lockfiles carry hashes, so they must be installed
  with `uv`. Plain `pip install -r` enters
  hash-checking mode, which rejects the Git-pinned
  `pyld` URL. The container and `tox-uv` already
  use `uv`.
- `pyproject.toml` must read the `*.in` files: the
  lockfile syntax (`--hash` lines and line
  continuations) is not valid package metadata.
