# AGENTS.md - Agent Coding Guidelines for pymediawikidocker

This file provides guidelines for agentic coding agents working on this repository.

## Important Rules

**CRITICAL: NEVER EVER DO ANY ACTION READING, MODIFYING OR RUNNING without explaining the plan.
Each set of intended actions needs to be explained in the format:
I understood that <YOUR ANALYSIS> so that i plan to <GOALS YOU PURSUE> by <ACTIONS TO BE CONFIRMED> confirm with go!
YOU WILL NEVER PROCEED WITHOUT POSITIVE CONFIRMATION by go!**

## Project Overview

pymediawikidocker creates and controls clusters of MediaWiki docker
application instances - each consisting of a MediaWiki and a MariaDB
container. Documentation: https://wiki.bitplan.com/index.php/Pymediawikidocker

It consists of:
- `mwdocker/` - the python package
- `mwdocker/resources/` - jinja templates and extension catalog
- `tests/` - unit tests using unittest

Requires Python 3.10+ and a running docker daemon for the
integration tests.

---

## Build, Lint, and Test Commands

### Installation
```bash
pip install .
# or: scripts/install
```

### Running Tests

**Run all tests with unittest discover (default):**
```bash
python3 -m unittest discover
# or: scripts/test
```

**Run a single test file:**
```bash
python -m unittest tests.test_extensions
```

**Run a specific test method:**
```bash
python -m unittest tests.test_extensions.TestExtensions.testSpecialVersionHandling
```

Note: `tests/test_install.py` creates real docker clusters and takes
several minutes; `testSpecialVersionHandling` scrapes live BITPlan
wikis over the network.

### Code Formatting

**Format and sort imports (always before commit):**
```bash
scripts/blackisort
```
This runs `isort` then `black` (88 character line length).

### Running the Application

**CLI command:**
```bash
mwcluster   # mwdocker/mwdocker_cmd:main
```

---

## Code Style Guidelines

### Imports

Order imports as follows (enforced by isort):
1. Standard library
2. Third-party packages
3. Local application imports (`mwdocker.*`, `tests.*`)

Top-level imports only - no inline imports in functions.

### Formatting

- **Line length**: black default (88 characters)
- **Strings**: f-strings for interpolation
- **Indentation**: 4 spaces

### Type Hints

Required on new function signatures and return types.
Prefer `Optional[X]` over `X | None` for 3.10 compatibility.

### Naming Conventions

- **Classes**: `PascalCase` (e.g. `ExtensionList`, `MwClusterConfig`)
- **New functions/methods**: `snake_case`
- **Legacy camelCase** (e.g. `getDetailsFromUrl`): keep for
  compatibility; use snake_case for new code
- **Constants**: `UPPER_SNAKE_CASE`

### Docstrings

Google-style with Args/Returns sections; module headers use:
```python
"""
Created on YYYY-MM-DD

@author: wf
"""
```

### Return Style

Named return variable, single return - no direct expression returns.

### Error Handling

- Catch specific exceptions; auxiliary operations (e.g. scraping
  extension detail pages) must tolerate transient network errors
- `debug` flag gates diagnostic output

### Data Classes

Use the `@lod_storable` decorator from `basemkit.yamlable` for
YAML/JSON storable dataclasses (see `mwdocker/mw.py`).

### Testing

- Test classes inherit from `Basetest` (from `basemkit.basetest`)
- No pytest fixtures, no conftest.py - unittest style only
- `Basetest.inPublicCI()` gates tests that cannot run in GitHub Actions

### File Organization

```
pymediawikidocker/
├── mwdocker/            # python package
│   ├── config.py        # MwClusterConfig
│   ├── docker.py        # docker application handling
│   ├── mw.py            # Extension / ExtensionList
│   ├── mwcluster.py     # cluster handling
│   ├── mwdocker_cmd.py  # mwcluster CLI
│   ├── webscrape.py     # WebScrape helper
│   └── resources/       # jinja templates, extensions.json
├── tests/               # unittest based tests
├── scripts/             # install, test, blackisort, doc, release
└── pyproject.toml       # hatchling build
```

### Dependencies

Key dependencies (see pyproject.toml):
- `pybasemkit` - Basetest, YAML/JSON storable dataclasses
- `python_on_whales` - docker control
- `beautifulsoup4` - Special:Version scraping
- `jinja2` - templating for docker/LocalSettings files

---

## CI/CD

GitHub Actions workflow: `.github/workflows/build.yml`
- Runs on Python 3.10 (ubuntu-latest)
- Installs dependencies via `scripts/install`
- Runs tests via `scripts/test`

Release: `.github/workflows/upload-to-pypi.yml` - hatch build with
OIDC trusted publishing on GitHub release.

---

## Additional Notes

- Version is managed via hatchling in `mwdocker/__init__.py`
- Compliance is checked with `checkos -o WolfgangFahl -p pymediawikidocker --local`
- Follow existing code patterns when extending functionality
