# pm-wt-rewrite/04/02b pm read verbs fc-2a6562:fc-ef483a

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02b-reads.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/02b pm read verbs fc-2a6562:fc-ef483a

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02b-reads.md`

Ticket **fc-ef483a**, one of four step-2 workers running in parallel on separate
branches. The core (dispatcher, store, who, render, registry, `init new show stores`)
is merged. Read and obey `docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md`
first, especially "Module contract" and "Shared files in a parallel step".

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a`.

## Read first

`pm/docs/design.md` sections "Events", "Verbs" (the `ls` words, `ready`, `get`
fields rules) and "Output" (bare `pm`, `ls`, `--json`); transcripts `06-orient.t`,
`07-ls.t`, `14-get-emit-log.t`, `20-json.t`, and the `--all-stores` step of
`13-stores.t`; `pm/tools/store.py` and `render.py` as core left them.

## Deliver

1. `pm/tools/verbs/orient.py` (bare `pm`): `yours:`, `ready:`, `parked:`, each only
   when it has entries, five then `+N more: pm ls ready`; with nothing to show, one
   line that says how to file work. Plugin `orient` output is a later ticket: add
   nothing for it.
2. `pm/tools/verbs/ls.py`: the word grammar, order, the cap of 20, `-n`, `+N more: add -n 0`,
   `nothing matches.`, `--json`, and `--all-stores`, which the overseer moved to this
   ticket from fc-e2d8c9: read every store in `registry.read()` (with `store.find` on
   its path) and list their tickets together; with `--json` each object gains `store`.
3. `pm/tools/verbs/get.py`: the design's fields and the dotted `ns.key` form; an
   unknown field is a usage error as transcript 14 shows.
4. `pm/tools/verbs/log.py` (`pm log [id] [-n count]`, the stored lines verbatim) and
   `pm/tools/verbs/emit.py` (`pm emit id ns.name key=value ...`, through
   `store.change`).
5. `--json` for `show` and `ls`: one function in `render.py` placed after `show`; then
   replace `store.unbuilt("json")` in `pm/tools/verbs/show.py` with it.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 06-orient -k 07-ls -k 14-get-emit-log -k 20-json -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The second exits 0 with `failed 0`, and its `unbuilt verbs still needed` line names
none of `orient ls get log emit json`. For each of your four transcripts that is
still pending, name the verb it waits on (another ticket's) and confirm every step
before that call matches.

## Report

Commit message `pm read verbs: bare pm, ls, get, log, emit, --json`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-ef483a/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/02b-reads.md`.
