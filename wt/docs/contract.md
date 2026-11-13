# wt

One scripted worktree lifecycle for every provider (cl-0c03c7, epic
cl-95fece). Replaces the prose git sequence in the `worktree-lifecycle`
skill so agents stop re-deriving it, stop triggering approval prompts on
raw git, and stop diverging (`branch -D`, `rm -rf`, main-checkout edits).

## Install root

Provider-neutral: renders once to `~/.local/libexec/wt/` (the `shared`
pseudo-provider), symlinked onto PATH as `~/.local/bin/wt` by this
package's `postdeploy` step. No provider-specific copy.

## Verbs

```
wt start <id> [--as NAME] [--force]    # claim via pm (or adopt own claim), add/resume the worktree
wt finish <id> [--note TEXT] [--findings VALUE] [--keep-open] [--no-gate]
                                       # gate, rebase, ff-only merge, teardown, close
wt land <id> [--no-gate]               # = finish --keep-open: merge + teardown, ticket stays claimed
wt park <id> [--waits-on <id-or-note>] [--note TEXT] [--findings VALUE]
                                       # commit WIP, close --unmerged, teardown
wt status                              # worktree list joined against tickets
wt pending                             # done-unmerged tickets, blockers cleared
wt prune                               # clear deferred-teardown registrations, delete their merged branches
wt selftest                            # full lifecycle in a throwaway repo
```

`--as` defaults to `$WT_ACTOR` when set.

`finish` and `park` pass `--note` and `--findings` straight to
`pm ticket close` (fr-bc2f6f, fr-b880c8); each is omitted from the close
when not given. On `park`, `--note` is prepended to the generated
branch/sha/resume note (the resume line stays last). A zero-delta park
releases the ticket instead of closing it, so it records neither and says
so.

`finish --keep-open` (`wt land`, fr-366ba3) does everything `finish` does
-- same refusals (dirty worktree, store/repo guard, rebase conflict,
ff-only exhaustion), merge, worktree and branch removal -- but skips the
`pm ticket close`: the ticket stays claimed and open, for a long-lived
ticket whose records must reach the default branch every turn. It rejects
`--note`/`--findings` (nothing to attach them to). To keep working, run
`wt start <id>` again from the same session: it adopts the existing claim
(below), no release needed.

`start` adopts a ticket that is already `claimed` by the claim it would
itself write (same provider/actor and same session token, derived as pm's
`session_token` does: `--session`, else `PM_SESSION_ID`, else
`CLAUDE_CODE_SESSION_ID`), prints one `adopting existing claim` line and
skips the claim. A different token, a different actor, or a bare-name claim
still refuses. `wt start --force` passes `--force` to `pm ticket claim`
(blocked ticket, operator-sanctioned only); end a force-claimed ticket with
`wt park`, never `wt finish` (start prints a reminder; not enforced).

### Gate (`.pm/config.json` key `gate`, fr-240ed1)

`finish` and `land` read an optional `gate` from the target repo's
`.pm/config.json`: a non-empty argv list, e.g.
`{"gate": ["python3", "tests/run_suite.py"]}`. It runs in the worktree (after
the dirty-worktree check, before any rebase or merge). Non-zero exit refuses
the finish: nothing merged, ticket stays claimed, worktree intact, and the
last 30 lines of output are printed. Every run prints
`gate <argv> exit N, SKIP lines: K` (output lines matching `skip`/`skipped`,
case-insensitive) so skipped tests can be reported as NOT PROVEN. A
malformed `gate` (not a list of strings) refuses too -- a typo never turns
the gate off. `--no-gate` (for doc-only tickets) bypasses it and appends
`gate skipped (--no-gate): <argv>` to the `pm ticket close --note`
(`land` has no close, so it only prints the skip). No `gate` key, no gate.

`known_red` entries in the same `.pm/config.json` excuse an owned red:
`known red (<ticket>): <line>` passes (the close note says
`known red <ticket>`); an entry whose line stopped failing refuses until it
is dropped. After the gate, the ff-only merge from the main checkout is
retried up to three times while the default branch keeps moving under
`pm ticket` commits. `finish` and `park` warn when `--findings` is missing,
and refuse before any merge or teardown once the store sets
`findings_required`.

`start`/`finish`/`park`/`status`/`pending`/`prune` also take `--store <path>` and
`--repo <path>` (fr-98ae8c, cl-4c434f). `start`/`finish`/`park` find the
store by ticket prefix first: they run `pm ticket where <id>` from the cwd
repo and use the root it prints (wt never reads the registry itself). When
pm says no registered store owns the prefix, the store is the cwd repo, so
an unregistered single-store repo works as before; any other `where`
failure (two owners, pm missing) stops with pm's message. `--store <path>`
overrides the lookup and is needed only for a store the registry does not
list; the worktree target then defaults to the store repo too. `--repo`
still overrides the worktree/git-mutation target independently of the
store. A worktree always lives at
`<target_repo>/.worktrees/<id>` on branch `<id>`.

