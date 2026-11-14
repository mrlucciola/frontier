# pm-wt-rewrite/04/02f pm step-2 fixes: transcripts 09 and 13 fc-2a6562:fc-f3c2bd

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02f-step2-fixes.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/02f pm step-2 fixes: transcripts 09 and 13 fc-2a6562:fc-f3c2bd

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02f-step2-fixes.md`

Ticket **fc-f3c2bd**. Four step-2 branches were written in parallel and merged; where
they meet, two transcripts fail. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first.
fc-3f4bfa (backup) runs in parallel on another branch and owns `pm/tools/store.py`'s
`find` and `change`, `verbs/init.py`, `verbs/doctor.py` and `verbs/restore.py`; do
not edit those. Your write set is the verb files below.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-f3c2bd`.

## Read first

`pm/docs/design.md` "Ids and the registry"; transcripts `09-link.t` and
`13-stores.t`; `pm/tools/store.py` (`ticket`, `locate`, `home`, `change`); the verb
files below.

## Deliver

1. `verbs/take.py`: a blocked take refuses
   `<id> is blocked by <ids>. Pick another: pm ls ready` (transcript 09 line 15).
2. Every mutating verb (`take drop done park reopen hold note edit link unlink emit`)
   passes `store.home(s, <target id>)` to `store.change`, so a ticket in another
   store is changed in its own store and a read-only store refuses. Inside `check`,
   look the ticket up in the `tickets` that `change` passes (that store's replay
   under its lock), not in a separate read. When several ids name tickets in
   different stores, refuse `<ids> are in different stores. Name them one store at a time.`
   `new --blocked-by` and `link` keep the link on the blocked ticket's side, as now.
3. `verbs/get.py`: `store` prints the root of the store that holds the ticket
   (transcript 13 line 25); a list field (`labels`, `blocked-by`, `blocks`) prints
   its values separated by single spaces.
4. Anything else transcript 09 or 13 needs, in verb files only. If a fix needs
   `store.py` beyond a new helper placed after `home`, stop and report it.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 09-link -k 13-stores -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The first exits 0 with `passed 2`. The second exits 0 with `failed 0`; paste its
full output.

## Report

Commit message `pm step-2 fixes: foreign ids change their own store`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-f3c2bd/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/02f-step2-fixes.md`.
