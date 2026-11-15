# wt selftest
# Runs a short ticket lifecycle in a throwaway repo through the real wt and the new pm.
# Prints SELFTEST PASSED when wt is healthy on this machine.

typeset -gi WT_ST_FAILS=0

wt_st_ok() { emulate -L zsh; print -r -- "ok: $1" }
wt_st_fail() { emulate -L zsh; print -r -- "FAIL: $1: $2"; (( WT_ST_FAILS++ )) }

# wt_st_expect <case> <wanted> <got>
wt_st_expect() {
  emulate -L zsh
  if [[ $2 == $3 ]]; then wt_st_ok "$1"; else wt_st_fail "$1" "wanted '$2', got '$3'"; fi
  return 0
}

# wt_st_new <repo> <title>: files a ticket and prints its id.
wt_st_new() {
  emulate -L zsh
  local out
  out=$(builtin cd -q -- "$1" && pm new "$2" --new 2>&1) || { print -r -- "pm new failed: $out"; return 1 }
  print -r -- "${out##*$'\n'}"
}

wt_st_get() {
  emulate -L zsh
  (builtin cd -q -- "$1" && pm get "$2" "$3" 2>&1)
}

# wt_st_commit <worktree> <file> <message>
wt_st_commit() {
  emulate -L zsh
  print -r -- "$2" > "$1/$2" &&
    git -C "$1" add -- "$2" &&
    git -C "$1" commit -q -m "$3"
}

wt_st_run() {
  emulate -L zsh
  local repo=$1 wt=$WT_COMPONENT/cli/wt
  local id wtp out

  # start; finish
  id=$(wt_st_new "$repo" "case 1") || { wt_st_fail start "$id"; return 0 }
  wtp=$repo/.worktrees/$id
  out=$(builtin cd -q -- "$repo" && "$wt" start "$id" --as selftest 2>&1)
  [[ -d $wtp ]] || { wt_st_fail start "no worktree at $wtp: $out"; return 0 }
  wt_st_ok "start"
  wt_st_commit "$wtp" a.txt work
  out=$(builtin cd -q -- "$repo" && "$wt" finish "$id" 2>&1) || wt_st_fail finish "exit $?: $out"
  if [[ ! -e $wtp ]] && ! git -C "$repo" rev-parse --verify -q "refs/heads/$id" >/dev/null &&
     [[ -f $repo/a.txt ]]; then
    wt_st_ok "finish merged, worktree and branch gone"
  else
    wt_st_fail "finish merged, worktree and branch gone" "$out"
  fi
  wt_st_expect "finish closes the ticket" done "$(wt_st_get "$repo" "$id" status)"

  # start; park; resume; finish
  id=$(wt_st_new "$repo" "case 2") || { wt_st_fail park "$id"; return 0 }
  wtp=$repo/.worktrees/$id
  (builtin cd -q -- "$repo" && "$wt" start "$id" --as selftest >/dev/null 2>&1)
  wt_st_commit "$wtp" b.txt work
  out=$(builtin cd -q -- "$repo" && "$wt" park "$id" 2>&1) || wt_st_fail park "exit $?: $out"
  wt_st_expect "park marks the ticket parked" parked "$(wt_st_get "$repo" "$id" status)"
  if [[ ! -e $wtp ]] && git -C "$repo" rev-parse --verify -q "refs/heads/$id" >/dev/null; then
    wt_st_ok "park keeps the branch, removes the worktree"
  else
    wt_st_fail "park keeps the branch, removes the worktree" "$out"
  fi
  out=$(builtin cd -q -- "$repo" && "$wt" start "$id" --as selftest 2>&1)
  [[ -d $wtp ]] || { wt_st_fail "start resumes the parked ticket" "$out"; return 0 }
  wt_st_ok "start resumes the parked ticket"
  wt_st_commit "$wtp" c.txt more
  out=$(builtin cd -q -- "$repo" && "$wt" finish "$id" 2>&1) || wt_st_fail "resumed finish" "exit $?: $out"
  if [[ -f $repo/b.txt && -f $repo/c.txt && ! -e $wtp ]]; then
    wt_st_ok "resumed finish merges both commits"
  else
    wt_st_fail "resumed finish merges both commits" "$out"
  fi

  # zero-delta park
  id=$(wt_st_new "$repo" "case 3") || { wt_st_fail "zero-delta park" "$id"; return 0 }
  (builtin cd -q -- "$repo" && "$wt" start "$id" --as selftest >/dev/null 2>&1)
  out=$(builtin cd -q -- "$repo" && "$wt" park "$id" 2>&1) || wt_st_fail "zero-delta park" "exit $?: $out"
  wt_st_expect "zero-delta park releases the ticket" open "$(wt_st_get "$repo" "$id" status)"

  # land
  id=$(wt_st_new "$repo" "case 4") || { wt_st_fail land "$id"; return 0 }
  wtp=$repo/.worktrees/$id
  (builtin cd -q -- "$repo" && "$wt" start "$id" --as selftest >/dev/null 2>&1)
  wt_st_commit "$wtp" d.txt work
  out=$(builtin cd -q -- "$repo" && "$wt" land "$id" 2>&1) || wt_st_fail land "exit $?: $out"
  if [[ -f $repo/d.txt && ! -e $wtp ]]; then wt_st_ok "land merges and tears down"; else wt_st_fail "land merges and tears down" "$out"; fi
  wt_st_expect "land keeps the ticket taken" taken "$(wt_st_get "$repo" "$id" status)"

  # prune
  if out=$(builtin cd -q -- "$repo" && "$wt" prune 2>&1); then
    wt_st_ok "prune with nothing to do"
  else
    wt_st_fail prune "exit $?: $out"
  fi
  return 0
}

