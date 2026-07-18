# Changelog

## [0.4.0] - 2026-07-18

- **why:** Add vision model support so opencode can recognize image-capable models from OpenAI-compatible APIs
- **model:** kompis/qwen-3.6-think-coding-mtp
- **tags:** vision, cli, model-stanza

### Added

- `--vision` / `-i` CLI flag accepts comma-separated glob patterns for vision-enabled models (`o2cfg/cli.py`, `o2cfg/config.py`)
- Vision stanza (`attachment: true`, `modalities: { input: ["text", "image"], output: ["text"] }`) applied to matching models during mapping (`o2cfg/mapper.py`)
- Vision tests across CLI parsing, config resolution, model mapping, and integration (`tests/cli_test.py`, `tests/config_test.py`, `tests/mapper_test.py`)

### Changed

- `BLUEPRINT.md` — added `--vision` argument spec, data flow notes, and output schema examples with vision stanza
- `README.md` — added "Marking models as vision-enabled" section and updated flags table

## [0.3.3] - 2026-07-14

- **why:** Remove unused imports to clean up code and reduce startup overhead
- **model:** kompis/qwen-3.6-think-coding
- **tags:** refactor, linting, cleanup

### Fixed
- Removed unused imports in o2cfg/cli.py and various test files.

## [0.3.2] - 2026-07-14

- **why:** Fix URL normalization with trailing slashes, dead code removal, and CLI flags that accept optional values
- **model:** kompis/qwen-3.6-think-coding-mtp
- **tags:** bug-fix, cli, url-normalization, dead-code

### Fixed

- Trailing slashes on `--url` no longer produce a double `/v1` in the request URL (`o2cfg/config.py`)
- `--url`, `--api-key`, `--output`, `--provider-name`, `--allowlist`, and `--denylist` accept no value and fall back to environment variables (`o2cfg/cli.py`, `o2cfg/config.py`)

### Changed

- Removed dead `mutually_exclusive_group` in the CLI parser (`o2cfg/cli.py`)
- Removed unused default `verbosity=1` in `Settings.__init__`; now defaults to `0` (`o2cfg/config.py`)

### Fixed

- Removed incorrect verbosity claim from 0.1.0 changelog entry (`CHANGELOG.md`)

## [0.3.1] - 2026-07-09

- **why:** Version drift between pyproject.toml and __init__.py; --version flag used a hardcoded constant instead of __version__
- **model:** qwen-3.6-think-coding
- **tags:** version, bump-script, cli

### Fixed

- `--version` flag now reads from `__version__` in `o2cfg/__init__.py` instead of a hardcoded constant (`o2cfg/cli.py`)
- `scripts/bump-version.sh` now updates both `pyproject.toml` and `o2cfg/__init__.py` in lockstep
- `o2cfg/__init__.py` version aligned with `pyproject.toml`

### Changed

- `scripts/bump-version.sh` checks for both `pyproject.toml` and `o2cfg/__init__.py` before running

## [0.3.0] - 2026-07-09

- **why:** Add glob pattern filtering, short CLI flags, comprehensive logging, and fix config edge cases
- **model:** qwen-3.6-think-coding
- **tags:** glob-filtering, cli-flags, logging, config-fixes

### Added

- Glob pattern matching for allowlist and denylist filters (`o2cfg/filter.py`)
- Short flags `-C` and `-O` for context and output model limit overrides (`o2cfg/cli.py`)
- Logging throughout the CLI and config modules (`o2cfg/cli.py`, `o2cfg/config.py`, `o2cfg/__main__.py`)

### Fixed

- `base_url` trailing `/v1/models` handled without double-path duplication (`o2cfg/config.py`)
- `limit` field only included in output when explicitly set (`o2cfg/mapper.py`)
- Typo in model name reference

### Changed

- Large files split into smaller focused modules (`o2cfg/`)

## [0.2.1] - 2026-07-08

- **why:** Verbosity default did not match the blueprint spec; no flags and -vv both produced debug output
- **model:** qwen-3.6-think-coding
- **tags:** verbosity, blueprint-compliance, bug-fix

### Fixed

- Default verbosity now maps to warning (no flags and -v both produce warning); -vv produces info; -vvv produces debug (`o2cfg/cli.py`, `o2cfg/__main__.py`)

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
- **model:** qwen-3.6-think-coding
- **tags:** blueprint-compliance, security, tests

### Fixed

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
- **model:** qwen-3.6-think-general
- **tags:** scaffold, blueprints, readme, documentation

### Added

- `BLUEPRINT.md` — language-agnostic system architecture defining CLI args, model discovery, filtering, and config output for o2cfg
- `CODEBASE.md` — physical file tree mapping blueprint components to Python stdlib sources with pytest test suite
- `README.md` — user documentation with uvx commands, usage examples, configuration options, and output sample formats
- `docs/memory/INDEX.md` + `docs/memory/archive/2026-07-08-openai2opencode-project.md` — project memory index and decision entries

### Changed

- `references/README.md` — updated to include o2cfg configuration details alongside existing spec links
