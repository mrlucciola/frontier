# wt status [--store PATH] [--repo PATH]
# Lists the worktrees of the repo joined against the tickets of the store.

wt_verb() {
  emulate -L zsh
  local store_opt="" repo_opt="" arg
  while (( $# )); do
    arg=$1
    case $arg in
      --store|--repo)
        if (( $# < 2 )); then
          wt_say "$arg needs a value. Re-run: wt status $arg <value>"
          return 2
        fi
        if [[ $arg == --store ]]; then store_opt=$2; else repo_opt=$2; fi
        shift 2
        ;;
      *)
        wt_say "wt status: unexpected argument $arg. Usage: wt status [--store PATH] [--repo PATH]"
        return 2
        ;;
    esac
  done

  local cwd_repo store repo
  cwd_repo=$(wt_repo_root .) || return 1
  [[ -n $store_opt ]] || store_opt=$cwd_repo
  wt_resolve_repos "$store_opt" "$repo_opt" "" "$cwd_repo" || return 1
  store=$WT_STORE repo=$WT_REPO

  wt_worktree_list "$repo" || return 1
  local -i i n=0
  local main_resolved=${repo:A} wt_path branch tstate rows=""
  for (( i = 1; i <= $#WT_WORKTREE_PATHS; i++ )); do
    wt_path=${WT_WORKTREE_PATHS[i]}
    [[ ${wt_path:A} == $main_resolved || -n ${WT_WORKTREE_BARE[i]} ]] && continue
    branch=${WT_WORKTREE_BRANCHES[i]:-(detached)}
    if [[ -n ${WT_WORKTREE_PRUNABLE[i]} ]]; then
      tstate="deferred-teardown -- directory gone, registration left by a sandboxed remove; wt prune clears it"
    elif [[ -z ${WT_WORKTREE_BRANCHES[i]} ]]; then
      tstate="FOREIGN/ORPHAN -- no ticket $branch in this store; not touched"
    else
      tstate=$(wt_pm_get "$store" "$branch" status 2>/dev/null)
      if (( $? != 0 )) || [[ -z $tstate ]]; then
        tstate="FOREIGN/ORPHAN -- no ticket $branch in this store; not touched"
      else
        tstate=${tstate##*$'\n'}
      fi
    fi
    print -r -- "$wt_path  $branch  $tstate"
    n+=1
  done
  (( n )) || print -r -- "no worktrees besides the main checkout"
  return 0
}
