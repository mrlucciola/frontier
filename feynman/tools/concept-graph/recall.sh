#!/usr/bin/env bash
# UserPromptSubmit hook for the concept graph (feynman skill).
# Fast path in shell: if no lexicon token appears in the payload, exit without
# starting python. On a hit, cg.py hook-recall verifies whole phrases against the
# prompt, applies scope and per-session dedup, and prints at most one JSON object.
# Always exit 0; never print anything but that object.
# Lives beside cg.py; linked at ~/.kiro/tools/concept-graph/ (feynman/INSTALL.md).
set -u

here="$(cd "$(dirname "$0")" && pwd)"
root="${CONCEPT_GRAPH_ROOT:-$HOME/.kiro/concepts}"
cg="${CONCEPT_GRAPH_CG:-$here/cg.py}"
py="${CONCEPT_GRAPH_PYTHON:-python3}"
lex="$root/lexicon.txt"

[ -s "$lex" ] || exit 0
[ -f "$cg" ] || exit 0

input="$(cat)"
[ -n "$input" ] || exit 0

if printf '%s' "$input" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9+#\n-' '\n' | grep -qxFf "$lex"; then
  printf '%s' "$input" | "$py" "$cg" hook-recall "$@" 2>/dev/null
fi
exit 0
