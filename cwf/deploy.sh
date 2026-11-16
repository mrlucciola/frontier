#!/usr/bin/env zsh

SKILLS_DIR_OPENCODE="$HOME/.config/opencode/skills"
CWF_DIR="$HOME/projects/frontier-clean/cwf"

mkdir -p "$SKILLS_DIR_OPENCODE"

# Activate the skills
for d in "$CWF_DIR/skills"/cwf-*(/); do
	ln -sfn "$d" "$SKILLS_DIR_OPENCODE/${d:t}"
done
ls -l "$SKILLS_DIR_OPENCODE"

# Activate the CLI
chmod +x "$CWF_DIR/cwf.py"
ln -sf "$CWF_DIR/cwf.py" "$HOME/.local/bin/cwf"
"$HOME/.local/bin/cwf" version

# Activate/Apply the instruction snippet. This should only ever modify the text between <!-- CWF:BEGIN --> and <!-- CWF:END -->.
AGENTS_OPENCODE="$HOME/.config/opencode/AGENTS.md"
begin='<!-- CWF:BEGIN -->' end='<!-- CWF:END -->' nl=$'\n'

# Validate file exists:
[[ -r "$CWF_DIR/instructions/opencode.AGENTS.md" ]] || { print -u2 "missing instructions/opencode.AGENTS.md"; exit 1 }

block="$begin$nl$(<"$CWF_DIR/instructions/opencode.AGENTS.md")$nl$end"
text=""
[[ -f "$AGENTS_OPENCODE" ]] && text="$(<"$AGENTS_OPENCODE")"
if [[ "$text" == *"$begin"*"$end"* ]]; then
	text="${text%%"$begin"*}$block${text#*"$end"}"
else
	text="${text:+$text$nl$nl}$block"
fi
mkdir -p "${AGENTS_OPENCODE:h}"
print -r -- "$text" >"$AGENTS_OPENCODE"
