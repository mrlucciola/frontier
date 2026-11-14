# INITIATIVE: wt rewrite (fc-262fa8)

## State

```text
fc-262fa8  P2  open          wt rewrite: self-contained zsh component in frontier-clean/wt, one file per verb [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-30c060  P2  closed        wt characterization suite: black-box tests proven green against the old wt
  fc-122c0d  P2  claimed       wt core: zsh dispatcher and lib (git, pm, fail, config), verb table [@agent:claude/claude#95c6eaa1]
  fc-8ecb48  P2  open          wt verb: start (take, resume, adopt own ticket, quiet prune)
  fc-249727  P2  open          wt verbs: finish and land (gate, rebase, ff-only merge, teardown, done)
  fc-917232  P2  open          wt verb: park (WIP commit, park or drop, teardown)
  fc-983ff4  P2  open          wt verbs: status prune
  fc-8c1f62  P2  open          wt integration: suite green on the redesigned pm, selftest, component docs, readability review
  fc-347c67  P2  open          wt pm plugin: refuse a direct done while a worktree exists, hint after take, orient lines
```

## Next batch

fc-30c060, alone, in five serial worker parts on branch `fc-30c060` (fc-2a6562 closed
2026-11-14; transcripts passed 25, failed 0 on the overseer's re-run):

1. `prompts/00-characterize-1-start.md` -- runner, two-sided adapter, repo fixture,
   `start`. Done: 29e8a2a, overseer re-run passed 20, failed 0.
2. `00-characterize-2a-finish-gate.md` -- `finish` and `land`: gate, known red, findings,
   notes, dirty refusal, land. Done: 38634fa, overseer re-run passed 40, failed 0.
3. `00-characterize-2b-finish-merge.md` -- rebase-conflict auto-park, ff-only retry,
   refusal after the merge, merged marker, nested-repo and `.vscode` refusals, failed
   remove `STOP.`, the `findings()` reader 2a lacked. Done: 3a4b9fe, overseer re-run
   passed 51, failed 0.
4. `00-characterize-3-park.md` -- `park`, plus deferred teardown through a PATH `git`
   shim (ruling below). Done: 85d68fa, overseer re-run passed 73, failed 0;
   `uncovered.md` deleted, nothing uncovered.
5. `00-characterize-4-status.md` -- `status`, `prune`, `pending` (old side only), store
   and repo resolution, plus `start` leftovers: quiet prune, re-run with the worktree
   present, `park --waits-on <ticket-id>`. Done: 8cbfd20, overseer re-run passed 95,
   failed 0.
6. `00-characterize-5-newside-fixes.md` -- the overseer's new-side check (the suite on
   `--pm new` against `.tmp/wt-unbuilt-stub`, which answers every verb exit 70) printed
   `passed 9, pending 83, skipped 1, failed 8`: a subtest table reusing prefix `tk`
   (the new `pm init` registers prefixes) and a `Pending` inside `subTest`, plus the
   two-owners case. Done: 51c9993; overseer re-run on the stub printed `passed 9,
   pending 84, skipped 2, failed 0`.
7. Read-only reviewer (qa-engineer, opus) mapped the suite to `wt/docs/contract.md`:
   `reports/00-review.md`, PARTIAL, about 20 gaps. All accepted. Closed by
   `00-characterize-6a-review-finish.md` (finish, land, teardown, guard, fault rows)
   then `00-characterize-6b-review-rest.md` (sessions, start hint, where failures,
   refusal words, nested variants, selftest, guard on park), serial after 6. 6a done:
   f82be24, 111 tests; stub run `passed 9, pending 100, skipped 2, failed 0`. 6b
   done: c85a178, 123 tests; stub run `passed 9, pending 112, skipped 2, failed 0`.
8. Re-review in flight (qa-engineer, read-only): coverage again, plus every assertion
   a correct new wt could not pass (old-pm or JSON-config words). Known one:
   `test_malformed_gate_refuses` pins the old JSON-gate words on both sides. Done:
   `reports/00-review-2.md`, PARTIAL: 10 new-side blockers, 6 weak spots.
9. `00-characterize-7-review2-fixes.md` -- side-neutral assertions under the rulings
   below, last gaps. Done: fc28c3f.

