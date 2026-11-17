# wt contract

Reference for the `wt` command: its verbs, refusals and output lines. The suite
`wt/tests/test_wt_cli.py` is the authority on exact wording.

A worktree always lives at `<repo>/.wt/<id>` on branch `<id>`, one per ticket, beside
wt's committed config `.wt/gate` and `.wt/known-red`.
`wt` talks to [pm](/pm/README.md) only through its command line: `pm get`, `pm take`,
`pm done`, `pm park`, `pm drop` and `pm emit`, with `WT_CALLER=1` set on each call so
the plugin's guards let wt through.

## Verbs

```
wt start <id> [--as NAME] [--force]    # take via pm (or adopt own claim), add/resume the worktree
wt finish <id> [--note TEXT] [--findings VALUE] [--keep-open] [--no-gate]
                                       # gate, rebase, ff-only merge, teardown, pm done
wt land <id> [--no-gate]               # = finish --keep-open: merge + teardown, ticket stays taken
wt park <id> [--waits-on <id-or-note>] [--note TEXT] [--findings VALUE]
                                       # commit WIP, pm park, teardown
wt status                              # worktree list joined against tickets
wt prune                               # clear deferred-teardown registrations, delete their merged branches
wt selftest                            # full lifecycle in a throwaway repo; prints SELFTEST PASSED
```

`--as` defaults to `$WT_ACTOR` when set; without either, `start` refuses.

`finish` and `park` pass `--note` and `--findings` straight to `pm done` and
`pm park`; each is omitted when not given. On `park`, `--note` is prepended to the
generated branch/sha/resume note (the resume line stays last). A zero-delta park
releases the ticket (`pm drop`) instead of parking it, so it records neither and says so.

`finish --keep-open` (`wt land`) does everything `finish` does, with the same
refusals (dirty worktree, store/repo guard, rebase conflict, ff-only exhaustion), merge,
worktree and branch removal, but skips `pm done`: the ticket stays taken, for a
long-lived ticket whose records must reach the default branch every turn. It rejects
`--note` and `--findings`. To keep working, run `wt start <id>` again from the same
session: it adopts the existing claim.

`start` adopts a ticket already taken by the claim it would itself write (same actor and
same session token: `--session`, else `PM_SESSION_ID`, else `CODEX_THREAD_ID`, else
`CLAUDE_CODE_SESSION_ID`), prints one `adopting existing claim` line and skips the take.
A different token, a different actor, or a bare-name claim refuses. `wt start --force`
passes `--force` to `pm take` (blocked ticket, operator-sanctioned only); end a
force-taken ticket with `wt park`, never `wt finish` (start prints a reminder; not
enforced).

`start`, `finish`, `park`, `status` and `prune` also take `--store <path>` and
`--repo <path>`. `start`, `finish` and `park` find the store with `pm get <id> store`
from the cwd repo. When pm says no registered store owns the prefix, the store is the
cwd repo; any other failure stops with pm's message. `--store` overrides the lookup
(needed only for a store the registry does not list) and the worktree target then
defaults to the store repo. `--repo` overrides the worktree and git target
independently.

## Facts wt records

`wt` writes `pm emit <id> wt.start branch=<id> path=<path>`, `wt.merged sha=<sha>` and
`wt.park sha=<sha> [findings=...]`, readable with `pm get <id> wt.<key>`.

## Gate

`finish` and `land` run an executable `<repo>/.wt/gate` in the worktree, after the
dirty-worktree check and before any rebase or merge. A non-zero exit refuses: nothing
merged, ticket stays taken, worktree intact, and the last 30 lines of output are
printed. Every run prints `gate .wt/gate exit N, SKIP lines: K` (output lines matching
`skip`/`skipped`, case-insensitive) so skipped tests can be reported as NOT PROVEN. A
`.wt/gate` that exists but is not executable refuses too: a typo never turns the gate
off. `--no-gate` (doc-only tickets) bypasses it and appends
`gate skipped (--no-gate): .wt/gate` to the done note (`land` has no done, so it only
prints the skip). No `.wt/gate`, no gate.

`<repo>/.wt/known-red` excuses an owned red: one `<ticket id> <text>` per line. A
failing line matching an entry passes (the done note says `known red <ticket>`); an
entry whose text stopped failing refuses until it is dropped. After the gate, the
ff-only merge from the main checkout is retried up to three times while the default
branch keeps moving under `pm` commits. `finish` and `park` warn when `--findings` is
missing, and refuse before any merge or teardown once the store sets
`findings_required`.

## Rules

- `park` removes the worktree and keeps the branch; it commits WIP first; a non-empty
  `<worktree>/.local` blocks the park.
- `wt` never runs `branch -D` or `worktree remove --force`, and never `rm -rf`. The one
  `rm -r` it runs is `selftest` removing its own scratch directory.
