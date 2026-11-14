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

fc-30c060, alone, once fc-2a6562 is closed.

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
- **Fault reports.** The old wt appends to `~/frontier/docs/backlog/inbox/infra-faults/`.
  Tests point `$WT_FAULT_DIR` at a temporary directory once the new wt honors it;
  against the old wt, a test that provokes a fault row first checks whether the old
  code has an override, and is listed in `wt/docs/uncovered.md` if it has none.
- **Structure check.** `docs/contributing.md` carries an `A-RUN` exemption row for wt
  until tests exist. fc-8c1f62 deletes the row.
