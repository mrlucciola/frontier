# wt's calls to pm. pm runs from the store repo (that is how it finds an unregistered
# store); WT_CALLER=1 tells pm's own guards the call is wt's. $session is optional and
# reaches pm as PM_SESSION_ID for that call only.

# wt_pm <store> <session> <pm args...>
wt_pm() {
  emulate -L zsh
  local store=$1 session=$2
  shift 2
  local -a vars=(WT_CALLER=1)
  [[ -n $session ]] && vars+=(PM_SESSION_ID=$session)
  (
    builtin cd -q -- "$store" 2>/dev/null || { print -u2 -r -- "wt: cannot enter store $store"; exit 1 }
    exec env "${vars[@]}" pm "$@"
  )
}

wt_pm_get()  { emulate -L zsh; wt_pm "$1" "" get "$2" "$3" }                     # store id field
wt_pm_take() { emulate -L zsh; local s=$1 x=$2; shift 2; wt_pm "$s" "$x" take "$@" }  # store session id [args]
wt_pm_done() { emulate -L zsh; local s=$1 x=$2; shift 2; wt_pm "$s" "$x" done "$@" }
wt_pm_park() { emulate -L zsh; local s=$1 x=$2; shift 2; wt_pm "$s" "$x" park "$@" }
wt_pm_drop() { emulate -L zsh; local s=$1 x=$2; shift 2; wt_pm "$s" "$x" drop "$@" }
wt_pm_emit() { emulate -L zsh; local s=$1; shift; wt_pm "$s" "" emit "$@" }       # store id wt.name k=v

# A --store/--repo argument as its repo root. It must be a repo's own top level, never a
# subdirectory; a linked worktree maps to its main checkout.
wt_resolve_repo() {
  emulate -L zsh
  local path=${1/#\~/$HOME} option=$2 top
  path=${${path:A}}
  if [[ ! -d $path ]]; then
    print -u2 -r -- "wt: $option $1 is not a directory"
    return 1
  fi
  top=$(git -C "$path" rev-parse --show-toplevel 2>&1) || {
    print -u2 -r -- "wt: $option $1 is not inside a git repository (git rev-parse --show-toplevel: $top)"
    return 1
  }
  top=${top:A}
  if [[ $top != $path ]]; then
    print -u2 -r -- "wt: $option $1 is not a repo root, it resolves to $top. Pass that repo's own top-level directory, not a subdirectory of it."
    return 1
  fi
  wt_repo_root "$top"
}

# Sets WT_STORE (repo whose .pm holds the ticket) and WT_REPO (repo that gets the
# worktree and every git change). Store: --store, else `pm get <id> store`, else the cwd
# repo when pm cannot place the id. Repo: --repo, else the store.
# wt_resolve_repos <store option> <repo option> <ticket id> <cwd repo>
wt_resolve_repos() {
  emulate -L zsh
  local store_opt=$1 repo_opt=$2 id=$3 cwd_repo=$4 found
  typeset -g WT_STORE WT_REPO
  if [[ -n $store_opt ]]; then
    WT_STORE=$(wt_resolve_repo "$store_opt" --store) || return 1
  else
    found=$(wt_pm_get "$cwd_repo" "$id" store 2>/dev/null)
    if (( $? == 0 )) && [[ -n $found ]]; then
      WT_STORE=$(wt_resolve_repo "$found" "pm store") || return 1
    else
      WT_STORE=$cwd_repo
    fi
  fi
  if [[ -n $repo_opt ]]; then
    WT_REPO=$(wt_resolve_repo "$repo_opt" --repo) || return 1
  else
    WT_REPO=$WT_STORE
  fi
  return 0
}