## Settled decisions (do not relitigate without the epic)

- `park` removes the worktree and keeps the branch; it commits WIP first;
  a non-empty `<worktree>/.local` blocks the park.
- `wt` never runs `branch -D`, never `worktree remove --force`, never
  `rm -rf`.
- Every failure path prints one fixed line naming the exact next step and
  best-effort appends one deduplicated row to
  `~/frontier/docs/backlog/inbox/infra-faults/<day>-wt-<root-cause>.md`
  (mirrors the signing-failure pattern, cl-9a7d54) -- never a per-incident
  ticket.
- Exception (fr-c84ac9): when `git worktree remove`/`prune` fails with
  `Operation not permitted` on this worktree's admin dir and the tree is gone,
  `finish`/`park` print one "worktree for <id> is gone but its leftover
  registration ... could not be deleted in this sandbox; ... wt prune clears
  it" line instead, close or release the ticket as normal, and log a
  `*-teardown-deferred` row (informational debt, not a fault); `wt prune`
  (fr-f8fb42) clears it.
- A failed `git worktree remove` (finish or park) prints a `STOP.` line and
  never invites a retry, `--force` or a sandbox-disabled attempt; it hands
  the operator the cleanup commands (fr-90515c). `park` refuses a worktree
  that is only deletions (>50) or has lost its `.git` file, and `start`
  refuses to resume a branch whose tip is a mass-deleting `WIP: park`
  commit. A successful ff-only merge of a branch with commits pins the tip in
  `refs/wt/merged/<id>`; `finish` and `park` on a branch whose tip equals that
  marker (and is in the default branch) tear down and close the ticket, never
  park or `pm ticket release` it. The failed-remove handoff is per shape:
  dir gone -> `worktree prune`; partial tree -> operator-run `worktree remove
  --force`; `.git` file missing -> `rm -rf` then prune.
- `finish` and `park` refuse (before any merge, WIP commit or remove) a
  worktree holding a nested git repo (a `.git` dir with `config` or `hooks`)
  or a `.vscode` dir: the Claude CLI sandbox cannot delete those, so
  `git worktree remove` would leave a partial tree (fr-18b03c). The line
  names up to 5 paths and the operator-run `rm -rf` per path; no fault row.
  `start` appends a restart/resume hint when `git worktree add` fails with
  `.git/worktrees` "Operation not permitted".
- Pinned empirically (2026-10-07): `git worktree remove` deletes silently
  when only git-ignored files remain dirty -- it does not refuse. That is
  exactly why `park`'s `.local/` check is wt's own, not a reliance on git's
  dirty-check.

## Deferred teardown and prune (fr-c84ac9, fr-f8fb42)

When `git worktree remove` or `prune` fails with `Operation not permitted`
on THIS worktree's admin dir (`.git/worktrees/<id>`) and the working tree is
already gone, `finish` and `park` treat it as success with debt: the ticket
is closed or released as normal, the registration (and, on finish, the
branch) is left behind, and one `deferred` line says so. Before and after
each teardown `wt` writes a keep entry (a directory `.keep` holding an empty
`locked` file) in the worktrees admin dir, so git never deletes that
directory itself. Every other remove failure keeps the `STOP.` line.

`wt prune [--repo R] [--store S]` keeps the keep entry, runs
`git worktree prune`, then deletes a branch only when `refs/heads/<id>` is an
ancestor of the default branch and no worktree holds it. `wt start` runs it
quietly. If registrations remain it prints `<n> deferred-teardown
registration(s) remain; this session's sandbox denies deleting them.
Operator: !git -C <repo> worktree prune`: that is the operator's step, never
the agent's. `wt status` labels such an entry `deferred-teardown`.

## Reading wt output (full list)

- A line starting `OK:` is the verb's success. Nothing else to do, except:
- `OK: <id> merged ...; ticket NOT closed: its deployed copy is not current`
  (fr-2aed04): the ticket is labelled `tooling` and the repo's
  `bin/deploy close-check` found its packages not deployed current. This is
  the normal merge-then-deploy order, not a fault: deploy and verify the
  packages the lines above name (from the main checkout), then run the
  `pm ticket close ...` command the line ends with. Only when the deploy
  truly cannot happen now, close with `--no-deploy-check '<reason>'`.
