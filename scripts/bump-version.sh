#!/usr/bin/env bash
# bump-version.sh — Bump the version in pyproject.toml.
#
# Usage:
#   ./scripts/bump-version.sh [patch|minor|major]
#
# Exit codes:
#   0  Version bumped successfully.
#   1  Invalid arguments or pyproject.toml not found.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYPROJECT="$ROOT_DIR/pyproject.toml"

if [[ ! -f "$PYPROJECT" ]]; then
	echo "ERROR: $PYPROJECT not found." >&2
	exit 1
fi

if [[ $# -ne 1 ]]; then
	echo "Usage: $0 [patch|minor|major]" >&2
	exit 1
fi

BUMP_TYPE="$1"

if [[ "$BUMP_TYPE" != "patch" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "major" ]]; then
	echo "ERROR: bump type must be patch, minor, or major." >&2
	exit 1
fi

# Extract current version
CURRENT=$(grep -oP '^version = "\K[^"]+' "$PYPROJECT")
IFS='.' read -r MAJOR MINOR PATCH <<<"$CURRENT"

case "$BUMP_TYPE" in
major)
	MAJOR=$((MAJOR + 1))
	MINOR=0
	PATCH=0
	;;
minor)
	MINOR=$((MINOR + 1))
	PATCH=0
	;;
patch)
	PATCH=$((PATCH + 1))
	;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"

# Update pyproject.toml
sed -i "s/^version = \"$CURRENT\"/version = \"$NEW_VERSION\"/" "$PYPROJECT"

echo "$CURRENT -> $NEW_VERSION"
