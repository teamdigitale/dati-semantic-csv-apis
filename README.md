# Dati Semantic APIs

This repository provides documents, tools and PoC
for the management of semantic assets in the context
of the National Data Catalog for Semantic Interoperability.

This project is related to:

- <https://schema.gov.it>
- <https://github.com/teamdigitale/dati-semantic-schema-editor>

## Table of contents

- 💻 [Usage](#usage)

- 🚀 [API](#api)

<!-- - 📋 [Development](#development) -->

- 📝 [Contributing](#contributing)
- ⚖️ [License](#license)

The repository currently contains:

- a Python CLI for generating and validating
  vocabulary artifacts;
- an ASGI API for serving vocabulary catalogs,
  entries, and per-vocabulary OpenAPI specs;
- architecture and functional documentation in
  [docs](docs).

The core functional documentation is in Italian:

## Usage

The core documentation for this project
is in :flag-it: Italian.
You can find it in the [docs](docs) folder.

- [CSV Serialization](docs/README.csv.md)
- [REST API for Controlled Vocabularies](docs/README.api.md)

## Quick start

The project requires Python 3.12 or newer.

Build CLI:

```bash
tox -e build
dist/schema_gov_it_tools.bin --help
```

Run the root test suite:

```bash
tox --
```

Run the API test suite:

```bash
tox -e api
```

Run the containerized test environment:

```bash
docker compose up test
```

## API

The API implementation lives in [apiv1](apiv1).
It runs as an ASGI application on `uvicorn`.

Start the local API container:

```bash
docker compose up api-data --build
```

Start the local TLS reverse proxy used in tests:

```bash
docker compose up api-data-tls
```

Then open <https://localhost/ui/>.

## Contributing

Please, see [CONTRIBUTING.md](CONTRIBUTING.md) for more details on:

- using [pre-commit](CONTRIBUTING.md#pre-commit);
- following the git flow and making good [pull requests](CONTRIBUTING.md#making-a-pr).

Repository layout is the following:

```text
docs/         Project documentation and ADRs
assets/       Shared controlled vocabulary assets
tools/        CLI implementation
tests/        CLI and library tests
apiv1/        API implementation and API tests
scripts/      Helper scripts
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- pre-commit setup;
- branch and pull request workflow;
- CI expectations.

You can also test GitHub Actions locally with
[`act`](https://github.com/nektos/act):

```bash
# Run a specific job in the pipeline
act -j test
```
