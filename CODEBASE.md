# CODEBASE: o2cfg

**Language:** Python 3.10+
**Project Name:** o2cfg
**Virtual Environment Tool:** uv
**Test Framework:** pytest

---

## Directory Structure

```
o2cfg/
├── .gitignore
├── pyproject.toml          # project metadata, package info, test config (uv-compatible)
├── README.md               # usage, install, quick start
├── o2cfg/                  # source package
│   ├── __init__.py         # package marker, version string
│   ├── __main__.py         # entry point: argparse dispatch, discovery pipeline
│   ├── cli.py              # argparse setup, argument definitions, verbosity resolution
│   ├── config.py           # Config Resolver — merges CLI args + env vars, provides resolved settings object
│   ├── client.py           # OpenAI Client — HTTP GET /v1/models, timeout, auth header, error handling
│   ├── filter.py           # Model Filter — apply denylist first, then allowlist; no-op when both absent/empty
│   ├── mapper.py           # Model Mapper — transform API model objects to opencode schema + auto-discovery fallbacks
│   ├── output.py           # Output Writer — build config documents and write to stdout or file atomically
│   └── provider_name.py    # Provider Name — derive display name from base URL hostname
├── tests/                  # test suite
│   ├── __init__.py
│   ├── conftest.py         # shared fixtures — mocked HTTP responses, sample model payloads
│   ├── cli_test.py         # CLI argument parsing: help, version, all flags, missing-required validation
│   ├── config_test.py      # Config Resolver — env var merging, provider name resolution fallback chain, output null default
│   ├── client_test.py      # OpenAI Client — timeout, auth header injection, HTTP error codes, malformed JSON
│   ├── filter_test.py      # Model Filter — denylist removes entries, allowlist narrows to subset, both combined, empty/no-op cases
│   ├── mapper_test.py      # Model Mapper — id/name mapping, context/output extracted or null + override path
│   ├── main_config_doc_test.py  # Integration: build_config_document tests
│   ├── main_output_test.py    # Integration: write_output stdout and file tests
│   ├── main_run_basic_test.py # Integration: basic run with mocked discovery
│   ├── main_run_errors_test.py # Integration: error handling and discovery failure tests
│   └── main_run_test.py       # Integration: run overrides and custom provider tests
└── scripts/
    └── verify_codebase_sync.sh  # sync verification for CODEBASE.md physical paths
```

---

## Physical File Mapping (Blueprint → CODEBASE)

| Blueprint Component       | Source File            | Tests                     | Notes                                    |
|---------------------------|------------------------|---------------------------|------------------------------------------|
| CLI Layer                 | `o2cfg/__main__.py`, `o2cfg/cli.py`          | `tests/cli_test.py`    | Single invocation; argparse-driven       |
| Config Resolver           | `o2cfg/config.py`      | `tests/config_test.py`   | Provider name fallback, optional args    |
| Provider Name Derivation  | `o2cfg/provider_name.py` | `tests/config_test.py`  | URL hostname to display name conversion  |
| OpenAI Client             | `o2cfg/client.py`       | `tests/client_test.py`  | Timeout, Bearer auth, error boundaries   |
| Model Filter              | `o2cfg/filter.py`       | `tests/filter_test.py`  | Denylist first, then allowlist           |
| Model Mapper              | `o2cfg/mapper.py`       | `tests/mapper_test.py`  | Schema transformation, auto-discovery    |
| Output Writer (stdout/file) | `o2cfg/output.py`        | `tests/main_output_test.py` | stdout by default; atomic file write with `--output` |
| Config Document Builder   | `o2cfg/output.py`        | `tests/main_config_doc_test.py` | Build opencode JSON structure |
| Integration (run pipeline) | `o2cfg/__main__.py`   | `tests/main_run_*.py`   | Full CLI run with mocked discovery       |

---

## Dependency Manager

### Virtual Environment Setup

```bash
# Create venv and install dependencies
uv venv

# Activate (platform-specific)
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# Install development + test deps
uv pip install pytest

# Run tests
pytest
```

### pyproject.toml

Minimal metadata with uv-compatible package name and dependencies section:

```toml
[project]
name = "o2cfg"
version = "0.1.0"
description = "Auto-discover OpenAI-compatible models and generate opencode.json provider configs."
requires-python = ">=3.10"
dependencies = []        # stdlib only — no external runtime deps

[project.optional-dependencies]
test = ["pytest"]        # dev/test dependency, installed with uv pip install -e ".[test]"

[project.scripts]
o2cfg = "o2cfg.__main__:main"
```

---

## Python Standard Library Usage

All runtime dependencies are stdlib only. No external packages are needed for the application to function.

| Area                    | Stdlib Modules Used                              |
|-------------------------|--------------------------------------------------|
| HTTP Requests           | `urllib.request`, `urllib.parse`                |
| JSON Serialization      | `json`                                          |
| CLI / Arguments         | `argparse`, `sys`                               |
| Logging                 | `logging`                                       |
| Paths & File I/O        | `pathlib`, `os`, `tempfile`                     |
| URL Parsing             | `urllib.parse`                                  |
| Version/Type Hints      | `__version__` (manual), `typing` module         |

---

## Test System

### Framework: pytest

- Tests live in `tests/` parallel to the source package.
- Fixtures defined in `tests/conftest.py` provide sample OpenAI `/v1/models` responses and mock clients via `unittest.mock.patch`.
- No external mocking libraries — use `unittest.mock` (stdlib).

### Test Categories

| File           | What is tested                                          | How                                      |
|----------------|---------------------------------------------------------|------------------------------------------|
| `cli_test.py`  | Argument parsing, help/version output, required flags   | Subprocess invocation or direct argument parsing; verify exit codes via argparse. |
| `config_test.py`              | Settings merging, provider name fallback chain          | Call resolver with different flag/env combos; assert resolved values. |
| `client_test.py`               | HTTP requests to `/v1/models`, error handling           | Patch `urllib.request.urlopen`; verify request URL, headers, timeout value, and exception raising on non-200. |
| `filter_test.py`             | Denylist removals, allowlist subsetting, glob patterns, edge cases   | Feed raw model lists into filter function; assert output length and membership. Uses ``fnmatch`` glob syntax (``*``, ``?``, ``[seq]``). |
| `mapper_test.py`             | Model object transformation, limit extraction/fallback | Map sample API responses; verify output keys, null handling, CLI override paths. |

### Test Execution Patterns

```bash
# Run all tests
pytest

# Verbose mode
pytest -v

# Single file only
pytest tests/filter_test.py -v

# Coverage (optional, requires stdlib-only approach)
# Users can install coverage themselves with `uv pip install coverage`
coverage run -m pytest
```
