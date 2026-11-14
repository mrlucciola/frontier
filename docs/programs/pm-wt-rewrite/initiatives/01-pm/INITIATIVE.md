# INITIATIVE: pm rewrite (fc-c3514f)

## State

```text
fc-c3514f  P2  open          pm rewrite: self-contained Python component in frontier-clean/pm, one file per verb [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-2b34c9  P2  open          pm core: store module, ticket entry with the kept-verb table, verbs init create show
  fc-459fe0  P2  open          pm routing: store registry, prefix routing, frozen stores, verbs where and stores
  fc-d73327  P2  open          pm lifecycle verbs: claim hold release close reopen
  fc-739601  P2  open          pm read verbs: list ready tree summary
  fc-c10bcf  P2  open          pm structure verbs: dep unlink reparent edit note, cross-store edges, create duplicate guard
  fc-c5e673  P2  open          pm history verb: status enable disable sync restore, commit modes
  fc-913d02  P2  open          pm checks and views: validate lint archive board overview
  fc-59011f  P2  open          pm integration: full parity green, golden diff on live stores, component docs, readability review
  fc-0817f6  P2  closed        pm parity: port upstream drift 505936d6..1ecfec0a (claim exit lines, lint <id>)
```

## Next batch

fc-2b34c9, alone, as four serial workers on its branch: `01-core-a` (entry, store,
init; dispatched), `01-core-b` (gitcommit; written), `01-core-c` (create, show),
`01-core-d` (test_cli_contract.py). Everything else is blocked behind it.

## Owed operator actions

None.

## Decisions (overseer)

- **Duplicate guard moves into fc-2b34c9** (2026-11-13). Left unbuilt, the guard
  would fire on nearly every `create` against a store with rows, so step-3 tests
  would sit pending on it and their workers could not prove their own verbs.
  `01-core-c` builds `find_duplicates`, the exit-2 refusal, `--new` and `--dup-of`
  in `create.py`. fc-c10bcf keeps only the cross-store `--discovered-from` edge in
  `create.py`.
- **gitfault report writer dropped** (2026-11-13): recorded in `pm/docs/cut-list.md`
  "What the cuts change".
- **Reverse cross-store blockers in text `show`** (2026-11-13): until fc-459fe0, `show`
  calls `store.unbuilt("routing")` only when the registry file lists a store; the
  suite's default registry is empty, so ordinary `show` is not pending.

## Facts not to re-derive

- **Baseline.** The trimmed suite ran against the old CLI at frontier `505936d6`,
  sandboxed: `Ran 269 tests in 241.429s`, `OK (skipped=9)`,
  `parity: passed 260, pending 0, failed 0, skipped 9`. Git repos created under the
  suite's temp directories work inside the sandbox. After fc-0817f6 the suite is
  pinned to `1ecfec0a` and runs 271 tests: 262 pass, 9 skip.
- **Upstream moves.** The old pm took four commits during preparation (typed notes,
  the archived-id refusal, the `history-pending` store entry, `list --all-stores`);
  all four are in the suite. `list --all-stores` belongs to fc-739601. `pm/docs/cut-list.md` has the drift command. Run it on your first turn and
  again in fc-59011f. New upstream tests on kept surface are ported by you, in a
  ticket of their own, never by a verb worker.
- **Drift at first launch (fc-0817f6).** Two upstream tests ported from `1ecfec0a`:
  `claim` ends with four exit lines (`CLAIM_EXITS` in the old `ticket`; fc-d73327),
  and `lint <id>` reports missing dispatch headings (fc-913d02). The spec copy is
  read-only here and lags upstream by SPEC.md section 5 prose only; `cut-list.md`
  quotes the `lint <id>` rule.
- **Typed notes are kept surface.** `note --kind`, the kinds `close` and `edit` write,
  and `show` hiding `edit-trail` notes unless `--all-notes` are in the parity suite;
  they are not named in the ticket bodies, which were written before the resync.
- **Deferred keys are live on this repo's store.** `.pm/config.json` here sets all three
  since 88103df. The installed pm honors them. If fc-9076a6 is a child of fc-c3514f
  when you start, the operator has ruled it into this run: schedule it in step 3,
  merge it after fc-c5e673 (both touch history commits), and it removes the nine
  `@DEFERRED` decorators. If it is not a child, leave it alone.
- **Compacted rows.** Whatever the ruling, fc-2b34c9 makes the store read epics that
  carry `subtasks`, answer `show` for a compacted id, and refuse mutations on it.
- **Run time.** The full suite takes about four minutes. Workers iterate with `-k` and
  run the full `--allow-pending` gate once before reporting.
- **The harness runs `[sys.executable, <cli>, <verb>, ...]`.** `pm/tools/ticket` must be
  a Python script with no extension that takes verbs directly.
- **Pending rule.** Proven with a stand-in CLI that builds nothing: ten tests reported
  `pending`, zero `failed`, and the run named the unbuilt verbs. A setUp that hits an
  unbuilt verb counts as pending too.
- **A reliable no-op.** `archive --closed-before 2000-01-01` on a store with no closed
  rows writes nothing and commits nothing. `reparent <id> --none` is not a no-op: it
  rewrites `updated`, so it commits whenever the clock second has moved.
- **Registry in tests.** The suite sets `PM_STORES_FILE` itself. Outside tests the new
  default, `~/.config/pm/stores.json`, does not exist until cutover, which reads as an
  empty registry.
- **Golden diff setup (fc-59011f).** Give both CLIs the same registry with
  `PM_STORES_FILE=/Users/matthias/frontier/runtime-tools/pm/stores.json`, and set
  `PM_TELEMETRY_DIR=-` so the old CLI writes no telemetry row. Ten stores are
  registered; `~/claude` is frozen. All ten are `spec_version: 2`.
- **Old source sizes** at `505936d6`, for the line-count note at close: `ticket` 3114,
  `ticket_core.py` 2783, `gitcommit.py` 220, `gitfault.py` 207, `board.py` 198,
  `overview.py` 165.
- **`show --field`** is new surface, specified in fc-2b34c9 and tested in
  `test_cli_contract.py`, not in the parity suite.
- **Root README.** The pm row in the component table is added by fc-59011f and by no
  earlier ticket.
