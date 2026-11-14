# Worktree removal, shared by finish/land, park, prune and start (quiet prune). Git and
# filesystem facts only: closing or releasing a ticket stays with the verb.

typeset -gi WT_MASS_DELETE_MIN=50

# Results of the last wt_worktree_remove, read by the functions below.
typeset -g WT_REMOVE_RC=0 WT_REMOVE_OUT="" WT_REMOVE_ERR="" WT_REMOVE_ACTION="" WT_REMOVE_DEFERRED=0
# Results of the last wt_prune_debt.
typeset -ga WT_PRUNE_DELETED
typeset -gi WT_PRUNE_CLEARED=0 WT_PRUNE_REMAINING=0

# 'gone' (dir missing), 'no-gitfile' (partial tree, `.git` file lost) or 'gitfile'.
wt_wt_shape() {
  emulate -L zsh
  if [[ ! -e $1 ]]; then
    print -r -- gone
  elif [[ ! -f $1/.git ]]; then
    print -r -- no-gitfile
  else
    print -r -- gitfile
  fi
  return 0
}

# Operator-run steps that remove a worktree in each detectable shape.
wt_cleanup_steps() {
  emulate -L zsh
  local repo=$1 wt_path=$2 shape
  shape=$(wt_wt_shape "$wt_path")
  case $shape in
    gone)
      print -r -- "\`git -C $repo worktree prune\` (the directory is already gone; this drops the stale registration)" ;;
    no-gitfile)
      print -r -- "\`rm -rf ${(q)wt_path}\` (its .git file is gone, so git no longer recognises it)"
      print -r -- "\`git -C $repo worktree prune\` (drops the stale registration)" ;;
    *)
      print -r -- "\`git -C $repo worktree remove --force ${(q)wt_path}\` (a partial tree counts as modified, so a plain remove refuses; check \`git -C $wt_path status\` first)" ;;
  esac
  return 0
}

