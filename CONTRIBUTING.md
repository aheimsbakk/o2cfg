# Contributing to o2cfg

This guide covers development setup, testing, repository scripts, and the
contribution workflow.

## Development setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/aheimsbakk/o2cfg.git
cd o2cfg
uv venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
uv pip install -e ".[test]"
```

The runtime uses only Python standard library modules. The `test` extra adds
`pytest`, `pytest-cov`, and `coverage` — the only project dependencies.

## Running tests

```bash
pytest
```

Coverage must stay at or above 80%. `pyproject.toml` sets
`[tool.coverage.report] fail_under = 80`, so any run that collects coverage
fails below the threshold. To collect and view per-module coverage:

```bash
pytest --cov
```

No lint or typecheck tooling is configured in `pyproject.toml`.

## Repository scripts

All scripts live in `scripts/` and are executable. Run them from the
repository root.

### scripts/bump-version.sh

Bumps the version in `pyproject.toml` and `o2cfg/__init__.py` in lockstep.
Takes one required argument: `patch`, `minor`, or `major`.

```bash
./scripts/bump-version.sh patch   # 0.4.2 -> 0.4.3
./scripts/bump-version.sh minor   # 0.4.2 -> 0.5.0
./scripts/bump-version.sh major   # 0.4.2 -> 1.0.0
```

### scripts/validate-changelog.sh

Checks that `CHANGELOG.md` starts with `# Changelog`, that version entries use
the format `## [X.Y.Z] - YYYY-MM-DD`, and that each entry carries `**why:**`,
`**model:**`, and `**tags:**` metadata. Takes no arguments. Exits `1` and
prints each violation.

```bash
./scripts/validate-changelog.sh
```

### scripts/verify_codebase_sync.sh

Checks that every file path referenced in `CODEBASE.md` exists on disk. Takes
no arguments. Exits `1` and lists missing paths. Run it after any change that
adds, renames, or deletes files.

```bash
./scripts/verify_codebase_sync.sh
```

## Commit workflow

Use Conventional Commits: `<type>(<scope>): <summary>`.

- Summary line: 50 characters or fewer, imperative mood, no trailing period.
- Use `docs(sync):` for commits that update `BLUEPRINT.md` or `CODEBASE.md`.
- Synchronization commits must precede the final feature or fix commit.

## Documentation rules

- `README.md` — user documentation only: what the tool does and how to use it.
- `CONTRIBUTING.md` — developer guides, scripts, tooling, workflow.
- `BLUEPRINT.md` / `CODEBASE.md` — architecture and file mapping. Update them
  when system goals, hierarchy, state, or directory structure change, then run
  `./scripts/verify_codebase_sync.sh`.

## Generation tooling settings

> [!NOTE]
>
> Architecture (BLUEPRINT.md): Qwen 3.6 35B A3B
> - temp = 1.0, top-p = 0.95, top-k = 20, min-p = 0.0, presence-penalty = 1.5,
> repeat-penalty = 1.0
>
> Code: Qwen 3.6 35B A3B
> - temp = 0.6, top-p = 0.95, top-k = 20, min-p = 0.0, presence-penalty = 0.0,
> repeat-penalty = 1.0
