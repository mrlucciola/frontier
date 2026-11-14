# pm-wt-rewrite/04/01c pm log core: store, identity, registry, init and new fc-2a6562:fc-dac416

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-c-store.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/01c pm log core: store, identity, registry, init and new fc-2a6562:fc-dac416

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-c-store.md`

Ticket **fc-dac416**, third of four serial workers on its branch. The dispatcher,
`store.unbuilt` and the refusal helpers in `render.py` exist (reports `01-core-a-*`
and `01-core-b-*` in the worktree's `reports/`). You write the store module, identity,
the registry, and the verbs `init` and `new`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first,
especially "Module contract": every function it lists for `store.py`, `who.py` and
`registry.py` is yours to write now, with exactly that shape.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416`.

## Read first

`pm/docs/design.md` sections "Store" (all subsections except "Backup"), "Verbs" and
"Output"; transcripts `01-init.t`, `02-new-show.t`, `10-epic.t`, `11-duplicate.t`,
`12-default-id.t`. `find_duplicates` and `dup_tokens` in
`pm/v2/tools/verbs/create.py`.

## Deliver

1. `pm/tools/store.py`: `find`, `require`, `Store`, `now`, `read`, `replay`, `ticket`,
   `next_id`, `change`, per the contract. The store is the nearest ancestor of the
   working directory with `.pm/log.jsonl`; looking from a linked worktree into its
   main checkout is a later ticket. `replay` implements every `op` in the design's
   events table and the status diagram, skips bad lines, unknown tickets and unknown
   ops, and keeps plugin events in `events`.
2. `pm/tools/who.py` per the contract and the design's "Identity".
3. `pm/tools/registry.py`: `path`, `read`, `add`.
4. `pm/tools/verbs/init.py`: `pm init prefix`, with the output and the three refusals
   of transcript 01. It writes `.pm/config.json` as `{"prefix":"t"}` (compact),
   creates an empty `.pm/log.jsonl`, and adds its registry line. The `.gitignore`
   line is a later ticket; leave it out.
5. `pm/tools/verbs/new.py`: `pm new "title" [-b body] [-p 0-4] [-l label] [--epic]
   [--under id] [--take] [--as name]`, printing only the id; `--take` appends `new`
   and `take` in one `change`. `--under` refuses a ticket that is not an epic, as
   transcript 10 shows. `--from`, `--blocks` and `--blocked-by` call
   `store.unbuilt("link")`. The duplicate guard: copy `dup_tokens` and
   `find_duplicates` from the port into `new.py` unchanged, and when they find a
   match, or when `--new` is given, call `store.unbuilt("duplicate")`. The refusal
   text belongs to a later ticket.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 01-init -k 02-new-show -k 10-epic -k 11-duplicate -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending
```

`01-init.t` must be pending only on `stores`, `02-new-show.t` only on `show`,
`11-duplicate.t` only on `duplicate`; the second command exits 0 with `failed 0`.
Also write `<worktree>/.tmp/core_c_check.py`, which runs `pm init`, two `pm new` (one
with `--take --as w1` and a two-line `-b`) in a temporary directory under `.tmp/` with
`PM_STORES`, `PM_NOW`, `PM_ACTOR` and `PM_SESSION_ID` set, and prints the log; paste
the log under EVIDENCE and confirm the key order and `by` values by eye.

## Report

Commit message `pm log core: store, identity, registry, init and new`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/01-core-c-store.md`.