# Make sure the keep entry (.git/worktrees/.keep/locked) exists when the admin directory
# does. A directory holding an empty `locked` file survives `git worktree prune`; it keeps
# git from removing the worktrees directory with its last admin dir. Never fails.
wt_keep_worktrees_dir() {
  emulate -L zsh
  local common wdir
  common=$(git -C "$1" rev-parse --git-common-dir 2>/dev/null) || return 0
  [[ -n $common ]] || return 0
  [[ $common == /* ]] || common=$1/$common
  wdir=$common/worktrees
  [[ -d $wdir ]] || return 0
  [[ -e $wdir/.keep/locked ]] && return 0
  mkdir -p -- "$wdir/.keep" 2>/dev/null && : >> "$wdir/.keep/locked" 2>/dev/null
  return 0
}

# wt_worktree_remove <repo> <wt_path>: keep entry, then `git worktree remove` (`prune` when
# the directory is already gone), then keep entry again. Sets WT_REMOVE_RC, WT_REMOVE_OUT
# (stderr then stdout, for the deferred check), WT_REMOVE_ERR (git's stderr, else its stdout,
# trimmed: the text the lines below quote), WT_REMOVE_ACTION and WT_REMOVE_DEFERRED.
# Returns 0 when removed or deferred, 1 otherwise. Deferred means the one benign failure:
# git could not delete THIS worktree's admin dir (`.git/worktrees/<id>` plus `Operation not
# permitted`) and the working tree is gone; checked on a prune that exited 0 too.
wt_worktree_remove() {
  emulate -L zsh
  setopt extendedglob
  local repo=$1 wt_path=$2 shape errf sout serr
  local -a cmd
  wt_keep_worktrees_dir "$repo"
  shape=$(wt_wt_shape "$wt_path")
  if [[ $shape == gone ]]; then
    WT_REMOVE_ACTION="git -C $repo worktree prune"
    cmd=(git -C "$repo" worktree prune)
  else
    WT_REMOVE_ACTION="git -C $repo worktree remove $wt_path"
    cmd=(git -C "$repo" worktree remove "$wt_path")
  fi
  errf=$(mktemp "${TMPDIR:-/tmp}/wt-remove.XXXXXX" 2>/dev/null)
  if [[ -n $errf ]]; then
    sout=$("${cmd[@]}" 2>"$errf")
    WT_REMOVE_RC=$?
    serr=$(<"$errf")
    command rm -f -- "$errf"
  else
    serr=$("${cmd[@]}" 2>&1)
    WT_REMOVE_RC=$?
    sout=""
  fi
  WT_REMOVE_OUT=$serr$'\n'$sout
  serr=${${serr##[[:space:]]#}%%[[:space:]]#}
  sout=${${sout##[[:space:]]#}%%[[:space:]]#}
  WT_REMOVE_ERR=${serr:-$sout}
  WT_REMOVE_DEFERRED=0
  local admin=".git/worktrees/${wt_path:t}"
  if [[ $WT_REMOVE_OUT == *"$admin"* && $WT_REMOVE_OUT == *"Operation not permitted"* \
        && $(wt_wt_shape "$wt_path") == gone ]]; then
    WT_REMOVE_DEFERRED=1
  fi
  if (( WT_REMOVE_RC != 0 && ! WT_REMOVE_DEFERRED )); then
    return 1
  fi
  wt_keep_worktrees_dir "$repo"
  return 0
}

# wt_stop_remove_failed <key> <repo> <ticket> <verb> <what> <operator cmd>...: the STOP line
# for a failed remove, with the fault row; reads WT_REMOVE_ERR. Returns 1.
wt_stop_remove_failed() {
  emulate -L zsh
  local key=$1 repo=$2 ticket=$3 verb=$4 what=$5 err file cmds
  shift 5
  err=$WT_REMOVE_ERR
  file=$(wt_fault_row "$key" "$repo" "$ticket" "$verb" "git: $err -- $what")
  cmds=${(j:; :)@}
  wt_say "STOP. $what: git said: $err. Recorded in ${file:-(fault report unwritable)}. This is infrastructure, not a finding: file no ticket and write no retro. Do not run any further git, wt or pm command against this worktree and do not escalate or disable the sandbox; tell the operator and hand them this cleanup (operator-run, in order): $cmds."
  return 1
}

# wt_deferred_line <key> <repo> <ticket> <verb> <wt_path> <branch_kept 0|1>: the one line for
# a gone working tree whose admin dir git could not delete; reads WT_REMOVE_ERR.
wt_deferred_line() {
  emulate -L zsh
  local key=$1 repo=$2 ticket=$3 verb=$4 wt_path=$5 kept=$6 err file kept_text=""
  err=$WT_REMOVE_ERR
  file=$(wt_fault_row "$key" "$repo" "$ticket" "$verb" "git: $err -- worktree $wt_path removed, admin dir left behind")
  (( kept )) && kept_text="; branch $ticket is kept until then"
  wt_say "worktree for $ticket is gone but its leftover registration (admin dir $repo/.git/worktrees/$ticket) could not be deleted in this sandbox$kept_text; \`wt prune\` clears it. Recorded in ${file:-(fault report unwritable)}. This is infrastructure, not a finding: file no ticket and write no retro."
  return 0
}

wt_clear_merged() {
  emulate -L zsh
  git -C "$1" update-ref -d "refs/wt/merged/$2" >/dev/null 2>&1
  return 0
}

# True only when the marker ref points at the branch tip and that tip is in the default branch.
wt_branch_already_merged() {
  emulate -L zsh
  local repo=$1 default=$2 id=$3 marker tip
  wt_branch_exists "$repo" "$id" || return 1
  marker=$(git -C "$repo" rev-parse --verify -q "refs/wt/merged/$id" 2>/dev/null) || return 1
  tip=$(git -C "$repo" rev-parse --verify -q "refs/heads/$id" 2>/dev/null) || return 1
  [[ -n $marker && $marker == $tip ]] || return 1
  wt_is_ancestor "$repo" "refs/heads/$id" "$default"
}

# Paths the sandbox cannot delete: the root of every nested git repo holding `.git/config`
# or `.git/hooks`, and every `.vscode` dir. One per line, sorted, unique. node_modules and
# symlinks are not entered; the worktree's own top-level `.git` file is ignored.
wt_undeletable_paths() {
  emulate -L zsh
  local top=${1:a} p
  local -a hits
  for p in "${(@f)$(find "$top" \( -name node_modules -o -name .vscode -o -name .git \) -prune -print 2>/dev/null)}"; do
    [[ -n $p && ! -L $p ]] || continue
    case ${p:t} in
      .vscode) [[ -d $p ]] && hits+=("$p") ;;
      .git)
        [[ $p == $top/.git ]] && continue
        [[ -d $p ]] || continue
        [[ -e $p/config || -e $p/hooks ]] && hits+=("${p:h}") ;;
    esac
  done
  (( $#hits )) || return 0
  print -rl -- "${(@ou)hits}"
  return 0
}

# wt_refuse_undeletable <wt_path> <ticket> <did_not> <verb>: returns 0 when the worktree holds
# nothing the sandbox cannot delete; otherwise prints the refusal (no fault row, at most five
# paths named) and returns 1.
wt_refuse_undeletable() {
  emulate -L zsh
  local wt_path=$1 ticket=$2 did_not=$3 verb=$4 out shown rms p
  local -a hits
  out=$(wt_undeletable_paths "$wt_path")
  [[ -n $out ]] || return 0
  hits=("${(@f)out}")
  shown=${(j:, :)hits[1,5]}
  (( $#hits > 5 )) && shown+=" and $(( $#hits - 5 )) more"
  rms=""
  for p in "${hits[@]}"; do
    rms+="${rms:+; }rm -rf ${(q)p}"
  done
  wt_say "worktree $wt_path holds paths the sandbox cannot delete (nested git repo or .vscode): $shown. Nothing was $did_not -- the worktree is intact and $ticket stays claimed. Hand the operator: $rms -- after that, \`wt $verb $ticket\` completes normally."
  return 1
}

# wt_merged_route <repo> <default> <wt_path> <ticket> <verb>: finish/park pre-check on git
# and filesystem facts. Returns 0 when wt already merged this branch (only teardown remains;
# a partial tree whose only changes are deletions is tolerated), 1 when not merged and the
# worktree is usable, 2 with a refusal printed (dirty merged tree, directory gone, or
# `.git` file missing). Closing the ticket is the verb's.
wt_merged_route() {
  emulate -L zsh
  local repo=$1 default=$2 wt_path=$3 ticket=$4 verb=$5 shape st line steps
  local -i merged=0
  wt_branch_already_merged "$repo" "$default" "$ticket" && merged=1
  shape=$(wt_wt_shape "$wt_path")
  if (( merged )); then
    if [[ $shape == gitfile ]]; then
      st=$(git -C "$wt_path" status --porcelain 2>/dev/null)
      for line in "${(@f)st}"; do
        [[ -n ${line//[[:space:]]/} ]] || continue
        if [[ ${line[1,2]} != *D* ]]; then
          wt_say "worktree $wt_path holds uncommitted changes beyond deletions; $ticket is already merged but nothing was torn down. Commit or remove them, then \`wt finish $ticket\`."
          return 2
        fi
      done
    fi
    return 0
  fi
  case $shape in
    gone)
      wt_say "worktree directory $wt_path is gone but git still registers it, and $ticket has no merged work to close. Nothing was changed. Tell the operator to run \`git -C $repo worktree prune\`; branch $ticket is kept, and \`wt start $ticket\` resumes it."
      return 2 ;;
    no-gitfile)
      steps=${(j:; :)${(@f)$(wt_cleanup_steps "$repo" "$wt_path")}}
      wt_say "$wt_path has no .git file: it is the partial tree of a failed worktree remove and git there would act on the enclosing repo. Nothing was changed; $verb refused. Tell the operator to clean it up: $steps"
      return 2 ;;
  esac
  return 1
}

# wt_prune_debt <repo> <default> [quiet]: prune prunable registrations, then delete the
# branches of the cleared ones and any marker-bearing branch proven merged with no worktree
# entry, by `git branch -d` only. Sets WT_PRUNE_CLEARED, WT_PRUNE_REMAINING and
# WT_PRUNE_DELETED. Prints the remaining-registrations line and the OK line unless quiet.
wt_prune_debt() {
  emulate -L zsh
  local repo=$1 default=$2 quiet=${3:-} i bid ln prefix=refs/wt/merged/ refs
  local -a before_paths before_branches after_paths held candidates seen
  local -i n_before=0
  WT_PRUNE_DELETED=() WT_PRUNE_CLEARED=0 WT_PRUNE_REMAINING=0
  wt_worktree_list "$repo" || return 1
  for (( i = 1; i <= $#WT_WORKTREE_PATHS; i++ )); do
    [[ -n ${WT_WORKTREE_PRUNABLE[i]} ]] || continue
    before_paths+=("${WT_WORKTREE_PATHS[i]:A}")
    before_branches+=("${WT_WORKTREE_BRANCHES[i]}")
  done
  n_before=$#before_paths
  [[ -n $quiet ]] && (( n_before == 0 )) && return 0
  wt_keep_worktrees_dir "$repo"
  git -C "$repo" worktree prune >/dev/null 2>&1
  wt_worktree_list "$repo" || return 1
  for (( i = 1; i <= $#WT_WORKTREE_PATHS; i++ )); do
    if [[ -n ${WT_WORKTREE_PRUNABLE[i]} ]]; then
      after_paths+=("${WT_WORKTREE_PATHS[i]:A}")
    fi
    [[ -n ${WT_WORKTREE_BRANCHES[i]} ]] && held+=("${WT_WORKTREE_BRANCHES[i]}")
  done
  WT_PRUNE_REMAINING=$#after_paths
  if (( WT_PRUNE_REMAINING )) && [[ -z $quiet ]]; then
    wt_say "$WT_PRUNE_REMAINING deferred-teardown registration(s) remain; this session's sandbox denies deleting them. Operator: !git -C $repo worktree prune"
  fi
  for (( i = 1; i <= n_before; i++ )); do
    (( ${after_paths[(Ie)${before_paths[i]}]} )) && continue
    WT_PRUNE_CLEARED+=1
    [[ -n ${before_branches[i]} ]] && candidates+=("${before_branches[i]}")
  done
  refs=$(git -C "$repo" for-each-ref --format='%(refname)' "$prefix" 2>/dev/null)
  for ln in "${(@f)refs}"; do
    [[ $ln == $prefix* ]] && candidates+=("${ln#$prefix}")
  done
  for bid in "${candidates[@]}"; do
    (( ${seen[(Ie)$bid]} )) && continue
    seen+=("$bid")
    [[ $bid == $default ]] && continue
    (( ${held[(Ie)$bid]} )) && continue
    if ! wt_branch_exists "$repo" "$bid"; then
      wt_clear_merged "$repo" "$bid"
      continue
    fi
    wt_is_ancestor "$repo" "refs/heads/$bid" "$default" || continue
    if git -C "$repo" branch -d "$bid" >/dev/null 2>&1; then
      wt_clear_merged "$repo" "$bid"
      WT_PRUNE_DELETED+=("$bid")
    fi
  done
  if [[ -z $quiet ]]; then
    print -r -- "OK: wt prune -- $WT_PRUNE_CLEARED registration(s) cleared, $WT_PRUNE_REMAINING remain, $#WT_PRUNE_DELETED branch(es) deleted${WT_PRUNE_DELETED:+: ${(j:, :)WT_PRUNE_DELETED}}"
  fi
  return 0
}
