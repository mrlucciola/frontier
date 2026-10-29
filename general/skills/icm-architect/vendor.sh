#!/usr/bin/env bash
# Vendor RinDig/icm-architect into this folder at a pinned commit, then commit the result.
# Usage: bash vendor.sh                              (uses ICM_ARCHITECT_COMMIT below)
#        ICM_ARCHITECT_COMMIT=<ref> bash vendor.sh   (first pull or a bump; then paste the
#                                                     printed SHA into the pin below)
set -euo pipefail

PIN=""   # full 40-hex SHA; empty until the first pull
REPO="https://github.com/RinDig/icm-architect"
HERE="$(cd "$(dirname "$0")" && pwd)"

ref="${ICM_ARCHITECT_COMMIT:-$PIN}"
if [ -z "$ref" ]; then
  echo "no pin set: run ICM_ARCHITECT_COMMIT=main bash vendor.sh once, then paste the SHA into PIN" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --quiet "$REPO" "$TMP/src"
git -C "$TMP/src" checkout --quiet "$ref"
SHA="$(git -C "$TMP/src" rev-parse HEAD)"

# Keep only what the skill needs at runtime, plus LICENSE (MIT requires it).
# VENDOR.md, VENDOR.lock and this script stay.
for f in SKILL.md LICENSE references assets scripts; do
  rm -rf "$HERE/$f"
  [ -e "$TMP/src/$f" ] && cp -R "$TMP/src/$f" "$HERE/$f"
done

printf 'upstream=%s\ncommit=%s\nvendored=%s\n' "$REPO" "$SHA" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$HERE/VENDOR.lock"
echo "vendored icm-architect @ $SHA"
if [ "$SHA" != "$PIN" ]; then
  echo "PIN in $0 is '${PIN:-unset}'; set it to $SHA and commit the vendored tree with it" >&2
fi
