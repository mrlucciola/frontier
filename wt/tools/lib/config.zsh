# wt's per-repo configuration: files under <repo>/.wt/, plus one pm store setting.

# wt_gate_find <store repo>: prints the gate's path and returns 0; returns 1 when the repo
# has no gate; prints a refusal and returns 2 when `.wt/gate` is not executable.
wt_gate_find() {
  emulate -L zsh
  local gate=$1/.wt/gate
  [[ -e $gate ]] || return 1
  if [[ ! -x $gate || -d $gate ]]; then
    print -u2 -r -- "wt: $gate is not executable, so wt cannot run the gate; fix it or pass --no-gate."
    return 2
  fi
  print -r -- "$gate"
  return 0
}

# Fills WT_RED_TICKETS and WT_RED_MATCH (index-aligned) from <repo>/.wt/known-red: one
# `<ticket id> <text to match>` per line, blank and `#` lines skipped.
wt_known_red() {
  emulate -L zsh
  setopt extendedglob
  local file=$1/.wt/known-red line id text
  typeset -ga WT_RED_TICKETS WT_RED_MATCH
  WT_RED_TICKETS=() WT_RED_MATCH=()
  [[ -f $file ]] || return 0
  while IFS= read -r line || [[ -n $line ]]; do
    line=${line##[[:space:]]#}
    [[ -z $line || $line == \#* ]] && continue
    id=${line%%[[:space:]]*}
    text=${line#$id}
    text=${text##[[:space:]]#}
    if [[ -z $text ]]; then
      print -u2 -r -- "wt: $file: '$line' needs '<ticket id> <text to match>'; fix that line."
      return 1
    fi
    WT_RED_TICKETS+=("$id") WT_RED_MATCH+=("$text")
  done < "$file"
  return 0
}

# True when the store's pm config requires --findings. Read by a helper because wt never
# parses JSON.
wt_findings_required() {
  emulate -L zsh
  /usr/bin/python3 -B "${WT_TOOLS}/lib/findings_required.py" "$1"
}
