#!/usr/bin/env zsh
# Deploy cwf: links into this checkout and one marked block. Safe to run again.
here="${0:A:h}"
snippet="$here/instructions/opencode.AGENTS.md"
[[ -r "$snippet" ]] || { print -u2 "missing $snippet"; exit 1 }

# opencode: skills
dest="$HOME/.config/opencode/skills"
mkdir -p "$dest"
for d in "$here/skills"/cwf-*(/); do
	ln -sfn "$d" "$dest/${d:t}"
done

# command line
mkdir -p "$HOME/.local/bin"
ln -sfn "$here/cwf.py" "$HOME/.local/bin/cwf"

# opencode: instruction block
target="$HOME/.config/opencode/AGENTS.md"
begin='<!-- CWF:BEGIN -->' end='<!-- CWF:END -->' nl=$'\n'
block="$begin$nl$(<"$snippet")$nl$end"
text=""
[[ -f "$target" ]] && { text="$(cat "$target"; print -n x)"; text="${text%x}" }
if [[ "$text" == *"$begin"*"$end"* ]]; then
	text="${text%%"$begin"*}$block${text#*"$end"}"
else
	[[ -n "$text" && "$text" != *"$nl" ]] && text+="$nl"
	text+="${text:+$nl}$block$nl"
fi
mkdir -p "${target:h}"
print -rn -- "$text" >"$target"
