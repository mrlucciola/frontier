# pm-wt-rewrite/04/02a pm lifecycle verbs fc-2a6562:fc-195118

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02a-lifecycle.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/02a pm lifecycle verbs fc-2a6562:fc-195118

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02a-lifecycle.md`

Ticket **fc-195118**, one of four step-2 workers running in parallel on separate
branches. The core (dispatcher, store, who, render, registry, `init new show stores`)
is merged. Read and obey `docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md`
first, especially "Module contract" and "Shared files in a parallel step". Run
`pm ticket show fc-195118` (the old pm, read-only) for the ticket body and its note:
`store.change()` and the default id are already in core.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-195118`.

## Read first

`pm/docs/design.md` sections "Status", "Identity", "Verbs" (the rules list) and
"Output"; transcripts `03-take-drop.t`, `04-done-findings.t`, `05-park-reopen-hold.t`,
`10-epic.t`, `12-default-id.t`, `17-help.t` (`pm help take` pins take's docstring
byte for byte); `pm/tools/store.py`, `render.py`, `who.py` as core left them.

## Deliver

`pm/tools/verbs/take.py`, `drop.py`, `done.py`, `park.py`, `reopen.py`, `hold.py`:

- `take` with no id takes the top of ready (priority, then creation; open, not an
  epic, every blocker done by `store.is_done`); never a parked one. Taking what you
  hold prints it again and appends nothing. A parked ticket resumes. Output is
  `render.show`.
- `--force` takes or drops a ticket someone else holds, takes a blocked ticket, and
  finishes an epic with children not done; a forced take records `from` (the previous
  holder's `by`).
- Several ids are all or nothing: check every id before one `change` appends.
- `--dry-run` runs every check, appends nothing, prints `ok: <id> can be <taken|dropped|done>`.
- `done`: `-m`, `--findings none|id,...` (with `findings_required`; `none` needs `-m`
  or an earlier note; each id must exist; the `done` event stores `findings` as the
  string `"none"` or a list of ids, which `render.show` already prints), `--reason`,
  the epic rule, and the `next:`
  line when the last child of an epic is done (transcript 10).
- Refusal texts exactly as the transcripts print them.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 03-take-drop -k 04-done-findings -k 05-park-reopen-hold -k 10-epic -k 12-default-id -k 17-help -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The second exits 0 with `failed 0`, and its `unbuilt verbs still needed` line names
none of `take drop done park reopen hold`. For each of your six transcripts that is
still pending, name the verb it waits on (another ticket's) and confirm every step
before that call matches.

## Report

Commit message `pm lifecycle verbs: take drop done park reopen hold`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-195118/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/02a-lifecycle.md`.
