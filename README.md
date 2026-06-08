# DB MCP Server

`db-mcp-server` provides database discovery, catalogue, API, Web UI, MCP, and A2A runtime surfaces.

## Publication Quick Start

Prerequisites:

- Docker 24 or newer with BuildKit enabled
- Python 3.12 if you run the package locally
- Public package source: `https://pypi.org/simple` (single index; no `--extra-index-url`)

Build the public image (see [EXTERNAL-BUILD.md](EXTERNAL-BUILD.md) for the full
external-builder guide):

```bash
./docker-build.sh latest --variant public
```

Or an isolated, registry-skipping publication-test image:

```bash
PUBLICATION_TAG_SUFFIX=github-test ./docker-build.sh latest --variant public
```

Run the local smoke by executing the shell block in [PUBLICATION-SMOKE.md](PUBLICATION-SMOKE.md) with `TAG=latest-gitea-test`.

The smoke run uses [.env.example](.env.example) and probes:

- API: `8086`
- Web: `8087`
- MCP: `8088`
- A2A: `8089`

## Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
# Single public index; the cloud_dog_db[nosql,sql] extras pull the DB drivers.
pip install -e ".[dev]" --index-url https://pypi.org/simple
```

The Cloud-Dog platform packages must be resolvable from the index you use. See
[EXTERNAL-BUILD.md](EXTERNAL-BUILD.md) for the public package-source strategy.

Runtime configuration is loaded from the env file passed to `server_control.sh`, then from shell environment variables, then from `defaults.yaml`.

## Documentation

- [BUILD.md](BUILD.md)
- [PUBLICATION-SMOKE.md](PUBLICATION-SMOKE.md)
- [.env.example](.env.example)

## Licence

Apache-2.0 - Copyright (c) 2026 Cloud-Dog, Viewdeck Engineering Limited
