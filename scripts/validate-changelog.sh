#!/usr/bin/env bash
# validate-changelog.sh — Basic validation of CHANGELOG.md format.
#
# Usage:
#   ./scripts/validate-changelog.sh
#
# Exit codes:
#   0  Validation passed.
#   1  Validation failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CHANGELOG="$ROOT_DIR/CHANGELOG.md"

if [[ ! -f "$CHANGELOG" ]]; then
	echo "ERROR: $CHANGELOG not found." >&2
	exit 1
fi

ERRORS=0

# Check that the file starts with the Changelog heading
if ! head -1 "$CHANGELOG" | grep -q '^# Changelog'; then
	echo "ERROR: CHANGELOG.md must start with '# Changelog'." >&2
	ERRORS=1
fi

# Check that version entries have proper format: ## [X.Y.Z] - YYYY-MM-DD
MISSING_VERSION_FORMAT=$(grep -nP '^\#\# \[.*?\]' "$CHANGELOG" | grep -cvP '^\d+:## \[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}' || true)
if [[ "$MISSING_VERSION_FORMAT" -gt 0 ]]; then
	echo "ERROR: Version entry format must be '## [X.Y.Z] - YYYY-MM-DD'." >&2
	ERRORS=1
fi

# Check that each version entry has why, model, and tags metadata
# Split the file into blocks by version headers
awk '/^## \[/{n++} n{print > "/tmp/changelog_block_" n ".md"}' "$CHANGELOG"

for block in /tmp/changelog_block_*.md; do
	if [[ -f "$block" ]]; then
		if ! grep -q '\*\*why:\*\*' "$block"; then
			echo "ERROR: Version entry missing '**why:**' metadata." >&2
			ERRORS=1
		fi
		if ! grep -q '\*\*model:\*\*' "$block"; then
			echo "ERROR: Version entry missing '**model:**' metadata." >&2
			ERRORS=1
		fi
		if ! grep -q '\*\*tags:\*\*' "$block"; then
			echo "ERROR: Version entry missing '**tags:**' metadata." >&2
			ERRORS=1
		fi
		rm -f "$block"
	fi
done

if [[ $ERRORS -ne 0 ]]; then
	echo "Changelog validation failed." >&2
	exit 1
fi

echo "CHANGELOG.md format is valid."
exit 0
