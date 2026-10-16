---
topic: "CODEBASE.md must use explicit paths, not globs"
importance: medium
category: warning
tags: [codebase, sync-script, glob-patterns]
created: 2026-10-16T14:33:23Z
model: kompis/qwen3.8-flash-next-iq3_s
---

`scripts/verify_codebase_sync.sh` checks every backtick path in CODEBASE.md
literally, so glob references like `tests/main_run_*.py` fail validation.
List each concrete file path in the Physical File Mapping table instead.
