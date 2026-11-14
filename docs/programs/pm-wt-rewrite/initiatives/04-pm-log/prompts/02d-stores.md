# pm-wt-rewrite/04/02d pm stores, routing and doctor fc-2a6562:fc-e2d8c9

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02d-stores.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/02d pm stores, routing and doctor fc-2a6562:fc-e2d8c9

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02d-stores.md`

Ticket **fc-e2d8c9**, one of four step-2 workers running in parallel on separate
branches. The core (dispatcher, store, who, render, registry, `init new show stores`)
is merged. Read and obey `docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md`
first, especially "Module contract" and "Shared files in a parallel step".
`ls --all-stores` moved to fc-ef483a; it is not yours.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-e2d8c9`.

## Read first

`pm/docs/design.md` sections "Ids and the registry", "Verbs" and "Output";
transcripts `13-stores.t` and `21-doctor.t`; `pm/tools/registry.py`, `store.py` and
`render.py` as core left them.

## Deliver

1. Routing in `pm/tools/registry.py`: an id is routed by its prefix from any
   directory, including one with no store; a prefix listed more than once reads from
   the first listed store that has the ticket; an unknown prefix refuses
   `no store has prefix <p>. Known: <prefixes>`. Use it to replace
   `store.unbuilt("routing")` in `store.ticket` and `store.is_done`, without changing
   their signatures. A verb that changes a ticket in another store appends to that
   store, through `store.change` on that store.
2. Read-only stores: a change to a store whose registry line ends ` ro` refuses
   `store <prefix> is read-only (<path>).` before anything is appended; reads work.
   Put the check where every mutating path passes it (`store.change`).
3. `blocks:` in `render.show` also lists tickets in other registered stores that are
   `blocked-by` this one and not done.
4. `pm/tools/verbs/doctor.py`: `ok: <prefix>, <n> ticket(s), <n> event(s)`, or one line
   per problem and exit 1, as transcript 21 shows. Report a line that is not an event,
   an event for an unknown ticket, and a link to a ticket that cannot be found. A
   `backup:` line is a later ticket's.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 13-stores -k 21-doctor -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The second exits 0 with `failed 0`, and its `unbuilt verbs still needed` line names
none of `routing doctor`. For each of your two transcripts that is still pending,
name the verb it waits on (another ticket's) and confirm every step before that call
matches.

## Report

Commit message `pm stores: routing by prefix, read-only stores, doctor`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-e2d8c9/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/02d-stores.md`.
