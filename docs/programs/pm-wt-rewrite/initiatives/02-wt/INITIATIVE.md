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
  fc-122c0d  P2  open          wt core: zsh dispatcher and lib (git, pm, fail), verb table
  fc-8ecb48  P2  open          wt verb: start (claim, resume, adopt own claim, quiet prune)
  fc-249727  P2  open          wt verbs: finish and land (gate, rebase, ff-only merge, teardown, close)
  fc-917232  P2  open          wt verb: park (WIP commit, close --unmerged or release, teardown)
  fc-983ff4  P2  open          wt verbs: status pending prune
  fc-8c1f62  P2  open          wt integration: suite green on the rewritten pm, selftest, component docs, readability review
```

## Next batch

fc-30c060, alone.

## Owed operator actions

None.

## Facts not to re-derive

- **No oracle exists yet.** The old `tests/test_wt_core.py` (78 tests) imports `wt_core`
  and patches its internals. It is reading material for what to cover, not a gate.
- **Old source sizes.** `cli/wt` 135, `src/wt_core.py` 2772, `src/crossrepo.py` 169,
  `src/faultreport.py` 78.
- **The old wt reads tickets as JSON** (`pm ticket show --json`). The zsh wt reads
  `pm ticket show <id> --field <name>` instead, which the pm rewrite added. If a field
  wt needs is missing there, that is a pm ticket, not a JSON parser in zsh.
- **Sandbox and git.** The old README records that `git init` cannot run sandboxed in
  some locations and that the old `selftest` builds its repo under `~/.claude/.tmp`.
  The pm parity suite does run `git init` under its temp directories inside the
  sandbox, so try the suite's temp directory first.
- **Teardown under the sandbox.** Removing a worktree's admin directory can fail with
  `Operation not permitted` depending on when the sandbox was last rebuilt. The contract
  treats that as deferred teardown, not a failure. A characterization test must accept
  both the clean and the deferred `OK:` line where the contract allows both.
- **Fault reports.** The old wt appends to `~/frontier/docs/backlog/inbox/infra-faults/`.
  Tests point `$WT_FAULT_DIR` at a temp directory once the new wt honors it; against
  the old wt, a test that provokes a fault row checks whether the old code has an
  override before running, and is listed in `wt/docs/uncovered.md` if it has none.
- **Root README.** The wt row in the component table is added by fc-8c1f62.
