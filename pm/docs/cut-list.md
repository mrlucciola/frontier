# pm rewrite: what stays, what goes, what waits

Operator ruling, 2026-11-12. The rewrite keeps the on-disk format (spec v2,
[docs/spec/v2](/pm/docs/spec/v2/SPEC.md)) byte-compatible and changes only the code.

## Surface

| | Items |
| --- | --- |
| Kept verbs | `init create show list ready tree summary claim hold release close reopen note edit dep unlink reparent where stores history validate lint archive board overview` |
| Kept behavior | prefix routing and the store registry, frozen stores, cross-store edges, `legacy_prefixes`, `findings_required`, the `pm-store` history ref, the `bin/deploy close-check` contract (exit 4), `validate --workspace` |
| Dropped | `upgrade`, `adopt`, `fix-labels`, `notes-prune`, per-call telemetry, `intake/`, `integrations/mao.py` |
| Deferred | `compact_closed_after_days`, `archive_closed_after_days`, `history_interval_seconds` |

Every registered store is at `spec_version: 2`.

**The deferral needs a new ruling.** When the cut was ruled, no registered store
set a deferred key. Two hours later frontier-clean commit 88103df set all three
on this repository's own store (`history_interval_seconds: 900`,
`compact_closed_after_days: 7`, `archive_closed_after_days: 21`). The features
are new work in the old pm (frontier c86faab0, 2026-11-12) and now have a live
user. Until the operator rules again, they stay deferred in fc-9076a6, and that
ticket blocks the cutover runbook, so the switch cannot silently turn them off.

## Baseline and upstream drift

The old pm is still being changed. The parity suite matches frontier `944f3cda`. The first copy was taken at `c86faab0`; four upstream
commits landed during that work and were folded in at `505936d6`, two more
tests were ported at `1ecfec0a`: `test_claim_ends_with_the_four_exits` (claim
prints the four exit lines) and `test_lint_id_reports_missing_dispatch_headings`
(`lint <id>`), and one at `7fd60e5c`:
`test_lint_and_summary_enforce_the_pilot_contract` (`lint` reports P-01 and P-02
for tickets labelled `pilot`; `summary` prints `pilots overdue: <ids>`). At
`03b232d2` two assertions changed: refusals now end with a hint naming the next
command (`status_hint`, and `no such ticket: <id>` gains a hint naming `list` and
`create`). The same commit added `claim --reopen`, `close --via wt` (a direct
`close` is refused while `.worktrees/<id>` exists; the old wt passes `--via wt`),
and `reopen` refusing a claimed ticket. Their only upstream tests import
`ticket_core`, so the lifecycle ticket covers them in `tests/test_cli_contract.py`.
At `944f3cda` three tests were ported: `dep` takes several targets all-or-none,
`dep --note` lands on the target, and `create --blocks`/`--blocked-by` write edges.

The spec copies here still match `505936d6`. The one upstream change after it is
prose in SPEC.md section 5, not format: `lint <id>` reports each missing dispatch
heading, `Done`|`Gate`, `Writes`|`Files`, `Read first`|`Inputs`,
`Do not`|`Not in scope`, matched as a line starting `<name>:` case-insensitively,
as `missing: <canonical heading>` and exit 1, else `dispatchable` and exit 0; an
unknown id exits 1. The ported test pins that behavior.

Before the rewrite is declared at parity, the integration ticket runs this and
ports every new test on kept surface, with the count table below updated:

```sh
git --no-pager -C /Users/matthias/frontier diff --stat 944f3cda HEAD -- runtime-tools/pm/ticket/tests/test_ticket_cli.py runtime-tools/pm/ticket/spec/v2
```

Empty output means no drift.

## What the cuts change

- **Dropped verbs exit 2** as unknown verbs, like any other typo.
- **Stores below spec v2 are not readable.** `validate` still reports I-02 on a
  config that is not v2. Nothing migrates one; the old `upgrade` in
  `~/frontier/runtime-tools/pm` is the tool for that until cutover.
- **`validate` fix hints must not name a dropped verb.** Three hints did:
  I-02 on a pre-v2 config and a missing required key (`run: pm ticket upgrade`),
  and I-10 unsorted labels (`run: pm ticket fix-labels <id>`). The ticket that
  ports `validate` writes the replacement text.
- **Deferred keys stay legal.** They are in the frozen
  [config schema](/pm/docs/spec/v2/config.schema.json), so `validate` still type-checks
  them. They have no effect: every mutating op snapshots history, and closed
  rows stay in `tickets.jsonl` until `pm ticket archive` moves them.
- **Rows the old pm compacted must still read correctly.** Deferring the sweep
  does not defer the data. An epic may carry a `subtasks` array, `show <id>` of
  a compacted id answers from it with `compacted: true`, and every mutating verb
  on that id refuses. The parity suite has no test for this; the reference is
  the old `ticket/tests/test_ticket_core.py`, and the store-core ticket adds the
  CLI tests to `tests/test_cli_contract.py`.
- **A failed commit no longer files an infra-fault report.** Overseer ruling,
  2026-11-13. The old `gitfault.py` imported `signing_failure_report` from
  `~/.claude/hooks` to append a deduplicated report under frontier's
  `docs/backlog/inbox/infra-faults/`. A component does not import another's
  internals ([component principles](/docs/component-principles.md) rule 9), so
  that writer is dropped. The classifier stays in `tools/gitcommit.py`: an
  identity or signing failure still prints its one remedy line and a failed
  commit still exits 3.

## Parity suite

`tests/test_cli_parity.py` is the old `ticket/tests/test_ticket_cli.py`, trimmed.
It passes against the old CLI and is the gate for the new one.