- Every failure prints one fixed line naming the exact next step and best-effort
  appends one deduplicated row to the fault report directory (`$WT_FAULT_REPORT_DIR`
  when set), never a per-incident ticket.
- A failed `git worktree remove` (finish or park) prints a `STOP.` line and never
  invites a retry, `--force` or a sandbox-disabled attempt; it hands the operator the
  cleanup commands. `park` refuses a worktree that is only deletions (more than 50) or
  has lost its `.git` file, and `start` refuses to resume a branch whose tip is a
  mass-deleting `WIP: park` commit. A successful ff-only merge of a branch with commits
  pins the tip in `refs/wt/merged/<id>`; `finish` and `park` on a branch whose tip
  equals that marker (and is in the default branch) tear down and finish the ticket,
  never park or drop it. The failed-remove handoff is per shape: dir gone -> `worktree
  prune`; partial tree -> operator-run `worktree remove --force`; `.git` file missing
  -> `rm -rf` then prune.
- `finish` and `park` refuse (before any merge, WIP commit or remove) a worktree
  holding a nested git repo (a `.git` dir with `config` or `hooks`) or a `.vscode` dir:
  the sandbox cannot delete those, so `git worktree remove` would leave a partial
  tree. The line names up to 5 paths and the operator-run `rm -rf` per path; no fault
  row. `start` appends a restart/resume hint when `git worktree add` fails with
  `.git/worktrees` "Operation not permitted".
- `git worktree remove` deletes silently when only git-ignored files remain dirty. That
  is why `park`'s `.local/` check is wt's own.
- A stale worktree of a ticket that is already done and merged is torn down by
  `wt finish <id>`.
- wt keeps its own settings (`.wt/gate`, `.wt/known-red`) out of pm's store.

## Deferred teardown and prune

When `git worktree remove` or `prune` fails with `Operation not permitted` on THIS
worktree's admin dir (`.git/worktrees/<id>`) and the working tree is already gone,
`finish` and `park` treat it as success with debt: the ticket is finished or released as
normal, the registration (and, on finish, the branch) is left behind, and one deferred
line says so. Before and after each teardown `wt` writes a keep entry (a directory
`.keep` holding an empty `locked` file) in the worktrees admin dir, so git never
deletes that directory itself. Every other remove failure keeps the `STOP.` line.

`wt prune [--repo R] [--store S]` keeps the keep entry, runs `git worktree prune`, then
deletes a branch only when `refs/heads/<id>` is an ancestor of the default branch and no
worktree holds it. `wt start` runs it quietly. If registrations remain it prints
`<n> deferred-teardown registration(s) remain; this session's sandbox denies deleting
them. Operator: !git -C <repo> worktree prune`: that is the operator's step, never the
agent's. `wt status` labels such an entry `deferred-teardown`.

## Reading wt output

- A line starting `OK:` is the verb's success. Nothing else to do.
- A line starting `wt:` is a failure. It names the exact next step, and when it ends
  `(reported: <path>)` the fault is already recorded: file no ticket for it. Run the
  step if it is yours; otherwise hand it over as one plain line plus the commands.
- `finish` **auto-parks** when the rebase conflicts or the ff-only merge still fails
  after three tries: the ticket is parked, the branch is kept, the worktree is gone.
  Resume later with `wt start`.
- After ANY park the worktree directory is gone immediately; the resume line is
  `wt start && wt finish` precisely so it needs no path. An `ls` of the old path
  failing, or `wt status` not listing a just-parked ticket (it reads live worktrees;
  `pm ls parked` reads tickets), is normal, not data loss. Do not recreate the dir.
- `ticket <id> is not claimable` from `start` means taken or refused: pick other work,
  never retry the take.
- A `.local is non-empty` refusal from `park` is operator content; stop and report it.
- `worktree for <id> is gone but its leftover registration (admin dir ...) could not be
  deleted in this sandbox; branch <id> is kept until then; wt prune clears it ... This
  is infrastructure, not a finding: file no ticket and write no retro.` is the deferred
  teardown, a success. The `OK: <id> merged into main, worktree removed; registration
  and branch deferred to wt prune, ticket closed` line follows. Run `wt prune`; if it
  reports remaining registrations, hand the operator its
  `!git -C <repo> worktree prune` line. Never run `git worktree prune` or
  `git branch -d` by hand.
- `<id> is already merged into <branch> but pm done failed (<reason>) ...`: the merge
  landed and a `pre-done` plugin or pm refused. Satisfy the reason, then run the
  `pm done` command the line ends with.
- `merged ... but git worktree remove ... failed` (the `STOP.` line, any failure that
  is not the admin-dir `Operation not permitted` with the tree gone): the ticket is
  still taken. Report the error verbatim; the operator recovers the directory outside
  the sandbox that refused the delete.
