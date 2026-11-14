# pm-wt-rewrite/01/03d pm verb history fc-c3514f:fc-c5e673

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03d-history.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03d pm verb history fc-c3514f:fc-c5e673

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03d-history.md`

Ticket **fc-c5e673** (history), one worker. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-c5e673`.
- Spec: `pm ticket show fc-c5e673` (body and notes, including the unported
  `legacy=True` commit path and the `.pm/history-pending` gitignore handling).

## Deliver

1. `pm/tools/verbs/history.py`: `status` (legacy, migrating, on, behind, missing),
   `enable` and `disable` as normal commits on the default branch with nothing staged
   and the exact refusals (non-empty index, staged gitignore that differs, pre-staged
   ticket file, off the default branch), crash-resume of `enable`, the
   `.pm/history-pending` gitignore line, `sync`, `restore` refusing a newer differing
   working file. The deferred state and `history_interval_seconds` are not built; their
   tests stay skipped.
2. `pm/tools/gitcommit.py`: this ticket alone may change existing code there, still
   without changing an existing signature (new keyword arguments with defaults are
   fine): add the legacy default-branch flush `enable` needs.
3. `pm/tests/test_cli_contract.py`: cover the `.pm/history-pending` gitignore and marker
   handling with a fault marker the test writes (the three parity tests for it are
   `@DEFERRED`).

Old source by name: `ticket`: `HISTORY_REF`, `_history_blobs`, `_history_behind`,
`_HistCtx`, `_flocked`, `_hist_raise`, `_hg`, `_hist_staged`, `_hist_precheck`,
`_hist_gitignore`, `_hist_missing_msg`, `_hist_state`, `_hist_require_key`,
`_history_status`, `_history_sync`, `_history_restore`, `_history_enable`,
`_history_disable`, `HISTORY_VERBS`, `cmd_history`, its `add_parser` block;
`ticket_core.py`: `mark_history_pending`, `clear_history_pending`, `history_pending`,
`commit_store`'s `legacy` branch. This is the largest single worker in step 3: if the
budget runs out, land `status`, `sync`, `restore` first and report `enable`/`disable`
in NOT DONE.

## Gate

The common gate with `-k HistoryCliTest -k AutoCommitTest -k WorktreeStoreTest`. The
full run's `unbuilt verbs still needed:` line does not name `history`.

## Report

Commit message `pm history: status, enable, disable, sync, restore (fc-c5e673)`. Report
path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-c5e673/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03d-history.md`.
