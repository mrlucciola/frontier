# INITIATIVE: wt rewrite (fc-262fa8)

## State

```text
fc-262fa8  P2  open          wt rewrite: self-contained zsh component in frontier-clean/wt, one file per verb [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-30c060  P2  open          wt characterization suite: black-box tests proven green against the old wt
  fc-122c0d  P2  open          wt core: zsh dispatcher and lib (git, pm, fail, config), verb table
  fc-8ecb48  P2  open          wt verb: start (take, resume, adopt own ticket, quiet prune)
  fc-249727  P2  open          wt verbs: finish and land (gate, rebase, ff-only merge, teardown, done)
  fc-917232  P2  open          wt verb: park (WIP commit, park or drop, teardown)
  fc-983ff4  P2  open          wt verbs: status prune
  fc-8c1f62  P2  open          wt integration: suite green on the redesigned pm, selftest, component docs, readability review
  fc-347c67  P2  open          wt pm plugin: refuse a direct done while a worktree exists, hint after take, orient lines
```

## Next batch

fc-30c060, alone, in four serial worker parts on branch `fc-30c060` (fc-2a6562 closed
2026-11-14; transcripts passed 25, failed 0 on the overseer's re-run):

1. `prompts/00-characterize-1-start.md` -- runner, two-sided adapter, repo fixture,
   `start`. Done: 29e8a2a, overseer re-run passed 20, failed 0.
2. `00-characterize-2a-finish-gate.md` -- `finish` and `land`: gate, known red, findings,
   notes, dirty refusal, land. In flight.
3. `00-characterize-2b-finish-merge.md` -- rebase-conflict auto-park, ff-only retry,
   refusal after the merge, merged marker, nested-repo and `.vscode` refusals, failed
   remove `STOP.`, deferred teardown.
4. `00-characterize-3-park.md` -- `park`.
5. `00-characterize-4-status.md` -- `status`, `prune`, `pending` (old side only), store
   and repo resolution, plus `start` leftovers: quiet prune, re-run with the worktree
   present.

Then a read-only reviewer maps the suite to `wt/docs/contract.md` section by section.

## Owed operator actions

None.

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
- **Old-side isolation knobs** (from the old `cmd_selftest`): `PM_STORES_FILE` (old
  registry), `PM_TELEMETRY_DIR=-`, `GIT_PAIRS_FILE` (old crossrepo guard). New pm:
  `PM_STORES`, `PM_PLUGINS`.
- **Structure check.** `docs/contributing.md` carries an `A-RUN` exemption row for wt
  until tests exist. fc-8c1f62 deletes the row.