- A line starting `wt:` is a failure. It names the exact next step, and when
  it ends `(reported: <path>)` the fault is already recorded in the
  deduplicated infra-faults report: do not file a ticket for it. Run the
  step if it is yours; otherwise hand it over as one plain line plus a fenced
  block of commands and `#` comment lines, and keep working.
- `finish` **auto-parks** when the rebase conflicts or the ff-only merge
  still fails after three tries: the ticket is `done-unmerged`, the branch is
  kept, the worktree is gone. Resume later with `wt start`.
- After ANY park the worktree directory is gone immediately -- the designed
  contract (fr-228b69; the resume line is `wt start && wt finish` precisely
  so it needs no path). An `ls` of the old path failing, or `wt status` not
  listing a just-parked ticket while `wt pending` does, is normal, not data
  loss: status reads live worktrees, pending reads `done-unmerged` tickets.
  Do not investigate, do not recreate the dir.
- `ticket <id> is not claimable` from `start` means taken or refused: pick
  other work, never retry the claim.
- A `.local is non-empty` refusal from `park`: that is operator content; stop
  and report it to the operator.
- `worktree for <id> is gone but its leftover registration (admin dir ...)
  could not be deleted in this sandbox; branch <id> is kept until then; wt
  prune clears it ... This is infrastructure, not a finding: file no ticket
  and write no retro.` is the deferred teardown, a success. The
  `OK: <id> merged into main, worktree removed; registration and branch
  deferred to wt prune, ticket closed` line follows and the ticket is
  already closed or released. Run `wt prune`; if it reports remaining
  registrations, hand the operator its `!git -C <repo> worktree prune`
  line. Never run `git worktree prune` or `git branch -d` by hand, and never
  file a ticket for it (the `*-teardown-deferred` rows are informational
  debt).
- `merged ... but git worktree remove ... failed` (the `STOP.` line, any
  failure that is not the admin-dir `Operation not permitted` with the tree
  gone): the ticket is still claimed. Report the error verbatim. The
  leftover directory is recovered by whoever the report reaches
  (`git worktree prune`, delete the residue, `git branch -d`), outside the
  sandbox that refused the delete.
- A stale worktree of your own (ticket already closed and merged):
  `wt finish <ticket-id>`. If its last line reports the ticket close failed
  because the ticket is already closed, the cleanup is done.
- On `.git/index.lock` (a `pm ticket` commit collided with yours): wait a
  few seconds and re-run the verb. Never delete the lock file.

## What the hooks deny (cl-437a2f, cl-e55503)

On Claude, core-hooks back the skill's rules mechanically; on Codex the
rules are the instructions alone.

- `rm -r` of `.worktrees/<id>` or `.worktrees` itself is denied: rm takes
  the uncommitted work and leaves the registration and branch behind.
  `rm -r` below a worktree root still asks; a worktree's own `.tmp/` is its
  scratch and passes.
- `git branch -D` (any force-delete spelling) is denied unless
  `git cherry main <branch>` prints no `+` line: a parked ticket's branch is
  the only copy of its work. Any other unmerged delete is the operator's call.
- `git worktree remove --force` asks on Claude and is forbidden on Codex:
  `--force` deletes modified and untracked files.
- `git switch` and `git stash` on the main checkout, and `git add -A` / `.`
  anywhere, are denied.

## Claude sandbox notes

- **`wt` is allow-listed** (`wt *` in posture); it runs with no prompt.
- **Deny-path budget (E2BIG).** Each registered worktree adds about three
  filesystem deny paths to the Bash sandbox profile. Near 220 deny paths the
  exec line crosses the OS limit and *every* sandboxed command fails `E2BIG`,
  whatever its content. The deny list is built at session start and rebuilt
  on a settings-file change or `/cd`, so mid-session teardown bounds the
  peak, not the current count. Budget one session restart (or `/sandbox`)
  into any phase that churns more than two or three worktrees.