**fc-30c060 accepted at fc28c3f (overseer, 2026-11-14).** Gate on the overseer's re-run:
`wt suite: passed 125, pending 0, skipped 0, failed 0` (old wt, old pm). New side
against `.tmp/wt-unbuilt-stub`: `passed 9, pending 114, skipped 2, failed 0`.
`docs/check_structure.py`: ok. `wt/docs/uncovered.md` does not exist: nothing
uncovered, so the characterization stop does not apply. From here
`wt/tests/test_wt_cli.py` is read-only for workers.

fc-30c060 closed by `wt finish` with `--findings fc-f0cc16`.

**fc-122c0d (core), alone, two serial workers on branch `fc-122c0d`:**

1. `prompts/01a-core.md` -- dispatcher, `git` `pm` `fail` `config` libs,
   `crossrepo.py`, `findings_required.py`. Done: bd0b0c6; stub-free suite run on the
   new side `passed 9, pending 114, skipped 2, failed 0`. Convention: the dispatcher
   sources every `tools/lib/*.zsh`, then the verb file, then calls `wt_verb "$@"`;
   `land` maps to `verbs/finish.zsh` with `WT_VERB=land`. Overseer check of the new pm:
   `pm get <id> store` prints the repo root; an unregistered prefix exits 1 with
   `pm: no store has prefix <p>`; from a directory with no store, routing fails
   (filed fc-0d0f1e). For the lib review: `wt_resolve_repos` falls back to the cwd
   repo on any `pm get` failure, where the contract wants that only for "no store has
   prefix"; pm missing must stop with `wt: could not run \`pm `.
2. `prompts/01b-teardown.md` -- `teardown.zsh` (keep entry, deferred and `STOP.`
   lines, undeletable paths, merged marker, prune of debt). Overseer split: these are
   shared by finish, park, prune and start, which meets principle 2's three-verb bar.

   Done: b445660 (`teardown.zsh`, 306 lines); suite on the new side `passed 9,
   pending 114, skipped 2, failed 0`.

Then a read-only check of the lib against component-principles and the old code,
because five parallel step-2 workers build on it and may not edit it. Done:
`reports/01-review.md`, BROKEN: `local path=` in `pm.zsh` clobbers zsh's `$PATH`
array (every `--store`/`--repo` call), the any-failure fallback, stderr mixed into
values, untrimmed err text, fault-row escaping, changed output lines, and six helpers
under principle 2's three-caller bar.
3. `prompts/01c-review-fixes.md` -- all findings. Done: 4635204. Overseer gate:
   `zsh -n` on `cli/wt`, `pm.zsh`, `git.zsh`, `fail.zsh`, `teardown.zsh` all exit 0;
   worker's full new-side run `passed 9, pending 114, skipped 2, failed 0`; check
   structure ok. fc-122c0d accepted. The final function list is in
   `reports/01c-review-fixes.md`. Rulings: `config.zsh` is
   deleted (gate and known red have one user, finish); `wt_findings_required` stays
   shared by finish and park, a proposed amendment to principle 2 for fc-121923; the
   one-line pm wrappers go, verbs call `wt_pm` directly.

Step-2 order (overseer, 2026-11-14): every suite test starts with `wt start`, so batch A
is fc-8ecb48 (start) and fc-347c67 (pm plugin); batch B, after start merges, is
fc-917232 (park), fc-983ff4 (status, prune) and fc-249727 (finish); merge park before
finish. `finish` auto-parks through `wt park <id> --auto` as a subprocess (interface in
`prompts/02-common.md`).

## Owed operator actions

None. (The fc-122c0d scratch cleanup was done by the operator on 2026-11-14; `wt
finish fc-122c0d` then merged and closed it.)

Batch A: fc-8ecb48 (`prompts/02a-start.md`) in flight, round 2. Round 1 (c592b74)
found a core bug from 01c: `${${(f)found}[-1]}` took the last character of `pm get`'s
output. Overseer fixed it on the start branch (c865198, `${found##*$'\n'}`); StartTest
then reached `start.zsh` and failed on its own `status` variable (read-only in zsh). fc-347c67
(`prompts/02e-pm-plugin.md`) closed: 54f697d, overseer re-run of
`pm/tests/run_transcripts.py --dir wt/tests/t` passed 3, failed 0. Its report was not
in the worker-brief shape; the artifacts were verified on disk instead.

