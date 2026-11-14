# The one failure line, the fault report row, and the cross-repo refusal.

typeset -g WT_FAULT_DIR_DEFAULT=/Users/matthias/frontier/docs/backlog/inbox/infra-faults

# wt_say <text>: one fixed line, `wt: <text>`, on stderr.
wt_say() {
  emulate -L zsh
  print -u2 -r -- "wt: $*"
}

_wt_cell() {
  emulate -L zsh
  local v=${1:--} cap=${2:-160}
  v=${v//|//}
  v=${v//$'\n'/ }
  print -r -- "${v[1,cap]}"
}

# wt_fault_row <key> <repo> <ticket> <verb> <detail>: one file per root cause and day,
# one row appended per occurrence. Prints the file path; prints nothing and returns 1 when
# the report cannot be written, which never stops the failing verb.
wt_fault_row() {
  emulate -L zsh
  local key=$1 dir=${WT_FAULT_REPORT_DIR:-$WT_FAULT_DIR_DEFAULT} day file row header
  day=$(date -u +%Y-%m-%d)
  file=$dir/$day-wt-$key.md
  row="| $(date -u +%Y-%m-%dT%H:%M:%SZ) | $(_wt_cell "$2") | $(_wt_cell "$3") | $(_wt_cell "$4") | $(_wt_cell "$5" 800) |"
  mkdir -p -- "$dir" 2>/dev/null || return 1
  header="# Infra fault - wt-$key - $day

Machine-appended by wt: one file per root-cause key per day, one row per occurrence. An
infrastructure fault in the worktree lifecycle, not an agent mistake.

| when (UTC) | repo | ticket | verb | detail |
|---|---|---|---|---|"
  # noclobber makes creation exclusive, so exactly one caller writes the header.
  ( set -o noclobber; print -r -- "$header" > "$file" ) 2>/dev/null
  print -r -- "$row" >> "$file" 2>/dev/null || return 1
  print -r -- "$file"
  return 0
}

# wt_fail <infra|flow> <key> <repo> <ticket> <verb> <what happened> [<next step>]
# Prints the fixed line and returns 1. infra: the row is the record, so the line says to
# file no ticket. flow: an agent-flow refusal that keeps its plain text and names the row.
wt_fail() {
  emulate -L zsh
  setopt extendedglob
  local kind=$1 key=$2 repo=$3 ticket=$4 verb=$5 remedy=$6 rerun=${7:-} row file msg
  row=$remedy
  [[ -n $rerun ]] && row+=" $rerun"
  file=$(wt_fault_row "$key" "$repo" "$ticket" "$verb" "$row")
  if [[ $kind == infra ]]; then
    msg="${remedy%%[. ]##}. Recorded in ${file:-(fault report unwritable)}. This is infrastructure, not a finding: file no ticket and write no retro"
    [[ -n $rerun ]] && msg+="; ${rerun%%.#}"
    msg+="."
  else
    msg=$row
    [[ -n $file ]] && msg+=" (reported: $file)"
  fi
  wt_say "$msg"
  return 1
}

# wt_guard <source repo> <target repo> <git subcommand> <ticket> <verb>: returns 1 with the
# refusal printed when the pairs file does not let source change target.
wt_guard() {
  emulate -L zsh
  local reason
  reason=$(/usr/bin/python3 -B "${WT_TOOLS}/lib/crossrepo.py" "$1" "$2" "$3") && return 0
  wt_fail flow crossrepo-refused "$2" "$4" "$5" "$reason"
}
