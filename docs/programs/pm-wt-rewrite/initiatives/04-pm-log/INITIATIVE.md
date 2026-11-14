# INITIATIVE: pm redesign (fc-2a6562)

## State

```text
fc-2a6562  P2  open          pm redesign: append-only event log, self-teaching CLI, plugins by file presence [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-dac416  P2  open          pm log core: quarantine the port to pm/v2, dispatcher, store module, verbs init new show help
  fc-195118  P2  open          pm lifecycle verbs: take drop done park reopen hold, the default id, --force, --dry-run, findings
  fc-ef483a  P2  open          pm read verbs: bare pm, ls, get, log, emit, --json
  fc-8b871a  P2  open          pm structure verbs: note edit link unlink, new's link flags, the duplicate guard
  fc-e2d8c9  P2  open          pm stores: routing by prefix, links across stores, read-only stores, --all-stores, doctor
  fc-a731f4  P2  open          pm plugins: cmd, pre, post and orient files; the dispatch and pilot plugins
  fc-3f4bfa  P2  open          pm backup: one blob at refs/pm/log after every append, restore, the store of a linked worktree
  fc-4a8593  P2  open          pm import: fill a log from a spec v2 store, and check it against every registered store
  fc-a761be  P2  open          pm harness hooks: pm hook for session start, prompt and stop; Claude and opencode wiring
  fc-d6c61c  P2  open          pm redesign integration: budgets, concurrency, remove pm/v2, component docs, readability review
```

## Next batch

fc-dac416, alone. Everything else is blocked behind it.

## Owed operator actions

None.

## Gate changes

None yet. One line per change to `pm/tests/t/`, `pm/tests/fixtures/` or
`pm/docs/design.md`: the file, what changed, why.

## Facts not to re-derive

- **The transcripts have never passed.** No implementation existed when they were
  written. Proven on 2026-11-14: the runner reports pass, fail, pending and
  fail-before-unbuilt correctly against a stand-in CLI; all 23 transcripts parse and
  run to their last step; `pm/tests/fixtures/v2` is a valid spec v2 store by the
  installed pm (`OK spec_version=2 rows=4 archive=absent`). Not proven: that the
  expected outputs are free of mistakes.
- **Two pms.** `pm` on `PATH` is the old frontier pm, used to run this epic. `pm/cli/pm`
  is the port until fc-dac416 moves it to `pm/v2/cli/pm`, and the new pm after that.
- **Module names.** The shared store module is `pm/tools/store.py` and the registry is
  `pm/tools/registry.py`. `pm/tools/verbs/log.py` is the `log` verb, not the store.
- **Transcript environment.** Each transcript runs in one `sh` in `$T/work` with
  `PM_ACTOR=ada`, `PM_SESSION_ID=s1` (token `e8bc163c`; `s2` is `ad328846`),
  `PM_NOW=2026-01-01T00:00:00Z`, `PM_STORES=$T/stores`, `PM_PLUGINS=$T/plugins`, a
  private `HOME`, and git identity and config isolated. `git init`, commits and linked
  worktrees work there inside the sandbox.
- **The help table's widths.** Each overview line is two spaces, the short usage padded
  to 22 columns, then the summary. The whole overview is 1464 bytes against a ceiling
  of 1600.
- **The duplicate measure is copied, not redesigned.** `find_duplicates` and
  `dup_tokens` are in `pm/tools/verbs/create.py` today and in `pm/v2/tools/verbs/create.py`
  after the move. Transcript 11 relies on its behavior for a title that repeats six
  rare words.
- **Session identity in hooks.** `pm hook` takes the session id from the JSON on stdin
  before the environment. Transcript 16 proves it with a session that holds nothing.
- **Claude hook behavior the design relies on, not verified here:** stdout of a
  SessionStart or UserPromptSubmit hook is added to context; a Stop hook that exits 2
  blocks and its stderr reaches the model; Stop's input carries `stop_hook_active`.
  fc-a761be confirms each against the documentation before relying on it.
- **Old sizes**, for the close note: the port is 25 verb files plus `store.py` 800,
  `routing.py` 435, `gitcommit.py` 293, `ticket` 135 lines. Count the whole of `pm/v2`
  at the commit before its removal.
- **Upstream.** `git -C ~/frontier log 90f8b81c..HEAD -- runtime-tools/pm runtime-tools/wt`
  printed nothing on 2026-11-14.
- **Not ours.** `pm/dash-ui/` is untracked and belongs to another session.
