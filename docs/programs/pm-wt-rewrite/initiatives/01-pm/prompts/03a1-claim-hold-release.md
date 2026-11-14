# pm-wt-rewrite/01/03a1 pm verbs claim hold release fc-c3514f:fc-d73327

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03a1-claim-hold-release.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03a1 pm verbs claim hold release fc-c3514f:fc-d73327

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03a1-claim-hold-release.md`

Ticket **fc-d73327** (lifecycle verbs), first of two serial workers on its branch; the
second builds `close` and `reopen`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327`.
- Spec: `pm ticket show fc-d73327` (body and notes).

## Deliver

`pm/tools/verbs/claim.py`, `hold.py`, `release.py`: claim attribution
(`agent:<provider>/<name>#<token>` from `--as`, `--session`, `PM_AGENT`, `PM_SESSION_ID`,
`CLAUDE_CODE_SESSION_ID`), bulk ids all-or-nothing in one lock with repeated ids
deduped, refusal on a blocked ticket unless `--force`, the hold marker and its heartbeat
and staleness, release's `released_by` and its fix for a stray assignee, the four exit
lines claim prints, and each verb's typed note kind. Also from upstream `03b232d2`
(the ticket's newest note): `claim --reopen` (a done-unmerged ticket back in one call,
dropping `findings`, `findings_absent`, `closed_by`, readiness checked as if open;
`store.claim_veto(t, reopen=...)` already has the texts) and `hold`'s
`not claimed (status: ...); <status_hint>`. Their upstream tests import `ticket_core`,
so add CLI cases for them to `pm/tests/test_cli_contract.py`.

Old source by name: `ticket`: `each`, `CLAIM_EXITS`, `cmd_claim`, `_hold_marker`,
`cmd_hold`, `acting_identity`, `cmd_release`, and their `add_parser` blocks;
`ticket_core.py`: `session_token`, `hold_state_dir`, `touch_session_seen`,
`hold_is_stale`, `session_assignee`, `split_assignee`, `claim_is_mine`, and
`Store.is_ready`/`unsatisfied_cross` for the blocked check. `store.py` already has
`claim_veto`, `session_token`, `session_assignee`; reuse them.

## Gate

The common gate with `-k claim -k hold -k release -k test_bulk`. The full run's
`unbuilt verbs still needed:` line names none of `claim`, `hold`, `release`.

## Report

Commit message `pm lifecycle: claim, hold, release (fc-d73327)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-d73327/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03a1-claim-hold-release.md`.
