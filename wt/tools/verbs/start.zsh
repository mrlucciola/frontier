# wt start <id> [--as NAME] [--session ID] [--store PATH] [--repo PATH] [--force]
# Claims the ticket through pm (or adopts the caller's own claim) and adds or resumes the
# worktree at <repo>/.worktrees/<id> on branch <id>.

wt_verb() {
  emulate -L zsh
  local id="" actor=${WT_ACTOR:-} session=${PM_SESSION_ID:-${CODEX_THREAD_ID:-}}
  local store_opt="" repo_opt="" arg
  local -i force=0
  while (( $# )); do
    arg=$1
    case $arg in
      --as|--session|--store|--repo)
        if (( $# < 2 )); then
          wt_say "$arg needs a value. Re-run: wt start <id> $arg <value>"
          return 2
        fi
        case $arg in
          --as) actor=$2 ;;
          --session) session=$2 ;;
          --store) store_opt=$2 ;;
          --repo) repo_opt=$2 ;;
        esac
        shift 2
        ;;
      --force) force=1; shift ;;
      -*)
        wt_say "wt start: unknown option $arg. Usage: wt start <id> [--as NAME] [--session ID] [--store PATH] [--repo PATH] [--force]"
        return 2
        ;;
      *)
        if [[ -n $id ]]; then
          wt_say "wt start takes one ticket id, got a second argument '$arg'. Usage: wt start <id> [--as NAME] ..."
          return 2
        fi
        id=$arg
        shift
        ;;
    esac
  done
  if [[ -z $id ]]; then
    wt_say "wt start needs a ticket id. Usage: wt start <id> [--as NAME] [--session ID] [--store PATH] [--repo PATH] [--force]"
    return 2
  fi

  local cwd_repo store repo
  cwd_repo=$(wt_repo_root .) || return 1
  wt_resolve_repos "$store_opt" "$repo_opt" "$id" "$cwd_repo" || return 1
  store=$WT_STORE repo=$WT_REPO
  if [[ -z $actor ]]; then
    wt_say "wt start requires --as <name> (or \$WT_ACTOR): pm take needs an actor name. Re-run: wt start $id --as <name>"
    return 1
  fi

  if [[ ${store:A} != ${cwd_repo:A} ]]; then
    wt_guard "$cwd_repo" "$store" commit "$id" start || return 1
  fi
  wt_guard "$cwd_repo" "$repo" worktree "$id" start || return 1

  local wip wip_sha wip_n
  if wt_branch_exists "$repo" "$id"; then
    wip=$(wt_wip_tip "$repo" "$id")
    if [[ -n $wip ]]; then
      wip_sha=${wip%% *} wip_n=${wip##* }
      if (( wip_n > 50 )); then
        wt_fail flow start-resume-mass-deletion "$repo" "$id" start \
          "refusing to resume $id: its tip $wip_sha is a wt WIP park commit that only deletes $wip_n files (a failed worktree remove left a partial tree and park committed it). Nothing was claimed or created. Do not retry with the sandbox disabled; tell the operator to inspect \`git -C $repo show --stat $wip_sha\` and, if the deletion is bogus, drop that commit from branch $id"
        return 1
      fi
    fi
  fi

  local status holder sid tok="" mine="" took=0 out rc
  status=$(wt_pm_get "$store" "$id" status 2>/dev/null)
  holder=$(wt_pm_get "$store" "$id" holder 2>/dev/null)
  sid=${session:-${CLAUDE_CODE_SESSION_ID:-}}
  if [[ -n $sid ]]; then
    tok=$(print -rn -- "$sid" | /usr/bin/shasum -a 256)
    tok=${tok[1,8]}
    mine="$actor#$tok"
  fi
  if [[ $status == taken && -n $mine && $holder == "$mine" ]]; then
    print -r -- "adopting existing claim on $id: $holder (same session)"
  else
    local -a take_args=(take "$id" --as "$actor")
    (( force )) && take_args+=(--force)
    out=$(wt_pm "$store" "$session" "${take_args[@]}" 2>&1)
    rc=$?
    if (( rc != 0 )); then
      wt_say "ticket $id is not claimable (taken, or pm refused): ${out}. Pick another ticket with \`pm ls ready\`, or ask the holder."
      return 1
    fi
    took=1
    if (( force )); then
      print -r -- "forced claim on $id: end this ticket with \`wt park\`, never \`wt finish\`"
    fi
  fi

  local default wt_path resume=0 add_err hint
  default=$(wt_default_branch "$repo") || { _wt_start_undo "$store" "$session" "$id" "$took" "$status"; return 1 }
  wt_path=$(wt_worktree_path "$repo" "$id")

  wt_prune_debt "$repo" "$default" quiet >/dev/null 2>&1

  wt_branch_exists "$repo" "$id" && resume=1
  if (( resume )); then
    add_err=$(git -C "$repo" worktree add "$wt_path" "$id" 2>&1)
  else
    add_err=$(git -C "$repo" worktree add -b "$id" "$wt_path" 2>&1)
  fi
  if (( $? != 0 )); then
    add_err=${add_err//$'\n'/ }
    hint=""
    if [[ $add_err == *".git/worktrees"* && $add_err == *"Operation not permitted"* ]]; then
      hint=" The worktrees admin directory was deleted during this session (git removes it when the last admin dir goes) and the sandbox denies recreating it; restart or resume the session."
    fi
    if [[ $add_err == *"missing but already registered worktree"* ]]; then
      hint+=" A deferred-teardown registration for $id is still present and this session cannot delete it; run wt prune from a new session, then wt start."
    fi
    _wt_start_undo "$store" "$session" "$id" "$took" "$status"
    if (( resume )); then
      wt_fail flow start-worktree-add-failed "$repo" "$id" start \
        "git worktree add for $id failed: $add_err.$hint" \
        "re-run \`git -C $repo worktree add $wt_path $id\` by hand after inspecting the error"
    else
      wt_fail flow start-worktree-add-failed "$repo" "$id" start \
        "git worktree add for $id failed: $add_err.$hint" \
        "re-run \`git -C $repo worktree add -b $id $wt_path\` by hand after inspecting the error"
    fi
    return 1
  fi

  if (( resume )); then
    if ! git -C "$wt_path" rebase "$default" >/dev/null 2>&1; then
      git -C "$wt_path" rebase --abort >/dev/null 2>&1
      wt_worktree_remove "$repo" "$wt_path" >/dev/null 2>&1
      wt_pm "$store" "$session" park "$id" -m "resume of $id: rebase onto $default conflicted; worktree removed, branch $id kept" >/dev/null 2>&1
      wt_fail flow start-resume-rebase-conflict "$repo" "$id" start \
        "resuming $id: rebase onto $default conflicted; worktree removed again, branch $id kept" \
        "resolve by hand: git -C $repo worktree add $wt_path $id && git -C $wt_path rebase $default"
      return 1
    fi
  fi

  wt_pm "$store" "$session" emit "$id" wt.start "branch=$id" "path=$wt_path" >/dev/null 2>&1
  print -r -- "OK: $id -> $wt_path"
  return 0
}

# _wt_start_undo <store> <session> <id> <took> <status before>: gives back a claim this
# start took; a ticket that was parked goes back to parked, anything else to open.
_wt_start_undo() {
  emulate -L zsh
  (( ${4:-0} )) || return 0
  if [[ $5 == parked ]]; then
    wt_pm "$1" "$2" park "$3" -m "wt start could not add the worktree; parked again" >/dev/null 2>&1
  else
    wt_pm "$1" "$2" drop "$3" >/dev/null 2>&1
  fi
  return 0
}
