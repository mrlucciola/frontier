# wt finish <id> [--note TEXT] [--findings VALUE] [--no-gate] [--keep-open]
# wt land <id> [--no-gate]      both also take --session ID, --store PATH, --repo PATH
# Runs <repo>/.wt/gate if present (--no-gate for doc-only tickets), rebases onto the
# default branch, merges ff-only, removes worktree and branch, then `pm done`
# (--note and --findings go there). Gate line "SKIP lines: K": list K under NOT PROVEN.
# A rebase conflict or lost ff-only race parks the ticket; resume with wt start.
# land = finish --keep-open: no pm done, the ticket stays taken; wt start <id> again from
# the same session to go on. On .git/index.lock wait a few seconds and re-run.

# `land` arrives here from the dispatcher with WT_VERB=land. wt_merged_route returns 0
# when the branch is already merged (only teardown remains), 1 when it still has to be
# merged, and 2 when it refused and printed why.

typeset -gi WT_FFONLY_TRIES=3
typeset -gi WT_GATE_TAIL=30
typeset -ga WT_RED_TICKETS WT_RED_MATCH WT_SCAN_HITS WT_SCAN_UNMATCHED WT_SCAN_STALE

wt_verb() {
  emulate -L zsh
  setopt extendedglob
  local verb=${WT_VERB:-finish} id="" note="" findings="" session=${PM_SESSION_ID:-}
  local store_opt="" repo_opt="" arg
  local -i keep_open=0 no_gate=0 have_note=0 have_findings=0
  [[ $verb == land ]] && keep_open=1
  while (( $# )); do
    arg=$1
    case $arg in
      --note|--findings|--session|--store|--repo)
        if (( $# < 2 )); then
          wt_say "$arg needs a value. Usage: wt $verb <id> $arg <value>"
          return 2
        fi
        case $arg in
          --note) note=$2 have_note=1 ;;
          --findings) findings=$2 have_findings=1 ;;
          --session) session=$2 ;;
          --store) store_opt=$2 ;;
          --repo) repo_opt=$2 ;;
        esac
        shift 2
        ;;
      --no-gate) no_gate=1; shift ;;
      --keep-open) keep_open=1; shift ;;
      -*)
        wt_say "wt $verb: unknown option $arg. Usage: wt $verb <id> [--note TEXT] [--findings VALUE] [--keep-open] [--no-gate] [--store PATH] [--repo PATH]"
        return 2
        ;;
      *)
        if [[ -n $id ]]; then
          wt_say "wt $verb takes one ticket id, got a second argument '$arg'. Usage: wt $verb <id> ..."
          return 2
        fi
        id=$arg
        shift
        ;;
    esac
  done
  if [[ -z $id ]]; then
    wt_say "wt $verb needs a ticket id. Usage: wt $verb <id> [--note TEXT] [--findings VALUE] [--no-gate]"
    return 2
  fi
  if (( keep_open && (have_note || have_findings) )); then
    wt_say "--note/--findings are recorded on the ticket close, and --keep-open (wt land) does not close the ticket -- pass them to the final \`wt finish $id\`."
    return 2
  fi

  local cwd_repo store repo wt_path default
  cwd_repo=$(wt_repo_root .) || return 1
  wt_resolve_repos "$store_opt" "$repo_opt" "$id" "$cwd_repo" || return 1
  store=$WT_STORE repo=$WT_REPO
  wt_path=$(wt_worktree_path "$repo" "$id")

  wt_worktree_list "$repo" || return 1
  local -i listed=0 i
  for (( i = 1; i <= $#WT_WORKTREE_PATHS; i++ )); do
    [[ ${WT_WORKTREE_PATHS[i]:A} == ${wt_path:A} ]] && listed=1
  done
  if (( ! listed )); then
    wt_say "no worktree at $wt_path for $id -- nothing to finish. If the work is unmerged, \`wt start $id\` resumes its branch."
    return 1
  fi

  if (( ! keep_open )); then
    _wt_finish_check_findings "$store" "$id" "$verb" "$have_findings" "$findings" "$note" || return 1
  fi

  default=$(wt_default_branch "$repo") || return 1
  local -i route
  wt_merged_route "$repo" "$default" "$wt_path" "$id" "$verb"
  route=$?
  if (( route == 2 )); then
    return 1
  elif (( route == 0 )); then
    if [[ ${store:A} != ${cwd_repo:A} ]]; then
      wt_guard "$cwd_repo" "$store" commit "$id" "$verb" || return 1
    fi
    wt_guard "$cwd_repo" "$repo" worktree "$id" "$verb" || return 1
    wt_refuse_undeletable "$wt_path" "$id" removed "$verb" || return 1
    _wt_finish_teardown "$repo" "$store" "$session" "$wt_path" "$id" "$default" "$note" "$verb" "$findings" "$keep_open" 0 1
    return $?
  fi

  local dirty
  dirty=$(git -C "$wt_path" status --porcelain 2>/dev/null)
  if [[ -n ${dirty//[[:space:]]/} ]]; then
    wt_say "worktree $wt_path has uncommitted or untracked files; finish merges only committed work and nothing was merged -- the ticket stays claimed and the worktree intact. Commit them (\`git -C $wt_path add <paths>\` then commit) or remove them, then re-run \`wt $verb $id\`."
    return 1
  fi

  if [[ ${store:A} != ${cwd_repo:A} ]]; then
    wt_guard "$cwd_repo" "$store" commit "$id" "$verb" || return 1
  fi
  wt_guard "$cwd_repo" "$repo" merge "$id" "$verb" || return 1

  local gate=$repo/.wt/gate gate_note="" skips=0 rc
  if [[ -e $gate ]]; then
    if (( no_gate )); then
      gate_note="gate skipped (--no-gate): .wt/gate"
      print -u2 -r -- "wt: --no-gate: skipping gate .wt/gate"
    else
      if [[ ! -x $gate || -d $gate ]]; then
        wt_say "$gate is not executable, so wt cannot run the gate; fix it or pass --no-gate."
        return 1
      fi
      _wt_finish_gate "$gate" "$wt_path" "$repo" "$id" "$verb"
      rc=$?
      (( rc == 0 )) || return 1
      gate_note=$WT_GATE_NOTE skips=$WT_GATE_SKIPS
    fi
    note=${note:+$note$'\n'}$gate_note
  fi

  wt_refuse_undeletable "$wt_path" "$id" merged "$verb" || return 1

  local -i attempt has_work
  local merge_err cause park_note
  for (( attempt = 1; attempt <= WT_FFONLY_TRIES; attempt++ )); do
    if ! git -C "$wt_path" rebase "$default" >/dev/null 2>&1; then
      git -C "$wt_path" rebase --abort >/dev/null 2>&1
      park_note=$(_wt_finish_autopark "$id" "$session" "$store_opt" "$repo_opt")
      wt_fail infra finish-rebase-conflict "$repo" "$id" "$verb" \
        "rebase of $id onto $default conflicted; auto-parked ($park_note)" \
        "resolve the conflict by hand in a fresh \`wt start $id\`, then \`wt finish $id\` again"
      return 1
    fi
    has_work=0
    [[ -n $(git -C "$repo" log --oneline "$default..$id" 2>/dev/null) ]] && has_work=1
    merge_err=$(git -C "$repo" merge --ff-only "$id" 2>&1)
    if (( $? == 0 )); then
      if (( has_work )); then
        git -C "$repo" update-ref "refs/wt/merged/$id" "refs/heads/$id" >/dev/null 2>&1
        wt_pm "$store" "$session" emit "$id" wt.merged "sha=$(git -C "$repo" rev-parse "refs/heads/$id" 2>/dev/null)" >/dev/null 2>&1
      fi
      break
    fi
    if (( attempt == WT_FFONLY_TRIES )); then
      merge_err=${merge_err//$'\n'/ }
      if [[ ${(L)merge_err} == *"local changes"* ]]; then
        cause="uncommitted changes in the $repo main checkout overlap this branch -- restore or commit them"
      else
        cause="the default branch kept moving"
      fi
      park_note=$(_wt_finish_autopark "$id" "$session" "$store_opt" "$repo_opt")
      wt_fail infra finish-ffonly-retry-exhausted "$repo" "$id" "$verb" \
        "ff-only merge of $id onto $default failed $WT_FFONLY_TRIES times ($cause); git: $merge_err; auto-parked ($park_note)" \
        "re-run \`wt finish $id\` once $default is quiet"
      return 1
    fi
  done

  _wt_finish_teardown "$repo" "$store" "$session" "$wt_path" "$id" "$default" "$note" "$verb" "$findings" "$keep_open" "$skips" 0
  return $?
}

# The subprocess is the dispatcher itself: park is another verb file. Its stdout is the
# note; its exit status is passed on.
_wt_finish_autopark() {
  emulate -L zsh
  local id=$1 session=$2 store_opt=$3 repo_opt=$4 out rc
  local -a args=(park "$id" --auto)
  [[ -n $store_opt ]] && args+=(--store "$store_opt")
  [[ -n $repo_opt ]] && args+=(--repo "$repo_opt")
  if [[ -n $session ]]; then
    out=$(command env PM_SESSION_ID="$session" "$WT_COMPONENT/cli/wt" "${args[@]}")
  else
    out=$("$WT_COMPONENT/cli/wt" "${args[@]}")
  fi
  rc=$?
  print -r -- "${out//$'\n'/ }"
  return $rc
}

_wt_finish_check_findings() {
  emulate -L zsh
  setopt extendedglob
  local store=$1 id=$2 verb=$3 have=$4 findings=$5 note=$6 text log
  local -i required=0
  wt_findings_required "$store" && required=1
  text="no --findings: this close attests nothing about what was not done, not proven, or found elsewhere; pass --findings none or the ids"
  if (( ! have )); then
    if (( required )); then
      wt_say "$text. Nothing was merged or removed; re-run \`wt $verb $id --findings <none|ids>\`."
      return 1
    fi
    wt_say "$text"
  elif [[ ${findings//[[:space:]]/} == none ]] && (( required )); then
    if [[ -z ${note//[[:space:]]/} ]]; then
      log=$(wt_pm "$store" "" show "$id" 2>/dev/null)
      if [[ $log != (#s)(*$'\n')#(notes:|notes \(last)* ]]; then
        wt_say "--findings none needs a non-empty --note or an existing ticket note: 'none' is a statement, not a default. Nothing was merged or removed; re-run \`wt $verb $id --findings none --note <text>\`."
        return 1
      fi
    fi
  fi
  return 0
}

# Fills WT_RED_TICKETS and WT_RED_MATCH (index-aligned) from <repo>/.wt/known-red: one
# `<ticket id> <text to match>` per line, blank and `#` lines skipped.
_wt_known_red() {
  emulate -L zsh
  setopt extendedglob
  local file=$1/.wt/known-red line id text
  WT_RED_TICKETS=() WT_RED_MATCH=()
  [[ -f $file ]] || return 0
  while IFS= read -r line || [[ -n $line ]]; do
    line=${line##[[:space:]]#}
    [[ -z $line || $line == \#* ]] && continue
    id=${line%%[[:space:]]*}
    text=${line#"$id"}
    text=${text##[[:space:]]#}
    if [[ -z $text ]]; then
      print -u2 -r -- "wt: $file: '$line' needs '<ticket id> <text to match>'; fix that line."
      return 1
    fi
    WT_RED_TICKETS+=("$id") WT_RED_MATCH+=("$text")
  done < "$file"
  return 0
}

# Classifies a failing run's output against the known-red entries. Sets WT_SCAN_HITS
# ("<ticket>\t<line>"), WT_SCAN_UNMATCHED (failure-marked lines no entry covers) and
# WT_SCAN_STALE (entry indexes with no hit). A failure-marked line is covered when it, an
# ancestor by indentation, or all of its indented children are covered.
_wt_red_scan() {
  emulate -L zsh
  setopt extendedglob
  local out=$1 ln text lead c
  local -a ind txt matched parent children stack hit_e anc covered kids
  local -i n=0 i e
  WT_SCAN_HITS=() WT_SCAN_UNMATCHED=() WT_SCAN_STALE=()
  for ln in "${(@f)out}"; do
    text=${${ln##[[:space:]]#}%%[[:space:]]#}
    [[ -n $text ]] || continue
    lead=${ln##[[:space:]]#}
    ind+=($(( ${#ln} - ${#lead} )))
    txt+=("$text")
  done
  n=$#txt
  for (( i = 1; i <= n; i++ )); do
    matched[i]=0 parent[i]=0 children[i]=""
    [[ ${txt[i]} =~ '^(PASS|ok|SKIP|DEGRADED)([^A-Za-z0-9_]|$)' ]] && continue
    for (( e = 1; e <= $#WT_RED_MATCH; e++ )); do
      if [[ ${txt[i]} == *"${WT_RED_MATCH[e]}"* ]]; then
        matched[i]=1
        WT_SCAN_HITS+=("${WT_RED_TICKETS[e]}"$'\t'"${txt[i]}")
        hit_e+=($e)
        break
      fi
    done
  done
  for (( i = 1; i <= n; i++ )); do
    while (( $#stack )) && (( ${ind[$stack[-1]]} >= ${ind[i]} )); do
      stack[-1]=()
    done
    anc[i]=${matched[i]}
    if (( $#stack )); then
      parent[i]=${stack[-1]}
      children[${stack[-1]}]+=" $i"
      (( ${anc[${stack[-1]}]} )) && anc[i]=1
    fi
    stack+=($i)
  done
  for (( i = n; i >= 1; i-- )); do
    covered[i]=${anc[i]}
    kids=(${=children[i]})
    if (( ! covered[i] && $#kids )); then
      covered[i]=1
      for c in $kids; do
        (( ${covered[c]} )) || covered[i]=0
      done
    fi
  done
  for (( i = 1; i <= n; i++ )); do
    [[ ${txt[i]} =~ '(^|[^A-Za-z0-9_])(FAIL|FAILED|ERROR|not ok)([^A-Za-z0-9_]|$)' ]] || continue
    (( ${covered[i]} )) || WT_SCAN_UNMATCHED+=("${txt[i]}")
  done
  for (( e = 1; e <= $#WT_RED_MATCH; e++ )); do
    (( ${hit_e[(Ie)$e]} )) || WT_SCAN_STALE+=($e)
  done
  return 0
}

# _wt_finish_gate <gate> <worktree> <repo> <id> <verb>: runs the gate in the worktree. On
# success sets WT_GATE_NOTE and WT_GATE_SKIPS and returns 0; a refusal prints and returns 1.
typeset -g WT_GATE_NOTE=""
typeset -gi WT_GATE_SKIPS=0
_wt_finish_gate() {
  emulate -L zsh
  local gate=$1 wt_path=$2 repo=$3 id=$4 verb=$5 out ln lower e
  local -a lines tail_lines hit_tickets
  local -i rc skips=0 n_lines
  out=$( builtin cd -q -- "$wt_path" && "$gate" 2>&1 )
  rc=$?
  lines=("${(@f)out}")
  for ln in "${lines[@]}"; do
    lower=${(L)ln}
    [[ $lower =~ '(^|[^a-z0-9_])skip(ped)?([^a-z0-9_]|$)' ]] && skips+=1
  done
  print -u2 -r -- "wt: gate .wt/gate exit $rc, SKIP lines: $skips"
  _wt_known_red "$repo" || return 1
  if (( $#WT_RED_MATCH )); then
    _wt_red_scan "$out"
    for ln in "${WT_SCAN_HITS[@]}"; do
      print -u2 -r -- "known red (${ln%%$'\t'*}): ${ln#*$'\t'}"
    done
    for e in "${WT_SCAN_STALE[@]}"; do
      wt_say "known-red now green: close ${WT_RED_TICKETS[e]} and drop the entry (match '${WT_RED_MATCH[e]}') from $repo/.wt/known-red -- nothing was merged; the ticket stays claimed and the worktree intact. Re-run \`wt $verb $id\` after removing it."
    done
    (( $#WT_SCAN_STALE )) && return 1
    if (( rc != 0 && $#WT_SCAN_HITS && ! $#WT_SCAN_UNMATCHED )); then
      for ln in "${WT_SCAN_HITS[@]}"; do
        hit_tickets+=("${ln%%$'\t'*}")
      done
      WT_GATE_NOTE="gate: .wt/gate exit $rc, SKIP $skips"$'\n'"known red ${(j: :)${(ou)hit_tickets}}"
      WT_GATE_SKIPS=$skips
      return 0
    fi
  fi
  if (( rc != 0 )); then
    n_lines=$#lines
    tail_lines=("${(@)lines[$(( n_lines > WT_GATE_TAIL ? n_lines - WT_GATE_TAIL + 1 : 1 )),-1]}")
    print -u2 -r -- "wt: gate failed (exit $rc); last $WT_GATE_TAIL lines:"
    print -u2 -rl -- "${tail_lines[@]}"
    print -u2 -r -- "wt: nothing was merged -- the ticket stays claimed and the worktree intact. Fix it in $wt_path and re-run \`wt $verb $id\` (doc-only ticket: add --no-gate)."
    return 1
  fi
  WT_GATE_NOTE="gate: .wt/gate exit $rc, SKIP $skips"
  WT_GATE_SKIPS=$skips
  return 0
}

# _wt_finish_close_cmd <repo> <store> <id> <note> <findings>: a paste-safe `pm done` for
# the operator.
_wt_finish_close_cmd() {
  emulate -L zsh
  local repo=$1 store=$2 id=$3 note=$4 findings=$5 cmd="pm done"
  [[ -n $note ]] && cmd+=" -m ${(qq)note}"
  cmd+=" --findings ${(qq)${findings:-none}} $id"
  [[ ${store:A} != ${repo:A} ]] && cmd="cd ${(qq)store} && $cmd"
  print -r -- "\`$cmd\`"
}

# _wt_finish_done <store> <session> <id> <note> <findings>: runs `pm done`; output in
# WT_DONE_OUT, status returned.
typeset -g WT_DONE_OUT=""
_wt_finish_done() {
  emulate -L zsh
  local store=$1 session=$2 id=$3 note=$4 findings=$5
  local -a args=(done "$id")
  [[ -n $note ]] && args+=(-m "$note")
  [[ -n $findings ]] && args+=(--findings "$findings")
  WT_DONE_OUT=$(wt_pm "$store" "$session" "${args[@]}" 2>&1)
  return $?
}

_wt_finish_teardown() {
  emulate -L zsh
  local repo=$1 store=$2 session=$3 wt_path=$4 id=$5 default=$6 note=$7 verb=$8 findings=$9
  local keep_open=${10} skips=${11} already=${12}
  local what out tail err file refusal status_now closecmd
  local -a cmds
  local -i kept=0 deferred=0

  # pm refuses `--findings none` without a reason.
  if [[ -z $note && ${findings//[[:space:]]/} == none ]] && (( ! keep_open )); then
    note="wt finish: merged $id into $default"
  fi

  if ! wt_worktree_remove "$repo" "$wt_path"; then
    cmds=("${(@f)$(wt_cleanup_steps "$repo" "$wt_path")}")
    cmds+=("\`git -C $repo branch -d $id\`")
    closecmd=$(_wt_finish_close_cmd "$repo" "$store" "$id" "$note" "$findings")
    if (( already && ! keep_open )); then
      _wt_finish_done "$store" "$session" "$id" "${note:+$note$'\n'}branch was already merged into $default; worktree remove failed, cleanup left to the operator" "$findings"
      if (( $? == 0 )); then
        what="$id is already merged into $default and its ticket is now closed, but \`$WT_REMOVE_ACTION\` failed"
      else
        refusal=${WT_DONE_OUT//$'\n'/ }
        what="$id is already merged into $default but \`pm done\` failed ($refusal) and \`$WT_REMOVE_ACTION\` failed"
        cmds+=("$closecmd")
      fi
    else
      what="merged $id into $default, but \`$WT_REMOVE_ACTION\` failed; the ticket is NOT yet closed"
      (( keep_open )) || cmds+=("$closecmd")
    fi
    wt_stop_remove_failed finish-worktree-remove-failed "$repo" "$id" "$verb" "$what" "${cmds[@]}"
    return 1
  fi
  deferred=$WT_REMOVE_DEFERRED

  out=$(git -C "$repo" branch -d "$id" 2>&1)
  if (( $? != 0 )); then
    if (( deferred )) && [[ $out == *"used by worktree"* ]]; then
      kept=1
    elif [[ $out == *"branch '$id' not found"* ]]; then
      wt_clear_merged "$repo" "$id"
    else
      err=${out//$'\n'/ }
      file=$(wt_fault_row finish-branch-delete-failed "$repo" "$id" "$verb" "$err")
      wt_say "merged and removed the worktree for $id, but \`git -C $repo branch -d $id\` failed: $err. Recorded in ${file:-(fault report unwritable)}. This is infrastructure, not a finding: file no ticket and write no retro; delete the branch by hand."
    fi
  else
    wt_clear_merged "$repo" "$id"
  fi

  tail="worktree and branch removed"
  if (( deferred )); then
    wt_deferred_line finish-teardown-deferred "$repo" "$id" "$verb" "$wt_path" "$kept"
    if (( kept )); then
      tail="worktree removed; registration and branch deferred to wt prune"
    else
      tail="worktree removed; registration deferred to wt prune"
    fi
  fi

  if (( keep_open )); then
    print -r -- "OK: $id merged into $default, $tail, ticket left claimed and open. To keep working: \`wt start $id\` (the same session adopts the claim)."
    return 0
  fi

  closecmd=$(_wt_finish_close_cmd "$repo" "$store" "$id" "$note" "$findings")
  if ! _wt_finish_done "$store" "$session" "$id" "$note" "$findings"; then
    refusal=${WT_DONE_OUT//$'\n'/ }
    status_now=$(wt_pm_get "$store" "$id" status 2>/dev/null)
    if [[ $status_now == done ]]; then
      wt_fail flow finish-ticket-close-failed "$repo" "$id" "$verb" \
        "merged $id and cleaned up the worktree/branch, but \`pm done $id\` failed: $refusal" \
        "close it by hand with $closecmd"
      return 1
    fi
    [[ -n $WT_DONE_OUT ]] && print -u2 -r -- "$WT_DONE_OUT"
    print -r -- "OK: $id merged into $default, $tail; ticket NOT closed: pm refused ($refusal). Fix that, then run $closecmd"
    return 0
  fi
  print -r -- "OK: $id merged into $default, $tail, ticket closed${skips:+${${skips#0}:+; gate SKIP $skips recorded on the ticket}}"
  return 0
}