| | Count |
| --- | --- |
| Tests in the old suite at `944f3cda` | 288 |
| Removed | 14 |
| Changed | 8 |
| Skipped as deferred | 9 |
| Run against the CLI under test | 265 |

Removed, with the dropped item each one covered:

| Test | Covered |
| --- | --- |
| `TicketCliTest.test_telemetry_row_per_invocation` | telemetry |
| `ValidateTest.test_fix_labels_lowercases_and_drops_what_stays_invalid` | `fix-labels` |
| `ValidateTest.test_upgrade_dry_run_leaves_store_untouched` | `upgrade` |
| `ValidateTest.test_upgrade_abort_leaves_original_untouched` | `upgrade` |
| `ValidateTest.test_upgrade_repairs_missing_closure_reason_on_v2_store` | `upgrade` |
| `ValidateTest.test_upgrade_does_not_invent_a_missing_title` | `upgrade` |
| `ValidateTest.test_upgrade_does_not_backfill_title_alone` | `upgrade` |
| `ValidateTest.test_upgrade_v1_to_v2_renames_store_cuts_title_and_commits` | `upgrade`, v1 stores |
| `StoreRoutingTest.test_notes_prune_dry_run_lists_exactly_the_matching_notes_and_writes_nothing` | `notes-prune` |
| `StoreRoutingTest.test_notes_prune_apply_removes_only_matching_notes_one_commit_per_store` | `notes-prune` |
| `StoreRoutingTest.test_notes_prune_apply_refuses_a_frozen_store_selected_by_flag` | `notes-prune` |
| `StoreRoutingTest.test_adopt_dry_run_on_a_frozen_store_still_works` | `adopt` |
| `StoreRoutingTest.test_upgrade_workspace_continues_past_a_frozen_repo_and_exits_nonzero` | `upgrade` |
| `ValidateTest.test_archive_year_filename_follows_spec_version` | v1 stores; it imported the old `ticket_core`, so it ran no CLI (overseer, 2026-11-13). `test_archive_on_v2_store_writes_tickets_year_file` covers the v2 name |

Helpers that only those tests used went with them: `_make_v1_store`,
`v1_config_path`, `write_v1_rows`, `_read_rows_raw`, `_git_init`,
`_git_commit_all`, `pm_config_path`, `pm_tickets_path`, `seed_cost_notes`,
`has_ref`.

Changed, so they still pass against the old CLI and no longer need a dropped verb:

| Test | Change |
| --- | --- |
| `ValidateTest.test_I02_v0_store_is_exactly_one_step` | no longer asserts the `upgrade` fix hint or `agent_may_fix` |
| `ValidateTest.test_I10_labels_not_sorted` | no longer asserts the `fix-labels` fix hint |
| `ValidateTest.test_mechanical_fixes_resolve_their_invariant` | fixture has no unsorted labels; `fix-labels` call removed |
| `AutoCommitTest.test_no_op_mutation_does_not_commit` | the no-op is `archive --closed-before 2000-01-01` instead of `fix-labels` |
| `HistoryCliTest.test_no_op_verb_adds_no_commit` | same substitution |
| `StoreRoutingTest.test_frozen_store_refuses_every_store_scoped_verb` | loop no longer includes `upgrade`, `adopt`, `fix-labels` |
| `StoreRoutingTest.test_live_store_mutations_are_unaffected_by_a_frozen_peer` | `fix-labels` call removed |
| `HelpTextTest.test_validate_help_names_version_and_exits` | no longer asserts `v1 or v2` |

Skipped with `@DEFERRED` until `history_interval_seconds` is built. Removing the
decorator is that ticket's first step:

- `HistoryCliTest.test_deferred_note_makes_no_commit_and_marks_once`
- `HistoryCliTest.test_validate_accepts_the_deferred_marker`
- `HistoryCliTest.test_enable_ignores_the_marker_and_disable_drops_the_line`
- `HistoryCliTest.test_restore_clears_the_deferred_marker`
- `HistoryCliTest.test_deferred_create_unclaimed_is_deferred`
- `HistoryCliTest.test_deferred_claim_release_close_reopen_snapshot_at_once`
- `HistoryCliTest.test_deferred_marker_past_the_interval_flushes_on_next_op`
- `HistoryCliTest.test_deferred_sync_flushes`
- `HistoryCliTest.test_deferred_summary_flushes_without_a_warning`

A worker never edits `test_cli_parity.py`. A test that looks wrong goes to the
overseer, and any change lands here with its reason.

## Old tests not carried over

These import the old modules, so they cannot run against new code. Each kept
behavior they cover is re-tested beside the module that now owns it.

| Old file | Tests | Disposition |
| --- | --- | --- |
| `ticket/tests/test_ticket_core.py` | 150 | read as the behavior reference for `tools/store.py` and `tools/routing.py`; its compaction and auto-archive cases are the reference for the deferred ticket |
| `ticket/tests/test_gitcommit.py`, `test_gitfault.py` | | ported with `tools/gitcommit.py` |
| `view/tests/test_board.py`, `test_overview.py` | | ported with the `board` and `overview` verbs, driving the CLI |
| `ticket/tests/test_session_hooks.py` | | reference for the hook work in the instruction-delivery epic |
| `intake/tests`, `telemetry/tests`, `ticket/spec/v2/tests` | | dropped with their features |

## New-contract tests

`tests/test_cli_contract.py`, written with the first rewrite ticket, holds what
the new CLI must do and the old one does not: each dropped verb exits 2, no
`validate` hint names a dropped verb, and no call writes a telemetry file.
