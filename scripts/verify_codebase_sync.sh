#!/usr/bin/env bash
# verify_codebase_sync.sh — Validate that CODEBASE.md physical paths exist on disk.
#
# Usage:
#   ./scripts/verify_codebase_sync.sh
#
# Exit codes:
#   0  All paths in CODEBASE.md exist.
#   1  One or more paths are missing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CODEBASE="$ROOT_DIR/CODEBASE.md"

if [[ ! -f "$CODEBASE" ]]; then
	echo "ERROR: $CODEBASE not found."
	exit 1
fi

FOUND_ISSUES=0

# Collect all file paths from CODEBASE.md
# 1. Paths in backticks (from the Physical File Mapping table)
# 2. Paths in the directory tree (full paths like o2cfg/__init__.py)
extract_paths() {
	# Extract paths from backticks (full paths)
	grep -oP '`[^`]+\.(?:py|sh|toml|md|json|jsonc)`' "$CODEBASE" | tr -d '`'
	# Extract paths from tree lines (full paths with directory prefix)
	grep -oP '[a-zA-Z0-9_/-]+\.(?:py|sh|toml|md|json|jsonc)' "$CODEBASE" | sort -u
}

while IFS= read -r filepath; do
	# Skip empty lines
	[[ -z "$filepath" ]] && continue

	# Skip if it's just a filename without directory (e.g., "client.py" instead of "o2cfg/client.py")
	# These are false positives from the grep matching filenames in comments
	if [[ "$filepath" != */* ]]; then
		continue
	fi

	fullpath="$ROOT_DIR/$filepath"
	if [[ ! -e "$fullpath" ]]; then
		echo "MISSING: $filepath (expected at $fullpath)"
		FOUND_ISSUES=1
	fi
done < <(extract_paths | sort -u)

if [[ $FOUND_ISSUES -ne 0 ]]; then
	echo ""
	echo "CODEBASE.md contains references to files that do not exist on disk."
	exit 1
fi

echo "All paths in CODEBASE.md exist on disk."
exit 0