wt_verb() {
  emulate -L zsh
  if (( $# )); then
    wt_say "wt selftest takes no arguments, got $1. Usage: wt selftest"
    return 2
  fi

  local scratch repo pm_real
  scratch=$(mktemp -d "${TMPDIR:-/tmp}/wt-selftest-XXXXXX") || {
    print -r -- "SELFTEST FAILED: cannot create a scratch directory under ${TMPDIR:-/tmp}"
    return 1
  }
  repo=$scratch/repo
  mkdir -- "$repo" "$scratch/bin" "$scratch/plugins" "$scratch/faults" || {
    print -r -- "SELFTEST FAILED: cannot create directories in $scratch"
    return 1
  }

  pm_real=${WT_COMPONENT:h}/pm/cli/pm
  [[ -x $pm_real ]] || pm_real=${commands[pm]:-}
  if [[ -z $pm_real ]]; then
    rm -r -- "$scratch"
    print -r -- "SELFTEST FAILED: no pm found beside wt or on PATH"
    return 1
  fi
  ln -s -- "$pm_real" "$scratch/bin/pm"
  : > "$scratch/stores"

  export PATH=$scratch/bin:$PATH
  export PM_STORES=$scratch/stores PM_PLUGINS=$scratch/plugins
  export WT_FAULT_REPORT_DIR=$scratch/faults PM_TELEMETRY_DIR=-
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
  export GIT_AUTHOR_NAME=selftest GIT_AUTHOR_EMAIL=selftest@example.invalid
  export GIT_COMMITTER_NAME=selftest GIT_COMMITTER_EMAIL=selftest@example.invalid
  export PM_SESSION_ID=wt-selftest PM_AGENT=claude/worker
  unset WT_ACTOR PM_ACTOR CLAUDE_CODE_SESSION_ID CODEX_THREAD_ID

  if ! git init -q -b main "$repo" >/dev/null 2>&1; then
    rm -r -- "$scratch"
    print -r -- "SELFTEST FAILED: git init refused in $repo"
    return 1
  fi
  print -r -- seed > "$repo/README.md"
  git -C "$repo" add -- README.md &&
    git -C "$repo" commit -q -m seed &&
    (builtin cd -q -- "$repo" && pm init wtst >/dev/null 2>&1) &&
    git -C "$repo" add -- .gitignore .pm/config.json &&
    git -C "$repo" commit -q -m store || {
      rm -r -- "$scratch"
      print -r -- "SELFTEST FAILED: could not prepare the scratch repo in $repo"
      return 1
    }

  wt_st_run "$repo"

  rm -r -- "$scratch"
  if (( WT_ST_FAILS )); then
    print -r -- "SELFTEST FAILED: $WT_ST_FAILS case(s)"
    return 1
  fi
  print -r -- "SELFTEST PASSED"
  return 0
}