- **Linked-worktree admin dirs (`.git/worktrees/<id>`).** The CLI's built-in
  git-dir protection also covers them: `rmdir` and `mkdir` of the directory
  itself are refused, and no `allowWrite` lifts it (fr-ca78c3, fr-614c4f).
  Whether a session may delete one depends on timing: an admin dir created
  mid-session is deletable until a settings-file change (for example another
  session's posture deploy) rebuilds the sandbox, after which that same
  session gets `EPERM` for every admin dir registered at the rebuild
  (observed 2026-11-07, deny list 97 -> 112). `wt` handles it with deferred
  teardown and `wt prune`; excluding `wt` from the sandbox is rejected
  (fr-614c4f: a tracked, agent-writable `core.hooksPath` would run
  agent-written hooks unsandboxed). Probe
  (`docs/programs/frontier-tooling/followups/wt-sandbox-teardown/reports/01-probe.md`),
  phase 1: `git worktree prune` deletes a plain `.keep` file and keeps a
  `.keep/` directory holding `locked`; `git branch -d` refuses a branch held
  by a prunable registration; `git worktree add` dies `missing but already
  registered worktree`. Phase 2 (fresh-session behaviour) is still pending.
- **`.vscode` segment deny.** The sandbox denies any literal `.vscode` path
  segment, for writes and deletes. A tracked `.vscode/*` file makes
  `git worktree add` fail (`Operation not permitted`, then
  `fatal: Could not reset index`) and makes `git worktree remove` fail
  destructively. Fix once per repo: untrack the file and gitignore
  `.vscode/`. The `.claude/` segment behaves the same on teardown: a
  worktree whose checkout contains `.claude/` leaves residue on a sandboxed
  remove; the operator finishes it with `git worktree remove --force`.
- **`.git/config` and `.git/hooks` are write-denied.** A sandboxed
  `git branch -d` prints `could not write config file .git/config` and
  `update of config-file failed` but still deletes the branch (exit 0); that
  is expected. `git init` cannot run sandboxed at all (`wt selftest` builds
  its throwaway repo under `~/.claude/.tmp` for that reason).
- **Stay rooted in the main checkout.** Don't `cd`; address the worktree
  with `git -C .worktrees/<ticket-id> ...`. Commits there pass the git guard
  with no git-pairs entry (measured 2026-09-28, fr-efff63); if one is ever
  denied, hand the operator that denial's named remedy.

## Codex sandbox notes

- **Profile.** Worktree lifecycle writes `.git` (refs, `.git/worktrees/`,
  objects), which only the default `repo-maintainer` permission profile
  grants. Under the `repo-secret-safe` floor the commands fail; stop and
  report instead of asking for escalation.
- **Session root.** The writable workspace root is the directory the session
  was launched from. Launch Codex at the main checkout, not inside
  `.worktrees/<ticket-id>`, so that both `.worktrees/` and `.git/` are inside
  it, and `wt` resolves the right repo.
- **No escalation for the lifecycle.** `wt` and the git and `pm ticket`
  commands it runs all work inside the sandbox with no rule. An escalation
  prompt for one of them means the session root or profile is wrong; fix
  that, never ask for "always allow" (an allow rule runs the command outside
  the sandbox).
- **Directory deletes are the fragile part.** Codex's seatbelt refuses every
  directory `rmdir`/rename in the workspace, and escalation does not lift it,
  whenever the active profile carries a `**/<x>` deny glob (measured on
  codex-cli 0.153.2, cl-d9e36a); posture therefore emits only `<x>` and
  `*/<x>`. A `.worktrees/*/<x>` deny refuses deletion of every
  `.worktrees/<id>` directory (measured, fr-64cef3), so a worktree root
  carries no secret denies: files there, and anything deeper than one level
  below the repo root, are readable. If a `wt` teardown reports
  `failed to delete '...': Operation not permitted`, that is the posture
  regressed, not a job for `rm -rf`: report it.
- **Store and session.** Start as actor `codex`: `wt start <id> --as codex`.
  `wt start` passes `--session` through to `pm ticket claim`, defaulting to
  `$PM_SESSION_ID` or `$CODEX_THREAD_ID` (cl-322003), so the claim is
  attributable with no extra flag. If neither is set, pass it explicitly:
  `wt start <id> --as codex --session <id>`; otherwise the claim is a bare
  `codex` name and the session should name the ticket it started in its
  final response so the next session can tell it is its own.

## Layout

```
cli/wt          entrypoint; resolves its own path, dispatches to src/
src/wt_core.py  the six verbs
src/crossrepo.py cross-repo mutation guard (see its docstring for scope)
src/faultreport.py deduplicated infra-fault report writer
tests/          pure-function and lifecycle tests
```

## Cross-repo

wt's own verbs never cross a repo boundary (worktrees are always created
inside the repo wt was invoked in). `crossrepo.refuse()` is still called
before every mutating git subprocess so wt can never become a silent
bypass of the git-pairs policy (`hooks/core-hooks/lib/gitguard.py`,
`~/frontier/config/claude/git-pairs.json`) if a future caller ever hands
it a real cross-repo pair. See `src/crossrepo.py`'s docstring for the
documented gap: the pairs data file currently deploys to Claude only
(`config/claude/.deploy.json`), so on Codex the guard fails closed (no
pairs declared) exactly as gitguard's own loader does for a missing file.
`tests/test_crossrepo.py` asserts parity against gitguard's own pure
functions on the cases this module covers.
