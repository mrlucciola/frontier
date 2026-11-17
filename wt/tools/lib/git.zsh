# Git facts every verb needs. Functions print their answer; a failure prints its own
# `wt:` line and returns 1.

# Main checkout of the repository containing $1 (a linked worktree maps to its main checkout).
wt_repo_root() {
  emulate -L zsh
  local top common err
  top=$(git -C "${1:-.}" rev-parse --show-toplevel 2>/dev/null) || {
    err=$(git -C "${1:-.}" rev-parse --show-toplevel 2>&1)
    print -u2 -r -- "wt: not inside a git repository (git rev-parse --show-toplevel: $err)"
    return 1
  }
  top=${top:A}
  common=$(git -C "$top" rev-parse --git-common-dir 2>/dev/null) || { print -r -- "$top"; return 0 }
  [[ $common == /* ]] || common=$top/$common
  common=${common:A}
  if [[ ${common:t} == .git ]]; then
    print -r -- "${common:h}"
  else
    print -r -- "$top"
  fi
  return 0
}

wt_default_branch() {
  emulate -L zsh
  local branch err
  branch=$(git -C "$1" branch --show-current 2>/dev/null)
  if (( $? != 0 )) || [[ -z $branch ]]; then
    err=$(git -C "$1" branch --show-current 2>&1)
    print -u2 -r -- "wt: could not determine the default branch of $1 (main checkout must stay on a named branch, never detached HEAD): $err. Check out the default branch in $1, then re-run."
    return 1
  fi
  print -r -- "$branch"
  return 0
}

wt_worktree_path() {
  emulate -L zsh
  print -r -- "$1/.wt/$2"
  return 0
}

wt_branch_exists() {
  emulate -L zsh
  git -C "$1" show-ref --verify --quiet "refs/heads/$2"
}

# Fills four index-aligned arrays: WT_WORKTREE_PATHS, WT_WORKTREE_BRANCHES (empty when
# detached), WT_WORKTREE_PRUNABLE (git's reason, empty when not prunable), WT_WORKTREE_BARE
# (1 for a bare entry, else empty).
wt_worktree_list() {
  emulate -L zsh
  local out line
  typeset -ga WT_WORKTREE_PATHS WT_WORKTREE_BRANCHES WT_WORKTREE_PRUNABLE WT_WORKTREE_BARE
  WT_WORKTREE_PATHS=() WT_WORKTREE_BRANCHES=() WT_WORKTREE_PRUNABLE=() WT_WORKTREE_BARE=()
  out=$(git -C "$1" worktree list --porcelain 2>/dev/null) || {
    out=$(git -C "$1" worktree list --porcelain 2>&1)
    print -u2 -r -- "wt: git worktree list failed: $out"
    return 1
  }
  for line in "${(@f)out}"; do
    case $line in
      "worktree "*) WT_WORKTREE_PATHS+=("${line#worktree }") WT_WORKTREE_BRANCHES+=("") WT_WORKTREE_PRUNABLE+=("") WT_WORKTREE_BARE+=("") ;;
      bare) WT_WORKTREE_BARE[-1]=1 ;;
      "branch "*) WT_WORKTREE_BRANCHES[-1]=${line#branch refs/heads/} ;;
      prunable*) WT_WORKTREE_PRUNABLE[-1]=${${line#prunable}# }; [[ -n ${WT_WORKTREE_PRUNABLE[-1]} ]] || WT_WORKTREE_PRUNABLE[-1]=prunable ;;
    esac
  done
  return 0
}

# True when $2 is an ancestor of (or equal to) $3 in repo $1.
wt_is_ancestor() {
  emulate -L zsh
  git -C "$1" merge-base --is-ancestor "$2" "$3" 2>/dev/null
}
