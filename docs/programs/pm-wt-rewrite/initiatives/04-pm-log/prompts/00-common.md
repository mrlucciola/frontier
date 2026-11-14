# pm-wt-rewrite/04 common worker rules fc-2a6562

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md`

Every worker prompt of this initiative names this file. Read all of it before your
first edit; it binds you as if it were in your prompt.

## Where you work

- Your prompt names a worktree, `/Users/matthias/projects/frontier-clean/.worktrees/<ticket-id>`.
  The overseer created it with `wt start`. Edit only paths under it, from your first edit.
- Every git command is `git -C <worktree> ...`; every other path is absolute. No `cd`.
- `git add` explicit paths only. Commit on the ticket branch, run your gate, and stop.
  Never run `wt`, never merge, rebase, stash, remove the worktree or delete the branch.
- Never run `pm ticket close`, `note` or `claim`. Discoveries go in NOT DONE; the
  overseer files them.
- Scratch files go in `<worktree>/.tmp/`. Never `rm` them.
- Binding brief: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`
  (budget: stop at 80k tokens or 40 tool calls, commit what is green, report the rest
  in NOT DONE).

## Two pms

- `pm` on `PATH` is the old frontier pm. You do not need it; do not run it.
- The pm being built is `pm/cli/pm` in your worktree. Run it only through the gate, or
  as `/usr/bin/python3 <worktree>/pm/cli/pm ...` inside a directory under
  `<worktree>/.tmp/`, with `PM_STORES` pointing at a file in that directory. Never run
  it against this repository's own `.pm/`, and never against `~/.config/pm`.

## Rules

- Never edit `pm/tests/t/`, `pm/tests/fixtures/`, `pm/tests/run_transcripts.py` or
  `pm/docs/design.md`. A transcript that contradicts the design, another transcript or
  itself: stop, and put the file, line, expected and got text, and which side you
  think is right in NOT DONE. The overseer fixes the gate and re-dispatches.
- Code standard: `docs/component-principles.md`. Standard-library Python at
  `/usr/bin/python3` (3.9.6: no `match`, no `X | Y` types). No comment that restates
  code; no ticket ids in source.
- The pending rule: a verb with no file under `pm/tools/verbs/` is reported unbuilt by
  the dispatcher; a built verb that reaches a part a later ticket owns calls
  `store.unbuilt(<name>)`. `--allow-pending` must stay at `failed 0` after your commit.
- Shared modules under `pm/tools/` take additive edits only. Changing the signature or
  meaning of a function in the contract below goes back to the overseer; replacing a
  `store.unbuilt(...)` call with the real behavior is not a change of meaning.
- No argparse help dump and no traceback reaches the user, on any path.
- Each verb file's docstring is its `pm help <verb>` text: first line
  `usage: <the verb's full usage from the design's verb table>`, a blank line, then
  a few sentences. Under 700 bytes.
- Run from the worktree root: `/usr/bin/python3 -B pm/tests/run_transcripts.py ...`.

## Module contract

The overseer fixed this so later workers can write verbs in parallel. A function
listed here keeps its name, arguments and meaning. Add what your ticket needs.

**Verb file** `pm/tools/verbs/<verb>.py`: module docstring as above, and
`run(argv) -> int` where `argv` is the words after the verb. The dispatcher puts
`pm/tools/` on `sys.path`, so a verb imports `store`, `who`, `render`, `registry`
directly.

**`pm/cli/pm`**: the verb table (verb, short usage, summary) exactly as transcript 17
prints it, the six aliases, `pm help`, `pm help <verb>` (prints the verb file's
docstring; a verb with no file is unbuilt), the closest-verb refusal, bare `pm` runs
`verbs/orient.py`. A missing verb file calls `store.unbuilt(verb)`. Any exception
other than `SystemExit` becomes one line on stderr, `pm: internal error: <Type>: <message>`,
exit 1.

**`pm/tools/render.py`** owns everything the user reads:
- `refuse(text)`: stderr `pm: <text>`, exit 1. The caller writes the full sentence(s)
  after `pm: `, including the trailing period and the helping command.
- `usage_error(doc, text)`: stderr `pm: <text>` then the first line of `doc`, exit 2.
- `parser(doc)`: an `argparse.ArgumentParser` with `add_help=False` whose `error()`
  calls `usage_error(doc, <argparse's message>.)`. Verbs parse with it.
