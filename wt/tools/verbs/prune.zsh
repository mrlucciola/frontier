# wt prune [--store PATH] [--repo PATH]
# Clears deferred-teardown registrations and the merged branches they leave behind.

wt_verb() {
  emulate -L zsh
  local store_opt="" repo_opt="" arg
  while (( $# )); do
    arg=$1
    case $arg in
      --store|--repo)
        if (( $# < 2 )); then
          wt_say "$arg needs a value. Re-run: wt prune $arg <value>"
          return 2
        fi
        if [[ $arg == --store ]]; then store_opt=$2; else repo_opt=$2; fi
        shift 2
        ;;
      *)
        wt_say "wt prune: unexpected argument $arg. Usage: wt prune [--store PATH] [--repo PATH]"
        return 2
        ;;
    esac
  done

  local cwd_repo repo default
  cwd_repo=$(wt_repo_root .) || return 1
  [[ -n $store_opt ]] || store_opt=$cwd_repo
  wt_resolve_repos "$store_opt" "$repo_opt" "" "$cwd_repo" || return 1
  repo=$WT_REPO
  default=$(wt_default_branch "$repo") || return 1
  wt_prune_debt "$repo" "$default" || return 1
  return 0
}