fc-8ecb48 closed after round 2 (9fccaab): overseer re-run StartTest passed 17, pending 1
(on park), failed 0; full suite exit 0.

Batch B in flight, three parallel workers: fc-917232 (`02c-park.md`), fc-983ff4
(`02d-status-prune.md`), fc-249727 (`02b-finish.md`). Merge park before finish, then
re-run finish's auto-park tests on main.

## Facts not to re-derive

- **Rewritten 2026-11-14.** Every child's body was rewritten for the redesigned pm,
  and fc-347c67 was added for wt's pm plugin. An edit-trail note on each ticket holds
  its previous body.
- **No oracle exists yet.** The old `tests/test_wt_core.py` (78 tests) imports `wt_core`
  and patches its internals. It is reading material for what to cover, not a gate.
- **Old source sizes.** `cli/wt` 135, `src/wt_core.py` 2772, `src/crossrepo.py` 169,
  `src/faultreport.py` 78.
- **How wt talks to the new pm.** Reads: `pm get <id> status holder store ...`, one
  value per line. Changes: `pm take`, `pm done`, `pm park`, `pm drop`. wt's own facts:
  `pm emit <id> wt.<name> key=value`, read back with `pm get <id> wt.<key>`. A check
  that changes nothing: `--dry-run`. wt sets `WT_CALLER=1` around its own calls so its
  `pre-done` plugin file lets them through.
- **Word map between the two pms.** claimed is taken; done-unmerged is parked; closed
  is done; `claim` is `take`; `close` is `done`; `close --unmerged` is `park`;
  `release` is `drop`; `pm ticket where <id>` is `pm get <id> store`.
- **Configuration moves out of JSON.** The old wt reads `gate` and `known_red` from
  `.pm/config.json`. The new one runs an executable `.wt/gate` and reads
  `.wt/known-red`, one `<ticket id> <text>` per line. Only the lai store sets `gate`
  today.
- **Dropped.** `wt pending`: parked tickets are `pm ls parked`. The deploy check that
  made the old pm exit 4 is now someone's `pre-done` plugin; to wt it is one more
  reason `pm done` can refuse after a merge.
- **Sandbox and git.** `pm/tests/run_transcripts.py` runs `git init`, commits and
  `git worktree add` under its temporary directory inside the sandbox. Start there.
- **Teardown under the sandbox.** Removing a worktree's admin directory can fail with
  `Operation not permitted` depending on when the sandbox was last rebuilt. The contract
  treats that as deferred teardown, not a failure. A characterization test accepts both
  the clean and the deferred `OK:` line where the contract allows both.
- **Fault reports.** The old wt appends to `~/frontier/docs/backlog/inbox/infra-faults/`
  unless `$WT_FAULT_REPORT_DIR` is set (`src/faultreport.py:37`). Ruling (overseer,
  2026-11-14): the new wt honors the same variable name, so the suite sets one
  variable for both sides.
- **Malformed gate on the new side.** Ruling (overseer, 2026-11-14): a `.wt/gate` that
  exists but is not executable refuses `finish` and `land`, as a non-list `gate` does
  on the old side. The adapter's `set_gate(malformed=...)` writes one.
- **Adoption needs actor and token (for fc-8ecb48).** The new pm calls a ticket "yours"
  when the tokens match, whatever the actor. The contract refuses a different actor
  with the same session (`StartTest.test_refuses_foreign_claim_other_actor`), so the
  new `start` compares the actor as well as the token before adopting.
- **`PM_AGENT=claude/worker` in the suite's env.** Without it the old pm writes
  `human:<actor>` claims, which `start` never adopts. The new pm ignores it.
- **Deferred teardown is covered, not uncovered.** Ruling (overseer, 2026-11-14): the
  suite fakes git's EPERM reply with a `git` shim first on `PATH`, as the old
  selftest's `deferred_remove_git` does in-process. 2b had listed it in `uncovered.md`.
- **Old wt vs contract, for the acceptance ruling.** 2b pinned these as the old wt
  behaves: (1) `wt start` on an auto-parked rebase-conflict ticket rebases again,
  conflicts again, removes the worktree and exits 1, so the agent cannot resolve the
  conflict through wt, though the contract says "Resume later with `wt start`"
  (`test_rebase_conflict_auto_parks`); (2) after a failed remove, git has already
  dropped the registration, and `wt finish` says `nothing to finish` with the ticket
  still taken. The `--force` in the `STOP.` line's operator-run cleanup matches the
  contract's per-shape handoff; it is not a contradiction.
