#!/usr/bin/env bash
# Vendor RinDig/icm-architect into this folder at a pinned commit.
# Usage: bash vendor.sh            (uses ICM_ARCHITECT_COMMIT below)
#        ICM_ARCHITECT_COMMIT=<sha> bash vendor.sh
set -euo pipefail

ICM_ARCHITECT_COMMIT="${ICM_ARCHITECT_COMMIT:-main}"   # replace 'main' with a full SHA before first deploy
REPO="https://github.com/RinDig/icm-architect"
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --quiet "$REPO" "$TMP/src"
git -C "$TMP/src" checkout --quiet "$ICM_ARCHITECT_COMMIT"
SHA="$(git -C "$TMP/src" rev-parse HEAD)"

# Keep only what the skill needs at runtime. VENDOR.md and this script stay.
for f in SKILL.md README.md LICENSE references assets scripts; do
  rm -rf "$HERE/$f"
  [ -e "$TMP/src/$f" ] && cp -R "$TMP/src/$f" "$HERE/$f"
done

printf 'upstream=%s\ncommit=%s\nvendored=%s\n' "$REPO" "$SHA" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$HERE/VENDOR.lock"
echo "vendored icm-architect @ $SHA"
