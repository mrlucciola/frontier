# INITIATIVE: pm redesign (fc-2a6562)

## State

```text
fc-2a6562  P2  open          pm redesign: append-only event log, self-teaching CLI, plugins by file presence [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-dac416  P2  closed        pm log core: quarantine the port to pm/v2, dispatcher, store module, verbs init new show help
  fc-195118  P2  closed        pm lifecycle verbs: take drop done park reopen hold, the default id, --force, --dry-run, findings
  fc-ef483a  P2  closed        pm read verbs: bare pm, ls, get, log, emit, --json
  fc-8b871a  P2  closed        pm structure verbs: note edit link unlink, new's link flags, the duplicate guard
  fc-e2d8c9  P2  closed        pm stores: routing by prefix, links across stores, read-only stores, --all-stores, doctor
  fc-a731f4  P2  claimed       pm plugins: cmd, pre, post and orient files; the dispatch and pilot plugins [@agent:claude/claude#261b95c7]
  fc-3f4bfa  P2  closed        pm backup: one blob at refs/pm/log after every append, restore, the store of a linked worktree
  fc-4a8593  P2  claimed       pm import: fill a log from a spec v2 store, and check it against every registered store [@agent:claude/claude#261b95c7]
  fc-a761be  P2  claimed       pm harness hooks: pm hook for session start, prompt and stop; Claude and opencode wiring [@agent:claude/claude#261b95c7]
  fc-d6c61c  P2  open          pm redesign integration: budgets, concurrency, remove pm/v2, component docs, readability review
  fc-f3c2bd  P2  closed        pm redesign step-2 fixes: cross-ticket transcript failures after the step-2 merges
```

## Next batch

Step 2 closed 2026-11-14. On main, transcripts 01 to 14, 18, 20 and 21 pass without
`--allow-pending` (17 passed); `--allow-pending`: passed 18, pending 5, failed 0;
unbuilt: hook, import, plugins.

Step 3 closed 2026-11-14: fc-a761be, fc-4a8593, and fc-a731f4 after two review
rounds (`reports/03a-review*.md`). On main, all 24 transcripts pass without
`--allow-pending`; `import_check.py` matched all 10 registered stores.

In flight: fc-d6c61c, five serial workers `04-integration-a` to `-e`. Before `04c`, a
read-only reviewer lists every reference to `pm/v2` (written to
`reports/04-integration-c-review.md`); before `04e`, a read-only reviewer reads
`pm/cli`, `pm/tools`, `pm/plugins` against the principles
(`reports/04-integration-e-review.md`). After `04a`, the overseer updates the
runner's docstring (no unbuilt mechanism) as a gate change.

## Decisions

- **The module contract is fixed in `prompts/00-common.md`** (2026-11-14). Step-2
  workers code against it in parallel; a signature change comes back here.
- **Core writes `store.change()` and the default id**, not fc-195118 (2026-11-14):
  `new` already needs the one mutating path, and with it in core the step-2 tickets
  do not wait on fc-195118. fc-195118 keeps --force, --dry-run behavior, several ids,
  findings and the epic rules. The seed's "merge fc-195118 first" no longer applies.
- **The duplicate guard in core** (2026-11-14): `new.py` carries the copied
  `find_duplicates` from the start and calls `store.unbuilt("duplicate")` only on a
  match or `--new`, so transcript 11 stays pending and no other `new` is affected.
  fc-8b871a writes the refusal.
- **`ls --all-stores` moves to fc-ef483a** from fc-e2d8c9 (2026-11-14): `ls.py` is
  fc-ef483a's file, and listing every registered store needs only `registry.read()`
  from core, so the two run in parallel.
- **`store.is_done()` joins the contract** (2026-11-14): one readiness test that
  routing later extends, so fc-ef483a's `ls ready` and fc-e2d8c9's lookup meet in one
  function instead of a merge-order dependency.
- **Notes carry `kind`, not `tag`** (2026-11-14): transcript 20's `--json` pins the
  key; the contract was amended while worker 01c ran and it was told.

## Owed operator actions

None.

## Gate changes

One line per change to `pm/tests/t/`, `pm/tests/fixtures/` or
`pm/docs/design.md`: the file, what changed, why.

- `pm/docs/design.md` "Output", bare `pm`: the parked section's overflow line is
  `+N more: pm ls parked`, not `pm ls ready`, which pointed at the wrong list
  (raised by worker 02b; no transcript pins it).
- `pm/tests/t/24-plugin-edges.t` added (on branch fc-a731f4, commit 3f2422a): a dry
  run runs `pre` and not `post`; a silent `pre` refusal names the plugin; a plugin
  file that cannot run is a refusal, not a traceback; `emit` rejects a name with `/`.
  Why: the reviewer check of fc-a731f4 (`reports/03a-review.md`) found these
  untested.

## Unbuilt stubs and their owners

Every `store.unbuilt(<name>)` call left in built code, and the ticket that removes it.
fc-d6c61c checks this list is empty before it removes the mechanism.

| Stub | Where | Removed by |
| --- | --- | --- |
| `routing` | `store.ticket`, `store.is_done` | fc-e2d8c9 (removed) |
| `link`, `duplicate` | `verbs/new.py` | fc-8b871a (removed) |
| `json` | `verbs/show.py` | fc-ef483a (removed) |
| `backup` | `verbs/init.py`, inside a git checkout | fc-3f4bfa |
| `plugins` | `cli/pm` `no_verb`, when the plugins directory is not empty | fc-a731f4 |
| `plugins` | `verbs/orient.py`, when the plugins directory is not empty | fc-a731f4 |

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
  printed nothing on 2026-11-14, at the ledger's writing and again at the overseer's
  first turn.
- **The gate ran before any work:** `-k 01-init` ended
  `transcripts: passed 0, pending 0, failed 1` against the ported dispatcher.
- **`check_structure.py` on main** reports one violation that is not ours:
  `docs/contributing.md:149: X-STALE exemption cwf L-ROOT`, caused by another
  session's uncommitted cwf work. A worktree at HEAD may not show it.
- **Not ours.** `pm/dash-ui/` is untracked and belongs to another session.
