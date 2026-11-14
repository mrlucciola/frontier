# wt's calls to pm. pm runs from the store repo (that is how it finds an unregistered
# store); WT_CALLER=1 tells pm's own guards the call is wt's. $session is optional and
# reaches pm as PM_SESSION_ID for that call only.

# wt_pm <store> <session> <pm args...>: verbs call this directly (take, done, park, drop,
# emit). Returns 127 with a `wt:` line when pm is not on PATH.
wt_pm() {
  emulate -L zsh
  local store=$1 session=$2
  shift 2
  (( $+commands[pm] )) || {
    print -u2 -r -- "wt: could not run \`pm $*\`: pm is not on PATH; put pm on PATH and re-run."
    return 127
  }
  local -a vars=(WT_CALLER=1)
  [[ -n $session ]] && vars+=(PM_SESSION_ID=$session)
  (
    builtin cd -q -- "$store" 2>/dev/null || { print -u2 -r -- "wt: cannot enter store $store; check that the directory exists and is readable, then re-run."; exit 1 }
    exec env "${vars[@]}" pm "$@"
  )
}

wt_pm_get() { emulate -L zsh; wt_pm "$1" "" get "$2" "$3" }                     # store id field

# True when the store's pm config requires --findings (finish and park). Read by a helper
# because wt never parses JSON.
wt_findings_required() {
  emulate -L zsh
  /usr/bin/python3 -B "${WT_TOOLS}/lib/findings_required.py" "$1"
}

# Sets WT_STORE (repo whose .pm holds the ticket) and WT_REPO (repo that gets the
# worktree and every git change). Store: --store, else `pm get <id> store`, else the cwd
# repo when pm cannot place the id. Repo: --repo, else the store. A --store/--repo argument
# must be a repo's own top level, never a subdirectory; a linked worktree maps to its main
# checkout.
# wt_resolve_repos <store option> <repo option> <ticket id> <cwd repo>
wt_resolve_repos() {
  emulate -L zsh
  local store_opt=$1 repo_opt=$2 id=$3 cwd_repo=$4 found rc raw label kind abspath top err resolved
  local -a kinds raws labels
  typeset -g WT_STORE WT_REPO
  if [[ -n $store_opt ]]; then
    kinds+=(store) raws+=("$store_opt") labels+=(--store)
  else
    found=$(wt_pm_get "$cwd_repo" "$id" store 2>&1)
    rc=$?
    if (( rc == 0 )) && [[ -n $found ]]; then
      kinds+=(store) raws+=("${found##*$'\n'}") labels+=("pm store")
    elif (( rc == 127 )); then
      print -u2 -r -- "$found"
      return 1
    elif (( rc == 1 )) && [[ $found == "pm: no store has prefix"* || $found == "pm: no ticket "* ]]; then
      WT_STORE=$cwd_repo
    else
      print -u2 -r -- "wt: \`pm get $id store\` failed (exit $rc): $found. Fix that pm error, or pass --store <ticket repo>, then re-run."
      return 1
    fi
  fi
  [[ -n $repo_opt ]] && kinds+=(repo) raws+=("$repo_opt") labels+=(--repo)
  local -i i
  for (( i = 1; i <= $#kinds; i++ )); do
    kind=${kinds[i]} raw=${raws[i]} label=${labels[i]}
    abspath=${raw/#\~/$HOME}
    abspath=${abspath:A}
    if [[ ! -d $abspath ]]; then
      print -u2 -r -- "wt: $label $raw is not a directory. Pass an existing repo path with $label, then re-run."
      return 1
    fi
    top=$(git -C "$abspath" rev-parse --show-toplevel 2>/dev/null) || {
      err=$(git -C "$abspath" rev-parse --show-toplevel 2>&1)
      print -u2 -r -- "wt: $label $raw is not inside a git repository (git rev-parse --show-toplevel: $err)"
      return 1
    }
    top=${top:A}
    if [[ $top != $abspath ]]; then
      print -u2 -r -- "wt: $label $raw is not a repo root -- it resolves to $top. Pass that repo's own top-level directory, not a subdirectory of it."
      return 1
    fi
    resolved=$(wt_repo_root "$top") || return 1
    if [[ $kind == store ]]; then WT_STORE=$resolved; else WT_REPO=$resolved; fi
  done
  [[ -n $repo_opt ]] || WT_REPO=$WT_STORE
  return 0
}