- `line(t, tickets)`: the one-line form of the design's "Output" section.
- `show(t, tickets, all_notes=False)`: the `show` text, without a trailing newline.

**`pm/tools/who.py`**:
- `actor(as_name=None)`, `token()` (None when no session id), `by(as_name=None)`
  (`actor#token` or `actor`), `actor_of(by)`, `yours(holder_by)`.

**`pm/tools/store.py`**:
- `unbuilt(name)`: appends `name` and a newline to `$PM_UNBUILT_LOG` when set,
  stderr `pm: <name> is not built yet.`, exit 70.
- `find(start=None)`: the `.pm` directory of the store for `start` (default cwd), or
  None. `require()`: the same, or refuses `no store here. Start one: pm init <prefix>`.
  Both return a `Store` with `root` (the directory holding `.pm`), `dir`, `log`,
  `config` (the parsed `config.json`) and `prefix`.
- `now()`: `$PM_NOW`, else UTC now as `YYYY-MM-DDTHH:MM:SSZ`.
- `read(s)`: the log's events as dicts; a line that is not JSON is skipped.
- `replay(events)`: `{id: ticket}` in creation order. A ticket is a dict with every
  `--json` key of the design (`blocked_by blocks body created findings from hold
  holder id kind labels notes pri reason related status title under updated`) plus
  `events`, the raw events of that ticket including plugin ops. `holder` is the `by`
  of the take; `notes` is a list of `{"ts", "by", "kind", "text"}` built per the
  design's note-line rule, where `kind` is the note's `-k` kind, or `done`, `parked`,
  `dropped` for the text given to those verbs, or `took over from <actor>` for a
  forced take, and null for a plain note (render prints it as the tag); `blocks` is
  computed from other tickets' `blocked-by` links. Defaults: `kind` `task`, `pri` 2,
  `body` `""`, lists empty, the rest null. `created` is the `new` event's `ts`,
  `updated` the `ts` of the ticket's latest event. Transcript 20 pins the shape.
- `ticket(s, tickets, word)`: resolves `word` to a ticket dict. `None` means the one
  ticket this session holds (refusals as transcript 12). A bare number is
  `<prefix>-<n>`. An id whose prefix is not this store's calls `unbuilt("routing")`.
  Unknown: refuses `no ticket <id>. Search: pm ls all <words>`.
- `next_id(s, tickets)`: one more than the ticket count, raised until unused.
- `is_done(tid, tickets)`: True when that ticket's status is `done`. A `tid` not in
  `tickets` whose prefix is another store's calls `unbuilt("routing")` until the
  stores ticket replaces it with a registry lookup; a blocker that cannot be found is
  not done. Every readiness test and every `blocked by` or `blocks:` line uses it.
- `change(s, check, actor=None, dry_run=False)`: the one path every mutating verb
  appends through. `check(tickets)` is a pure function: it refuses (via `render`) or
  returns a list of event dicts holding `op`, `id` and the rest. `change` takes an
  exclusive `flock` on the log, replays, calls `check`, fills `ts` (`now()`) and `by`
  (`who.by(actor)`), orders keys `ts by op id` then the rest sorted, and appends every
  line in one write. With `dry_run` it calls `check` and appends nothing. Returns the
  list of events (written, or that would be written). `check` must have no side
  effects: plugins will later call it twice.

**`pm/tools/registry.py`**: `path()` (`$PM_STORES`, else `~/.config/pm/stores`),
`read()` (a list of `(prefix, path, ro)`; a missing file is an empty list),
`add(prefix, path)`. Routing by prefix is a later ticket.

## Shared files in a parallel step

Several branches of one step edit `pm/tools/store.py`, `pm/tools/render.py` and
`pm/tools/registry.py`, and the overseer rebases them one after another. To keep
rebases clean: a helper that only your verbs use lives in your verb file
(component principle 2), not in a shared module; a new shared function goes
directly after the contract function it belongs with, never at the end of the file;
do not reformat, reorder or rename anything you did not write.

## Report

Write the report to the path your prompt names, in exactly the worker-brief shape
(`TICKET`, `DID`, `EVIDENCE`, `COMMITS`, `NOT DONE`, `BLOCKED ON OPERATOR`,
`ARTIFACTS`), commit it on the branch with your last commit, and print only its path.
