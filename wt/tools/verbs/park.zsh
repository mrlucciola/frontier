# wt park <id> [--waits-on <id-or-note>] [--note TEXT] [--findings VALUE] [--auto]
#   [--session ID] [--store PATH] [--repo PATH]
# Commits WIP, parks the ticket through pm (or drops it when the branch holds nothing),
# removes the worktree and keeps the branch. Use it when work must wait: a blocker, a
# conflict you must not resolve alone, another session's dirty file.
# The worktree directory is gone at once by design; wt status will not list it, pm ls
# parked does. Do not recreate it. Resume with wt start <id>.
# A non-empty <worktree>/.local blocks the park: that is operator content, report it.
# --note is prepended to the resume note. --auto is finish's interface (not for you).

# --auto: only the note on stdout, no OK line, findings default to none.

wt_verb() {
  emulate -L zsh
  local id="" waits_on="" note="" findings="" session_opt="" store_opt="" repo_opt="" arg
  local -i auto=0 have_findings=0
  while (( $# )); do
    arg=$1
    case $arg in
      --waits-on|--note|--findings|--session|--store|--repo)
        if (( $# < 2 )); then
          wt_say "$arg needs a value. Re-run: wt park <id> $arg <value>"
          return 2
        fi
        case $arg in
          --waits-on) waits_on=$2 ;;
          --note) note=$2 ;;
          --findings) findings=$2 have_findings=1 ;;
          --session) session_opt=$2 ;;
          --store) store_opt=$2 ;;
          --repo) repo_opt=$2 ;;
        esac
        shift 2
        ;;
      --auto) auto=1; shift ;;
      -*)
        wt_say "wt park: unknown option $arg. Usage: wt park <id> [--waits-on <id-or-note>] [--note TEXT] [--findings VALUE] [--session ID] [--store PATH] [--repo PATH]"
        return 2
        ;;
      *)
        if [[ -n $id ]]; then
          wt_say "wt park takes one ticket id, got a second argument '$arg'. Usage: wt park <id> [--waits-on <id-or-note>] ..."
          return 2
        fi
        id=$arg
        shift
        ;;
    esac
  done
  if [[ -z $id ]]; then
    wt_say "wt park needs a ticket id. Usage: wt park <id> [--waits-on <id-or-note>] [--note TEXT] [--findings VALUE]"
    return 2
  fi

  local env_session=${PM_SESSION_ID:-}
  # The environment wins for pm calls: ParkTest.test_waits_on_note_and_session_in_resume_line
  # passes --session for the resume line only, while pm must keep acting as the holder.
  local pm_session=${env_session:-$session_opt}
  local resume_session=${session_opt:-$env_session}

  local cwd_repo store repo default wt_path
  cwd_repo=$(wt_repo_root .) || return 1
  wt_resolve_repos "$store_opt" "$repo_opt" "$id" "$cwd_repo" || return 1
  store=$WT_STORE repo=$WT_REPO
  default=$(wt_default_branch "$repo") || return 1
  wt_path=$(wt_worktree_path "$repo" "$id")

  local -i registered=0 i
  wt_worktree_list "$repo" || return 1
  for (( i = 1; i <= $#WT_WORKTREE_PATHS; i++ )); do
    [[ ${WT_WORKTREE_PATHS[i]:A} == ${wt_path:A} ]] && registered=1
  done
  if (( ! registered )); then
    wt_say "no worktree at $wt_path for $id -- nothing to park. Run \`wt status\` to list worktrees, or \`wt start $id\` to make one."
    return 1
  fi

  local route
  wt_merged_route "$repo" "$default" "$wt_path" "$id" park
  route=$?
  if (( route == 2 )); then
    return 1
  elif (( route == 0 )); then
    _wt_park_merged "$repo" "$store" "$cwd_repo" "$default" "$wt_path" "$id" "$pm_session" \
      "$note" "$findings" $have_findings $auto
    return $?
  fi

  local -a local_files=("$wt_path"/.local/*(DN))
  if (( $#local_files )); then
    wt_say "$wt_path/.local is non-empty -- park refuses to remove a worktree carrying local state. Clear it (or move what matters out) and re-run \`wt park $id\`."
    return 1
  fi

  if [[ ${store:A} != ${cwd_repo:A} ]]; then
    wt_guard "$cwd_repo" "$store" commit "$id" park || return 1
  fi
  wt_guard "$cwd_repo" "$repo" commit "$id" park || return 1

  wt_refuse_undeletable "$wt_path" "$id" "committed or removed" park || return 1

  local porcelain delta
  porcelain=$(git -C "$wt_path" status --porcelain 2>/dev/null)
  delta=$(git -C "$repo" log --oneline "$default..$id" 2>/dev/null)
  if (( auto )); then
    if (( ! have_findings )) && wt_findings_required "$store"; then
      findings=none have_findings=1
    fi
  elif [[ -n $porcelain || -n $delta ]]; then
    _wt_park_check_findings "$store" "$id" "$note" "$findings" $have_findings || return 1
  fi

  if [[ -n $porcelain ]]; then
    local ln first=""
    local -i nlines=0 ndel=0
    for ln in "${(@f)porcelain}"; do
      [[ -n ${ln//[[:space:]]/} ]] || continue
      nlines+=1
      if [[ ${ln[1,2]} == *D* && ${ln[1,2]} != '??' ]]; then
        ndel+=1
        [[ -n $first ]] || first=${ln[4,-1]}
      fi
    done
    if (( ndel > WT_MASS_DELETE_MIN && ndel == nlines )); then
      wt_fail flow park-mass-deletion-refused "$repo" "$id" park \
        "refusing to park $id: the worktree is $ndel deletions and nothing else (e.g. $first) -- the signature of a partial tree left by a failed worktree remove, which WIP-committing would record as a mass deletion on the branch. Nothing was committed. Do not retry with the sandbox disabled; tell the operator to inspect \`git -C $wt_path status\` and either restore the files (\`git -C $wt_path checkout -- .\`) or remove the worktree by hand"
      return 1
    fi
    git -C "$wt_path" add -A >/dev/null 2>&1
    local commit_out
    commit_out=$(git -C "$wt_path" commit -m "WIP: park $id" 2>&1)
    if (( $? != 0 )); then
      wt_fail infra park-wip-commit-failed "$repo" "$id" park "committing WIP for $id failed: ${commit_out//$'\n'/ }"
      return 1
    fi
  fi

  local out rc
  delta=$(git -C "$repo" log --oneline "$default..$id" 2>/dev/null)
  if (( $? == 0 )) && [[ -z $delta ]]; then
    _wt_park_zero_delta "$repo" "$store" "$wt_path" "$id" "$pm_session" "$waits_on" \
      "$note" "$findings" $auto
    return $?
  fi

  local tip_sha holder actor
  tip_sha=$(git -C "$wt_path" rev-parse HEAD 2>/dev/null) || tip_sha="(unknown)"
  holder=$(wt_pm_get "$store" "$id" holder 2>/dev/null)
  actor=${${holder%%#*}##*[:/]}
  [[ -n $actor ]] && export PM_ACTOR=$actor # pm park acts as the holder, not the shell's actor
  local resume="wt start $id"
  [[ -n $actor ]] && resume+=" --as $actor"
  [[ -n $resume_session ]] && resume+=" --session $resume_session"
  [[ -n $store_opt ]] && resume+=" --store $store_opt"
  [[ -n $repo_opt ]] && resume+=" --repo $repo_opt"
  resume+=" && wt finish $id"
  [[ -n $store_opt ]] && resume+=" --store $store_opt"
  [[ -n $repo_opt ]] && resume+=" --repo $repo_opt"

  local parked="branch $id @ $tip_sha; waits-on ${waits_on:-(none)}; resume: $resume"
  (( auto )) && parked+="; auto-parked by an infrastructure fault, not a finding: file no ticket"
  [[ -n $note ]] && parked="$note; $parked"

  out=$(wt_pm "$store" "$pm_session" park "$id" -m "$parked" 2>&1)
  if (( $? != 0 )); then
    wt_fail infra park-ticket-close-failed "$repo" "$id" park "pm park for $id failed: ${out//$'\n'/ }"
    return 1
  fi
  if (( have_findings )); then
    wt_pm "$store" "$pm_session" emit "$id" wt.park "sha=$tip_sha" "findings=$findings" >/dev/null 2>&1
  else
    wt_pm "$store" "$pm_session" emit "$id" wt.park "sha=$tip_sha" >/dev/null 2>&1
  fi

  if ! wt_worktree_remove "$repo" "$wt_path"; then
    local -a steps=("${(@f)$(wt_cleanup_steps "$repo" "$wt_path")}")
    wt_stop_remove_failed park-worktree-remove-failed "$repo" "$id" park \
      "parked $id but \`git -C $repo worktree remove $wt_path\` failed" \
      "${steps[@]}" "keep branch $id"
    return 1
  fi
  (( WT_REMOVE_DEFERRED )) && wt_deferred_line park-teardown-deferred "$repo" "$id" park "$wt_path" 0

  _wt_park_record_wait "$repo" "$store" "$pm_session" "$id" "$waits_on"

  if (( auto )); then
    print -r -- "$parked"
  else
    print -r -- "OK: $id parked -- $parked"
  fi
  return 0
}

# _wt_park_check_findings <store> <id> <note> <findings> <given 0|1>: warns when findings
# are missing, refuses before anything changes when the store requires them.
_wt_park_check_findings() {
  emulate -L zsh
  local store=$1 id=$2 note=$3 findings=$4 given=$5 text
  text="no --findings: this close attests nothing about what was not done, not proven, or found elsewhere; pass --findings none or the ids"
  if (( ! given )); then
    if wt_findings_required "$store"; then
      wt_say "$text. Nothing was merged or removed; re-run \`wt park $id --findings <none|ids>\`."
      return 1
    fi
    wt_say "$text"
  elif [[ ${findings//[[:space:]]/} == none ]] && wt_findings_required "$store" \
       && [[ -z ${note//[[:space:]]/} ]] && ! _wt_park_has_note "$store" "$id"; then
    wt_say "--findings none needs a non-empty --note or an existing ticket note: 'none' is a statement, not a default. Nothing was merged or removed; re-run \`wt park $id --findings none --note <text>\`."
    return 1
  fi
  return 0
}

# True when `pm show` prints a notes heading (design.md "Output").
_wt_park_has_note() {
  emulate -L zsh
  local shown ln
  shown=$(wt_pm "$1" "" show "$2" 2>/dev/null) || return 1
  for ln in "${(@f)shown}"; do
    [[ $ln == "notes:"* || $ln == "notes (last"* ]] && return 0
  done
  return 1
}

# _wt_park_record_wait <repo> <store> <session> <id> <waits-on>: a ticket-id waits-on is also
# a pm link; a failure is a fault row, never a refusal.
_wt_park_record_wait() {
  emulate -L zsh
  local repo=$1 store=$2 session=$3 id=$4 waits_on=$5 out file
  [[ $waits_on =~ '^[a-z0-9]+-[a-z0-9]+$' ]] || return 0
  wt_pm_get "$store" "$waits_on" status >/dev/null 2>&1 || return 0
  out=$(wt_pm "$store" "$session" link "$waits_on" blocks "$id" 2>&1)
  (( $? == 0 )) && return 0
  out=${out//$'\n'/ }
  file=$(wt_fault_row park-dep-record-failed "$repo" "$id" park "$out")
  wt_say "parked $id but could not record waits-on $waits_on as a pm link: $out. Recorded in ${file:-(fault report unwritable)}. This is infrastructure, not a finding: file no ticket and write no retro; run \`pm link $waits_on blocks $id\` by hand."
  return 0
}

_wt_park_zero_delta() {
  emulate -L zsh
  local repo=$1 store=$2 wt_path=$3 id=$4 session=$5 waits_on=$6 note=$7 findings=$8 auto=$9
  local out tail
  local -i kept=0
  if ! wt_worktree_remove "$repo" "$wt_path"; then
    local -a steps=("${(@f)$(wt_cleanup_steps "$repo" "$wt_path")}")
    wt_stop_remove_failed park-worktree-remove-failed "$repo" "$id" park \
      "parking $id found no commits to keep, but \`git -C $repo worktree remove $wt_path\` failed" \
      "${steps[@]}" "\`git -C $repo branch -d $id\`" "\`pm drop $id\`"
    return 1
  fi
  git -C "$repo" branch -d "$id" >/dev/null 2>&1 || kept=1
  (( WT_REMOVE_DEFERRED )) && wt_deferred_line park-teardown-deferred "$repo" "$id" park "$wt_path" $kept
  _wt_park_record_wait "$repo" "$store" "$session" "$id" "$waits_on"
  out=$(wt_pm "$store" "$session" drop "$id" 2>&1)
  if (( $? != 0 )); then
    wt_fail infra park-ticket-release-failed "$repo" "$id" park \
      "parked $id with no work to keep but \`pm drop $id\` failed: ${out//$'\n'/ }" \
      "release it by hand with \`pm drop $id\`"
    return 1
  fi
  if (( WT_REMOVE_DEFERRED )); then
    tail="worktree removed, registration deferred to wt prune"
  elif (( kept )); then
    tail="worktree removed, branch $id kept"
  else
    tail="worktree and branch removed"
  fi
  local parked="no commits to keep; ticket released back to open, $tail; waits-on ${waits_on:-(none)}"
  if (( auto )); then
    print -r -- "$parked"
    return 0
  fi
  print -r -- "OK: $id parked with nothing to merge -- $parked"
  if [[ -n $note || -n $findings ]]; then
    wt_say "--note/--findings were NOT recorded: a zero-delta park releases $id instead of closing it."
  fi
  return 0
}

# Work wt already merged is never parked or released: tear down and close it.
_wt_park_merged() {
  emulate -L zsh
  local repo=$1 store=$2 cwd_repo=$3 default=$4 wt_path=$5 id=$6 session=$7 note=$8 findings=$9
  local -i have_findings=${10} auto=${11}
  local out
  if (( auto )); then
    if (( ! have_findings )) && wt_findings_required "$store"; then
      findings=none have_findings=1
    fi
  else
    _wt_park_check_findings "$store" "$id" "$note" "$findings" $have_findings || return 1
  fi
  if [[ ${store:A} != ${cwd_repo:A} ]]; then
    wt_guard "$cwd_repo" "$store" commit "$id" park || return 1
  fi
  wt_guard "$cwd_repo" "$repo" worktree "$id" park || return 1
  wt_refuse_undeletable "$wt_path" "$id" removed park || return 1

  local -a done_args=(done "$id")
  done_args+=(-m "${note:-already merged into $default; worktree torn down by wt park}")
  (( have_findings )) && done_args+=(--findings "$findings")

  if ! wt_worktree_remove "$repo" "$wt_path"; then
    local -a steps=("${(@f)$(wt_cleanup_steps "$repo" "$wt_path")}")
    local what
    out=$(wt_pm "$store" "$session" "${done_args[@]}" 2>&1)
    if (( $? == 0 )); then
      what="$id is already merged into $default and its ticket is now closed, but \`git -C $repo worktree remove $wt_path\` failed"
    else
      what="$id is already merged into $default but \`pm done\` failed (${out//$'\n'/ }) and \`git -C $repo worktree remove $wt_path\` failed"
      steps+=("\`pm ${done_args[*]}\`")
    fi
    wt_stop_remove_failed park-worktree-remove-failed "$repo" "$id" park "$what" \
      "${steps[@]}" "\`git -C $repo branch -d $id\`"
    return 1
  fi

  local branch_out
  local -i kept=0
  branch_out=$(git -C "$repo" branch -d "$id" 2>&1)
  if (( $? == 0 )); then
    wt_clear_merged "$repo" "$id"
  elif (( WT_REMOVE_DEFERRED )) && [[ $branch_out == *"used by worktree"* ]]; then
    kept=1
  elif [[ $branch_out == *"branch '$id' not found"* ]]; then
    wt_clear_merged "$repo" "$id"
  else
    local file
    file=$(wt_fault_row park-branch-delete-failed "$repo" "$id" park "${branch_out//$'\n'/ }")
    wt_say "removed the worktree for $id, but \`git -C $repo branch -d $id\` failed: ${branch_out//$'\n'/ }. Recorded in ${file:-(fault report unwritable)}. This is infrastructure, not a finding: file no ticket and write no retro; delete the branch by hand."
  fi
  (( WT_REMOVE_DEFERRED )) && wt_deferred_line park-teardown-deferred "$repo" "$id" park "$wt_path" $kept

  out=$(wt_pm "$store" "$session" "${done_args[@]}" 2>&1)
  if (( $? != 0 )); then
    wt_fail infra park-ticket-close-failed "$repo" "$id" park \
      "removed the worktree for $id but \`pm done $id\` failed: ${out//$'\n'/ }" \
      "close it by hand with \`pm ${done_args[*]}\`"
    return 1
  fi
  local tail="worktree and branch removed"
  (( WT_REMOVE_DEFERRED )) && tail="worktree removed; registration deferred to wt prune"
  local parked="already merged into $default; worktree torn down and ticket closed, not released"
  if (( auto )); then
    print -r -- "$parked"
  else
    print -r -- "OK: $id $parked ($tail)"
  fi
  return 0
}
