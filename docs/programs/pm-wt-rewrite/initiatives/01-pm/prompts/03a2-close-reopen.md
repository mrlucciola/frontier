# pm-wt-rewrite/01/03a2 pm verbs close reopen fc-c3514f:fc-d73327

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03a2-close-reopen.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03a2 pm verbs close reopen fc-c3514f:fc-d73327

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03a2-close-reopen.md`

Ticket **fc-d73327** (lifecycle verbs), second of two serial workers on its branch. The
first built `claim`, `hold`, `release`; its report is `reports/03a1-claim-hold-release.md`
under `docs/programs/pm-wt-rewrite/initiatives/01-pm/` in the worktree. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327`.
- Spec: `pm ticket show fc-d73327` (body and notes).

## Deliver

`pm/tools/verbs/close.py` and `reopen.py`: bulk all-or-nothing, `closed_by`,
`--unmerged` (kind `park`), `--note`/`--reason` (kind `worker-return`), `--findings`
with `findings_required` (phase 1 warns, phase 2 refuses), findings ids across stores
through `routing.py`, an epic with open children (`--force`, `--detach` with kind
`edit-trail`), the tooling-label `bin/deploy close-check` contract (exit 4) and
`--no-deploy-check` (kind `finding`), `--session`; reopen clearing `closed_by`,
`findings`, holds and `closure_reason` as the old one does.

Old source by name: `ticket`: `refuse_if_unclaimed`, `refuse_if_closed`,
`close_open_children`, `NO_FINDINGS_TEXT`, `parse_findings`, `_cmd_close_locked`,
`EXIT_DEPLOY_PENDING`, `DEPLOY_CHECK_LABEL`, `_ticket_paths`, `deploy_check`,
`cmd_close`, `cmd_reopen`, their `add_parser` blocks. The `where --mutate` verb
(already merged) uses the same close-time rules: `rg -n` for them in `store.py` and
`routing.py` and reuse them rather than writing a second copy.

## Gate

The common gate with `-k close -k reopen -k findings -k phase -k deploy -k test_lifecycle_verbs_write_their_kind`.
The full run's `unbuilt verbs still needed:` line names none of `claim`, `hold`,
`release`, `close`, `reopen`.

## Report

Commit message `pm lifecycle: close, reopen (fc-d73327)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03a2-close-reopen.md`.
