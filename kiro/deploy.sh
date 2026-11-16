#!/usr/bin/env zsh
# Deploy kiro: version-gated links into this checkout and one marked block. Safe to run again.
here="${0:A:h}"

# Version gate FIRST, before any write: this adapter is pinned to Kiro CLI 2.x.
command -v kiro-cli >/dev/null 2>&1 || { print -u2 "refusing: kiro-cli not on PATH; install Kiro CLI 2.x, verify with: kiro-cli --version"; exit 1 }
observed="$(kiro-cli --version 2>&1)"
major=""
[[ "$observed" =~ '([0-9]+\.[0-9]+)' ]] && major="${match[1]%%.*}"
[[ "$major" == "2" ]] || { print -u2 "refusing: Kiro CLI 2.x required; observed: ${observed:-no version output}"; exit 1 }

snippet="$here/instructions/kiro.steering.md"
[[ -r "$snippet" ]] || { print -u2 "missing $snippet"; exit 1 }

# command line
mkdir -p "$HOME/.local/bin"
ln -sfn "$here/cli/kiro-probe" "$HOME/.local/bin/kiro-probe"

# kiro: steering block
target="$HOME/.kiro/steering/frontier.md"
begin='<!-- KIRO:BEGIN -->' end='<!-- KIRO:END -->' nl=$'\n'
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
