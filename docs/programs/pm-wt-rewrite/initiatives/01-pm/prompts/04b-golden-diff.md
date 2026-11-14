# pm-wt-rewrite/01/04b pm integration: golden diff on the live stores fc-c3514f:fc-59011f

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04b-golden-diff.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/04b pm integration: golden diff on the live stores fc-c3514f:fc-59011f

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04b-golden-diff.md`

Ticket **fc-59011f** (pm integration), second serial worker on its branch. The first
removed the unbuilt mechanism and brought parity to `pending 0, failed 0` (report
`reports/04a-pending-zero.md` under `docs/programs/pm-wt-rewrite/initiatives/01-pm/`).
You prove the new CLI prints what the old one prints on real data. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` ("Where you work"
and "Rules").

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f`.

## Deliver

1. `pm/tests/golden_diff.py`, standard library, run as
   `/usr/bin/python3 -B pm/tests/golden_diff.py`. For every store in the registry at
   `/Users/matthias/frontier/runtime-tools/pm/stores.json`, run with the old CLI
   (`/Users/matthias/frontier/runtime-tools/pm/ticket/src/ticket`) and the new one
   (`pm/tools/ticket`), both with `PM_STORES_FILE` set to that registry and
   `PM_TELEMETRY_DIR=-`, each through `--store <repo>`: `summary`, `ready`, `list`,
   `stores --check`, and `show` on five ids taken from that store's `list --json`
   (fewer when it has fewer). Compare stdout and exit code; print one line per
   comparison (`same` or `DIFF` with the first differing line of each side); exit 1 on
   any `DIFF`.
2. Read-only is a hard rule: these are other people's live stores. Before running
   anything in a store, skip it, printing `SKIP <repo>: <reason>` and counting it, when
   its `.pm/history-pending` marker exists (`summary` would commit a snapshot) or its
   repo is not readable. Run nothing that mutates. A skip is never silent, and a run
   with any skip exits 2 unless every skip is for an unreadable repo outside the
   sandbox, which you list in NOT DONE with the exact path.
3. Fix every `DIFF` in `pm/tools/` (texts and order byte-identical to the old CLI), or,
   when the old output is non-deterministic (a timestamp, a temp path), make the
   comparison normalize exactly that field and say which in DID.

## Gate

```sh
/usr/bin/python3 -B pm/tests/golden_diff.py
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket
/usr/bin/python3 -B -m unittest discover -s pm/tests
```

`golden_diff.py` exits 0 and its summary line counts stores, comparisons, `same`,
`DIFF` and `SKIP`; paste it. The parity run still ends `pending 0, failed 0`.

## Report

Commit message `pm integration: golden diff on the live stores (fc-59011f)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04b-golden-diff.md`.
