# Changelog

## [0.2.0] - 2026-07-08

- **why:** Align output with opencode schema (provider nesting), remove null limit fields, and switch to pretty-printed JSON
- **model:** qwen-3.6-think-coding
- **tags:** output-format, blueprint-compliance

### Fixed

- Provider entry now nested under `"provider"` key to match the opencode JSON schema (`o2cfg/__main__.py`)
- `limit` field omitted from model entries when both context and output are null with no CLI override (`o2cfg/mapper.py`)

### Changed

- JSON output switched from compact format to pretty-printed with indent 2 (`o2cfg/__main__.py`)

## [0.1.0] - 2026-07-08

- **why:** Fix blueprint deviations, implement missing security guards, and add comprehensive test suite
- **model:** qwen/qwen-plus
- **tags:** blueprint-compliance, security, tests

### Fixed

- Verbosity default now starts at `warning` (level 1) instead of `error` (`o2cfg/cli.py`, `o2cfg/__main__.py`)
- Non-auth API failures (timeout, unreachable, non-200, invalid JSON) now exit with code 1 instead of 0 (`o2cfg/__main__.py`)
- Output JSON now uses compact format with trailing newline (`o2cfg/__main__.py`)

### Added

- URL scheme validation: only `http` and `https` are accepted; other schemes raise `ValueError` (`o2cfg/config.py`)
- Path traversal guard: output paths are resolved via `os.path.realpath` before writing (`o2cfg/__main__.py`)
- Unhandled exception handler: top-level try/except in `run()` logs stack trace at debug level, plain message otherwise (`o2cfg/__main__.py`)
- 126 pytest tests covering CLI parsing, config resolution, HTTP client, model filtering, model mapping, and integration (`tests/`)

### Changed

- `o2cfg/__main__.py` — split `run()` into `run()` (wrapper) and `_run()` (implementation) for exception handling

## [0.0.0] - 2026-07-08

- **why:** Initial project scaffolding with architecture docs and README
- **model:** qwen/qwen-plus
- **tags:** scaffold, blueprints, readme, documentation

### Added

- `BLUEPRINT.md` — language-agnostic system architecture defining CLI args, model discovery, filtering, and config output for o2cfg
- `CODEBASE.md` — physical file tree mapping blueprint components to Python stdlib sources with pytest test suite
- `README.md` — user documentation with uvx commands, usage examples, configuration options, and output sample formats
- `docs/memory/INDEX.md` + `docs/memory/archive/2026-07-08-openai2opencode-project.md` — project memory index and decision entries

### Changed

- `references/README.md` — updated to include o2cfg configuration details alongside existing spec links