- On `.git/index.lock` (a `pm` commit collided with yours): wait a few seconds and
  re-run the verb. Never delete the lock file.
- `wt pending` answers `wt: no verb 'pending'. Parked tickets are listed by: pm ls
  parked`.

## Rules wt does not enforce

An agent follows these; wt cannot check them. `wt help` and `wt start` print the short
forms.

- The main checkout stays on its default branch and nobody switches it. Before every
  commit `git branch --show-current` prints the default branch there, or `<id>` in a
  worktree; if the main checkout is off its default branch, stop and report it.
- One ticket, one worktree, one branch, at `<repo>/.wt/<id>`: never under `.tmp/`,
  `.claude/`, `.codex/`, `.agents/` or outside the repo. Start it before the first edit;
  edit only under it. Never work a ticket you do not hold.
- Run `wt` from the main checkout (it resolves the main checkout from inside a linked
  worktree too). In a multi-agent run only the orchestrator runs `wt`; a worker edits and
  commits only in the worktree it was handed.
- Git in the worktree is `git -C <worktree> ...`, with explicit paths: never `git add -A`,
  `git add .` or `git commit -a`. Never `git stash` or `git switch` in the main checkout.
- `git branch -D` is allowed only when `git cherry <default> <branch>` prints no `+`
  line, with the command and its output in the ticket note.
- Before the session's final response, finish, park or release every ticket you hold,
  except one a failed teardown left taken: report that one.
- `<repo>/.tmp/` is disposable scratch (teardown takes it; never `rm` it). `<repo>/.local/`
  is durable uncommitted state: never delete, move or `git clean` it unless the user
  names that path. A fresh worktree has no installs or env files; whoever starts it makes
  it runnable and never copies secrets (`.env*`, `*.pem`, `*.key`, credentials) in.
  Gitignore `.tmp/`, `.local/` and `.wt/*`, keeping `!.wt/gate` and `!.wt/known-red`.
- Claude Code's built-in worktrees (`isolation: worktree`, `EnterWorktree`,
  `claude --worktree`) are for throwaway work that is never merged.
- A worktree with no ticket behind it is an orphan: report it, never remove it; only the
  session that created it or the operator removes it.

## Sandbox notes

Claude:

- `wt` is allow-listed (`wt *` in posture) and runs with no prompt. Each registered
  worktree adds about three deny paths to the Bash sandbox profile; near 220 every
  sandboxed command fails `E2BIG`. The list is built at session start, so budget one
  session restart into any phase that churns more than two or three worktrees.
- Admin dirs `.git/worktrees/<id>` may be undeletable depending on when the sandbox was
  last rebuilt (`EPERM` on `rmdir`); that is the deferred teardown above.
- The sandbox denies any literal `.vscode` path segment for writes and deletes. A
  tracked `.vscode/*` file makes `git worktree add` fail (`Operation not permitted`,
  then `fatal: Could not reset index`). Untrack it and gitignore `.vscode/`. A worktree
  whose checkout contains `.claude/` leaves residue on a sandboxed remove; the operator
  finishes it with `git worktree remove --force`.
- A sandboxed `git branch -d` may print `could not write config file .git/config` and
  `update of config-file failed` yet still delete the branch (exit 0); that is expected.
- Stay rooted in the main checkout; do not `cd` into a worktree.

Codex:

- Worktree lifecycle writes `.git`, so the session needs a profile that allows it; under
  a read-only floor the commands fail, so stop and report.
- Launch at the main checkout so `.wt/` and `.git/` are inside the writable root.
- Start as actor `codex`: `wt start <id> --as codex`. The session token defaults to
  `$PM_SESSION_ID` or `$CODEX_THREAD_ID`; if neither is set pass
  `--session <id>`, or the claim is a bare `codex` name.
- If a teardown reports `failed to delete '...': Operation not permitted`, the sandbox
  policy regressed; report it, do not `rm -rf`.
- `wt` and the git and pm commands it runs work inside the sandbox with no rule. An
  escalation prompt for one of them means the session root or profile is wrong; never ask
  for an allow rule, which would run the command outside the sandbox.

## Help and byte ceilings

`wt help` prints the verb table in `cli/wt`; `wt help <verb>` prints the leading comment
block of that verb's file under `tools/verbs/` (`land` prints finish's). Ceilings, all
bytes: `wt help` 1200, one verb's help 700, any failure line 400. The test
`tests/test_budgets.py` measures the first two and the usage failures on the real CLI and
every `wt_say` and `wt_fail` template in `tools/` with 24-byte stand-ins for variables;
it runs with
`/usr/bin/python3 -B -m unittest discover -s wt/tests -p 'test_budgets.py' -v`. Failure
lines that carry git's own error or an operator command list can exceed the ceiling with
long paths; the test does not see those.