- **Two owners is old-side only.** Ruling (overseer, 2026-11-14): the new pm routes a
  shared prefix itself (design.md, "Ids and the registry"), so the two-owners refusal
  test skips on the new side. The new side's gate expects exactly two skips: that and
  `pending`.
- **More pins from part 4, for the acceptance ruling.** `wt start` twice from the same
  session: the old wt adopts, then fails in `git worktree add` (exit 1, fault row).
  Every cross-repo call (`--store`/`--repo` to another repo, a prefix registered
  elsewhere) is refused unless `GIT_PAIRS_FILE` declares the pair; the suite declares
  pairs. The contract's resolution section does not mention it.
- **The cross-repo guard is kept.** Ruling (overseer, 2026-11-14): the new wt refuses
  an undeclared cross-repo mutation and reads the pairs from `$GIT_PAIRS_FILE` in the
  old shape, so the suite pins one behavior on both sides.
- **Fault rows as the old wt writes them (pinned in 6a).** One file per root cause and
  day, one row appended per occurrence; that file is the "deduplicated report". A
  non-infra refusal (cross-repo, mass-deletion resume) ends `(reported: <path>)`; an
  infra one (rebase conflict, `STOP.`, deferred) says `Recorded in <path>. This is
  infrastructure, not a finding`.
- **More pins from 6b, for the acceptance ruling.** A stale worktree whose ticket is
  already closed is NOT torn down by the old `finish` (its preflight `pm ticket where
  --mutate` refuses; exit 1, worktree and branch kept), against contract.md:198-200.
  The old `selftest` leaves three `wt-selftest-*pairs*.json` files in `$TMPDIR`.
- **Rulings on old wt vs contract (overseer, 2026-11-14, part 7).** Where the old wt
  contradicts the contract, a test pins the old wt on the old side and the contract on
  the new side, with a docstring starting `Old wt deviates from the contract:`. Applied
  to the stale worktree of a closed ticket (contract.md:198-200). Kept on both sides,
  changed later by fc-f0cc16: `wt start` re-conflicting on an auto-parked rebase
  conflict. Fault rows: one file per root cause, at least one row. `start` twice: state
  only, exit not pinned. The gate prints `.wt/gate` as its label on the new side.
- **The pairs check is Python.** Ruling (overseer, 2026-11-14): `$GIT_PAIRS_FILE` is
  JSON and zsh never parses JSON, so the guard is a stdlib helper
  `wt/tools/lib/crossrepo.py` that `fail.zsh` calls (principle 3). The same goes for
  reading `findings_required` from `.pm/config.json`. `pm done --dry-run` is not the
  findings check: it runs `pre-done` plugins too, which would move the after-merge
  guard refusal to before the merge.
- **Step-2 workers do not edit `wt/tools/lib/`.** A lib change one of them needs goes
  to the overseer, who makes it in a fix round, so the five can run in parallel.
- **Incident, 01b (2026-11-14).** The worker's hand driver ran `git init` under the
  worktree's `.tmp/`; the sandbox refused it (it denies a nested `.git/config` there),
  and the git commands that followed hit the real frontier-clean repository: a stray
  commit on fc-122c0d, branches `t1` and `t2`, a `t2` worktree, the keep entry, and a
  `git worktree prune` on the shared repo. The worker undid it. Overseer check after:
  `git worktree list` shows only main and fc-122c0d, no `t1`/`t2`, no `refs/wt/*`, and
  fc-122c0d is bd0b0c6 then b445660. Not provable: whether that prune removed another
  session's stale registration. Rule for every later prompt: throwaway repos live under
  `$TMPDIR` (as the suite's do), and a driver stops if `git init` fails.
- **Old-side isolation knobs** (from the old `cmd_selftest`): `PM_STORES_FILE` (old
  registry), `PM_TELEMETRY_DIR=-`, `GIT_PAIRS_FILE` (old crossrepo guard). New pm:
  `PM_STORES`, `PM_PLUGINS`.
- **Structure check.** `docs/contributing.md` carries an `A-RUN` exemption row for wt
  until tests exist. fc-8c1f62 deletes the row.
