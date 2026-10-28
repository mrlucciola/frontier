#!/usr/bin/env bash
# SessionStart hook: if the working directory is an ICM workspace, add one line
# of context so the agent runs `status` before doing anything else.
# Deployed to ~/.claude/hooks/icm-detect.sh; registered via settings.fragment.json.
set -u

is_icm=0
if [ -f CONTEXT.md ] && [ -d stages ]; then
  for d in stages/[0-9][0-9]-* stages/[0-9][0-9]_*; do
    [ -d "$d" ] && { is_icm=1; break; }
  done
fi
[ "$is_icm" -eq 1 ] || exit 0

entry="none"
[ -f AGENTS.md ] && entry="AGENTS.md"
[ -f CLAUDE.md ] && entry="CLAUDE.md"
[ -f AGENTS.md ] && [ -f CLAUDE.md ] && entry="AGENTS.md (CLAUDE.md also present; one should be a pointer)"

# Escape for JSON (backslash and double quote only; paths with other control chars are not expected).
dir="$(printf '%s' "$PWD" | sed 's/\\/\\\\/g; s/"/\\"/g')"
msg="ICM workspace detected at $dir. Entry file: $entry. Read it, then run status (icm-run skill) before acting. Load only what the current stage's Inputs table lists."

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$msg"
exit 0
