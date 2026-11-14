# pm design: an event log, a CLI that teaches itself, plugins by file presence

Status: ruled by the operator 2026-11-14; not built. This page is the specification
for the pm that replaces the ported one. The transcripts under `pm/tests/t/` are the
same specification in executable form and are the gate. Where the two disagree, the
overseer decides and fixes one of them; a worker changes neither.

## Why

The ported pm rewrites one row file on every change and commits it to git. Most of
its code exists to manage that: history states, a pending marker, batching,
compaction, archiving, nineteen invariants. An append-only log has none of those
problems, so none of that code is needed.

Three goals decide every choice below.

- **Fewer tool calls.** A call costs an agent more than its output. Verbs follow
  the agent's work, and each prints what the next step needs.
- **No standing instructions.** Guidance arrives in command output at the moment it
  applies. A session in a repo without `.pm/` pays nothing.
- **Nothing in pm names a plugin.** wt, deploy checks and dispatch rules attach
  through files that can be deleted.

## Store

A store is a directory `.pm/` holding two files.

| File | Tracked in git | Contents |
| --- | --- | --- |
| `config.json` | yes | `{"prefix":"t"}`, plus `"findings_required": true` when set. Other keys belong to plugins and are ignored. |
| `log.jsonl` | no | One event per line. Never rewritten, only appended to. |

The store for a command is the nearest ancestor of the working directory that has
`.pm/log.jsonl`. When none has it and the directory is in a git checkout, the main
checkout's root is tried, which is how a linked worktree finds its store. pm works
in a directory that is not a git repository.

### Events

An event is one line of compact JSON. Keys come in the order `ts`, `by`, `op`, `id`,
then the rest sorted by name.

```json
{"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"new","id":"t-1","title":"write the lexer"}
```

| `op` | Other keys | Effect |
| --- | --- | --- |
| `new` | `title`, and when given `body`, `kind` (`epic`), `pri`, `labels`, `under` | Creates the ticket, open |
| `edit` | any of `title`, `body`, `pri`, `under` (null clears), `label` (added), `unlabel` (removed) | Changes those fields |
| `take` | `from` when it replaced another holder | Status `taken`, holder is `by` |
| `hold` | `text` | Marks the ticket as deliberately kept across a pause |
| `drop` | `text` when given | Status `open`, no holder |
| `park` | `text` | Status `parked`, no holder |
| `done` | when given `text`, `findings`, `reason` | Status `done`, no holder |
| `reopen` | | Status `open` |
| `note` | `text`, `kind` when given | Adds a note |
| `link` | `rel` (`blocked-by`, `related`, `from`), `to` | Adds a link from this ticket |
| `unlink` | `to` | Removes this ticket's links to `to` |
| a name with a dot, such as `wt.park` | anything | None. It belongs to a plugin |

State is the result of replaying the log. A line that is not valid JSON, or names
an unknown ticket, is skipped. An `op` pm does not know is skipped. That last rule
is what lets a plugin store its own data in the log and lets an old pm read a newer
log.

A mutating verb takes an exclusive `flock` on the log, replays it, checks the
change, appends one or more lines with a single write, and releases. Readers take
no lock.

### Status

```text
open --take--> taken --done--> done --reopen--> open
                taken --park--> parked --take--> taken
                taken --drop--> open
open --done--> done            parked --reopen--> open
```

`hold` does not change status. Any status change clears it.

### Identity

`by` is `<actor>#<token>`, or `<actor>` alone when no session is known.

- **Actor:** `--as name` where a verb takes it, else `$PM_ACTOR`, else `claude` when
  `$CLAUDE_CODE_SESSION_ID` is set, else `codex` when `$CODEX_THREAD_ID` is set,
  else `$USER`.
- **Token:** the first eight hex digits of the SHA-256 of the session id, taken
  from `$PM_SESSION_ID`, then `$CLAUDE_CODE_SESSION_ID`, then `$CODEX_THREAD_ID`.

A ticket is "yours" when its holder's token equals yours, or, when neither side has
a token, when the actors are equal. `$PM_NOW`, when set, is the clock.

### Ids and the registry

A prefix is 1 to 8 lowercase letters or digits, starting with a letter. A new
ticket's id is `<prefix>-<n>`, where `n` is one more than the number of tickets in
the store, raised until it is unused. Imported tickets keep their old
ids. Inside its own store a ticket can be named by the number alone.

`~/.config/pm/stores`, or the file in `$PM_STORES`, maps prefixes to stores, one
`prefix path` per line, with ` ro` appended for a read-only store. `pm init` adds
its line. An id is routed by its prefix from any directory. A prefix may appear on
more than one line: a read uses the first listed store that has the ticket, and a
change goes to that store unless it is read-only.

A link to a ticket in another store is stored like any other. `blocked-by` lives on
the blocked ticket, in its store, so readiness needs only that store plus a lookup.
A blocker that cannot be found counts as not done.

### Backup

When the store is inside a git checkout, every append is followed by
`git hash-object -w .pm/log.jsonl` and `git update-ref refs/pm/log <sha>`. Because
the log only grows, the one blob is a complete backup: no commit, no tree, no
index, no signing. Superseded blobs are unreachable and git collects them. A
failure prints one warning line and never fails the verb. `pm restore` writes the
blob back when the log is missing or shorter. `pm init` adds `.pm/log.jsonl` to
`.gitignore`.

## Verbs

The first usage word is the verb. `[id]` left out means the one ticket this session
holds. These aliases work silently: `claim` for `take`, `release` for `drop`,
`close` for `done`, `create` for `new`, `list` for `ls`, `dep` for `link`.

| Usage | Does |
| --- | --- |
| `pm` | Orient: what you hold, what is ready, what is parked |
| `pm take [id ...] [--force] [--as name] [--dry-run]` | Take the top ready ticket, or the ones named, and print it |
| `pm note [id] "text" [-k decision\|finding\|measurement]` | Add a note |
| `pm done [id ...] [-m "text"] [--findings none\|id,...] [--reason wont-fix\|duplicate\|superseded\|abandoned] [--force] [--dry-run]` | Finish |
| `pm park [id] -m "text"` | Stop with work unfinished |
| `pm drop [id ...] [-m "text"] [--force] [--dry-run]` | Give back untouched |
| `pm hold [id] -m "text"` | Keep across a pause |
| `pm new "title" [-b body] [-p 0-4] [-l label] [--epic] [--under id] [--from id] [--blocks id] [--blocked-by id] [--take] [--as name] [--new]` | File a ticket and print its id |
| `pm edit id [--title text] [--body text] [-p 0-4] [-l label] [--unlabel label] [--under id\|none]` | Change fields |
| `pm link a blocks\|related b [c ...]` | Add links |
| `pm unlink a b` | Remove every link between two tickets |
| `pm reopen id` | Make a done or parked ticket open |
| `pm show [id] [--notes] [--json]` | One ticket |
| `pm ls [words ...] [-n count] [--json] [--all-stores]` | List tickets |
| `pm get id field [field ...]` | One value per line, for scripts |
| `pm log [id] [-n count]` | The stored event lines |
| `pm emit id ns.name [key=value ...]` | Append a plugin event |
| `pm init prefix` | Start a store here |
| `pm stores` | List the registry |
| `pm doctor` | Check this store |
| `pm restore` | Bring the log back from its git backup |
| `pm import` | Fill a new log from a spec v2 `tickets.jsonl` |
| `pm hook session-start\|prompt\|stop` | Print what a harness should inject |
| `pm help [verb]` | The verb list, or one verb's help |

Rules that hold across verbs:

- **Taking is idempotent.** Taking a ticket you hold prints it again and appends
  nothing. Taking a parked ticket resumes it.
- **`--force` is the operator's override.** It takes or drops a ticket someone else
  holds, takes a blocked ticket, and finishes an epic with unfinished children. A
  forced take records the previous holder in `from`.
- **Several ids are all or nothing.** Every id is checked before any line is
  appended.
- **`--dry-run` appends nothing.** It runs every check and every `pre` hook, then
  prints `ok: <id> can be <taken|dropped|done>` or the refusal.
- **Findings.** With `findings_required`, `done` needs `--findings`. `none` needs
  `-m` or an earlier note. Each id given must exist.
- **Duplicates.** `new` refuses when an open ticket, or one done within 30 days,
  shares enough rare words with the new title and body. The measure is
  `find_duplicates` from the ported `create.py`, unchanged. `--new` files anyway.
- **`ls` words.** Status words (`open taken parked done all`) select statuses and
  default to everything not done. `ready`, `mine` and `epics` narrow. `under:id`
  and `label:x` narrow. Any other word must appear in the title or body. Order is
  priority, then creation. The default cap is 20; `-n 0` removes it.
- **`ready`** means open, not an epic, and every blocker done.
- **`get` fields:** `status holder title pri kind under labels blocked-by blocks
  store body`. A name with a dot, `ns.key`, prints the latest value of `key` among
  this ticket's events whose `op` starts with `ns.`. An unset value prints an empty
  line.

## Output

Output is the instruction surface, so its shape is part of the contract.

**One line per ticket,** everywhere a ticket is listed:

```text
<id>  P<pri>  <status>  <title>[ [epic]][  @<actor>][  blocked by <id>, <id>]
```

`@<actor>` appears on a taken ticket. `blocked by` lists blockers that are not
done, on a ticket that is not done.

**`show` and `take`** print that line, then one line for each of these that
applies, in this order: `under: <id> <title>`, `blocks: <ids>` (tickets not done
that wait on this one, when this one is not done), `related: <ids>`, `from: <id>`,
`labels: <a, b>`, `hold: <text>`, `findings: <none or ids>`, `reason: <reason>`,
and for an epic `children: <counts by status>` followed by up to ten children that
are not done. Then a blank line and the body, when there is one. Then a blank line
and the notes.

A note line is `<date> <actor> [<tag>]: <text>`, indented two spaces, with later
lines of the text indented four. The tag is the note's kind, or `done`, `parked`,
`dropped` for the text given to those verbs, or `took over from <actor>` for a
forced take. A line with no text ends at the tag. An event with neither text nor
a takeover adds no line. The last five are shown under `notes:`; with more, the heading is
`notes (last 5 of 12; all: pm show <id> --notes):`.

**Bare `pm`** prints up to three sections, each only when it has entries:
`yours:`, `ready:` and `parked:`, entries indented two spaces. `ready` and `parked`
show five and then `+N more: pm ls ready` or `+N more: pm ls parked`. Plugin `orient` lines follow. With
nothing to show it prints one line that says how to file work.

**`ls`** prints one line per ticket. A capped list ends `+N more: add -n 0`. An
empty one prints `nothing matches.`

**Results** of a change are one line per ticket: `t-1 done`, `t-1 open`,
`t-1 noted`, `t-1 edited: title, pri`. `new` prints only the id. A line starting
`next:` follows when a specific next step exists.

**Refusals** go to stderr as `pm: <what is wrong>. <the command that helps>` and
exit 1. A usage error adds the verb's `usage:` line and exits 2. An unknown verb
names the closest one and exits 2. No path prints an argparse help dump or a
traceback.

**`--json`** prints one object per line with sorted keys and compact separators:
`blocked_by blocks body created findings from hold holder id kind labels notes pri
reason related status title under updated`, every key always present. Here
`blocked_by` and `blocks` list every link whatever its status. `--all-stores` adds
`store`.

### Size budgets

`pm/tests/test_budgets.py` holds these as byte ceilings, so cost is a test result.

| Output | Ceiling |
| --- | --- |
| `pm help` | 1600 |
| any `pm help <verb>` | 700 |
| any refusal | 300 |
| bare `pm` with 2 held, 8 ready, 3 parked | 700 |
| `pm hook session-start` for the same store | 760 |

## Plugins

A plugin is a directory under `~/.config/pm/plugins/`, or under `$PM_PLUGINS`,
usually a symlink into the component that owns it. pm looks for four kinds of
executable inside it. Installing is making the symlink. Removing is deleting it;
the plugin's events stay in the log and are ignored.

| File | When pm runs it | What its output means |
| --- | --- | --- |
| `cmd` | `pm <plugin name> args...` | It is the subcommand |
| `pre-<op>` | Before an event with that `op` is appended, outside the lock | Exit non-zero refuses the change; its output is the refusal |
| `post-<op>` | After the append | Its stdout is added after the verb's output |
| `orient` | On bare `pm` and the session-start hook | Its stdout is added after the sections |

Hooks receive `PM_OP`, `PM_ID`, `PM_STORE` (the repository root), `PM_BY`,
`PM_STATUS` (before the change), `PM_TEXT` and `PM_LABELS`, plus the caller's
environment. That is how a plugin lets its own calls through its own guard: wt sets
a variable before calling `pm done`, and its `pre-done` sees it. Plugins run in
name order.

Scripts read tickets with `pm get`, write plugin state with `pm emit`, and read it
back with `pm get <id> ns.key`. Those three, the hook files and the exit codes are
the whole contract.

Each hook point has a user today: `pre-done` for wt's "merge before finishing" and
frontier's deploy check, `post-take` for wt's worktree hint, `orient` for stale
worktrees and overdue pilots, `cmd` for `pm dispatch` and a dashboard.

## Harness hooks

`pm hook <event>` reads one JSON object on stdin with any of `cwd`, `session_id`,
`prompt`, `stop_hook_active`, and answers in plain text. These are Claude Code's
key names; another harness sends the same shape.

| Event | Prints | Exit |
| --- | --- | --- |
| `session-start` | Nothing outside a store. Inside: `pm tickets in this repo:`, the bare `pm` output, `All verbs: pm help` | 0 |
| `prompt` | For up to three ticket ids in the prompt that exist: `mentioned:` and one line each | 0 |
| `stop` | When this session holds a ticket with no `hold`, and `stop_hook_active` is not true: the tickets and the four exits, on stderr | 2 |

There is no skill and no global instruction text. A harness without hooks is
served by one line in the repository's `AGENTS.md`, which `pm init` prints.

## Import

`pm import`, run in a directory whose `.pm/` has a spec v2 `tickets.jsonl` and no
events, writes the log and registers the prefix. Old files are left in place.

| Old row | Events |
| --- | --- |
| every row | `new` at `created`, by `import`, with title, body, kind, priority, labels, parent |
| each note | `note` at its time, by `import`, kind kept; `edit-trail` notes are not imported |
| `blocks` edge to B | `link` on B, `blocked-by` this row |
| `blocked-by`, `related`, `discovered-from` edges | `link` on this row; a `<prefix>/<id>` target becomes the bare id |
| status `claimed` | `take` at `updated`, by the assignee as `<name>#<token>` |
| status `done-unmerged` | `park` at `updated` |
| status `closed` | `done` at `updated`, by `closed_by` when present, with `findings` and a `reason` other than `done` |
| `hold` | `hold` |
| an epic's `subtasks` entry, and each row of `archive/tickets-*.jsonl` | `new` then `done` |

## Source tree

```text
pm/
  cli/pm                 dispatcher: the verb table, aliases, plugin subcommands, help
  tools/store.py         find the store, read, replay, lock, append, back up
  tools/render.py        the one-line form, show, lists
  tools/who.py           actor, token, "yours"
  tools/registry.py      the registry and routing by prefix
  tools/plugins.py       run cmd, pre, post and orient files
  tools/verbs/<verb>.py  one file per verb; its docstring is `pm help <verb>`
  plugins/dispatch  plugins/pilot   two plugins a user may symlink in
  hooks/opencode/pm.ts   calls `pm hook`
  config/claude/hooks.json
  tests/run_transcripts.py   tests/t/*.t   tests/test_budgets.py
  docs/design.md
  README.md  AGENTS.md  CLAUDE.md  INSTALL.md
```

The dispatcher holds one table of verb, short usage and summary; `pm help` prints
it. Each verb file holds its own arguments, logic and full help. Bare `pm` runs
`tools/verbs/orient.py`.

## Not carried over

| Ported pm | Here |
| --- | --- |
| `ticket` and `view` families | Verbs directly under `pm` |
| `history`, the `pm-store` ref, a commit per change | The log, and one blob ref as backup |
| `archive`, compaction, auto-archive, interval batching | Not needed: nothing is rewritten |
| `validate`, `lint`, invariants I-01 to I-19 | `doctor`; a change that would break state is refused before it is written |
| `lint <id>` dispatch headings; the pilot contract in `lint` and `summary` | Plugins `dispatch` and `pilot`, shipped in `pm/plugins/` |
| `board`, `overview` | A separate component, reached as a plugin |
| `tree` | `show` lists direct links and an epic's children; the transitive view is dropped |
| `where`, `where --mutate` | `pm get <id> store`, and `--dry-run` |
| `claim --take-over`, `claim --reopen`, `close --via wt` | `take --force`, `take` on a parked ticket, and wt's own `pre-done` |
| `<prefix>/<id>` ids, `legacy_prefixes`, frozen stores | The id alone, and registry lines |
| typed lifecycle notes | The event's `op` is the type; `-k` keeps `decision`, `finding`, `measurement` |
| `bin/deploy close-check`, exit 4 | A `pre-done` plugin owned by frontier |
| the pm skill, global instruction sections | Command output and `pm hook` |

## Design record

```text
Relevant patterns:
  Explicit State Model     four statuses, one table of ops, state only by replay
  One Source of Truth      the log for data; the verb table for help; a verb's docstring for its help
  Test the Contract        transcripts pin command, output and exit code; nothing imports internals
  Abstraction After Evidence   every plugin hook point names a current user
Boundary map:
  pm owns tickets, the log, routing, its own output.
  A plugin owns its files, its events (names with a dot) and its config keys.
  The harness adapter owns only the mapping from its events to `pm hook`.
Design choice:
  append-only event log; verbs shaped by the agent's workflow; guidance in output;
  plugins found by file presence.
Rejected alternatives:
  Keep spec v2 and the ported code: carries the rewrite-and-commit machinery forever.
  One markdown file per ticket: agents would edit files directly, and a claim needs
  an atomic check that only one writer can give.
  Plugins found on PATH: any `pm-<name>` executable would run under pm's allow rule.
Implementation plan:
  the tickets of epic fc-2a6562, in docs/programs/pm-wt-rewrite/PLAN.md.
Validation:
  /usr/bin/python3 -B pm/tests/run_transcripts.py exits 0 with pending 0;
  pm/tests/test_budgets.py passes; pm/tests/import_check.py finds every ticket of
  every registered store after import with the same status and title.
Stop conditions:
  a transcript contradicts this page; a verb needs a second writer or a rewrite of
  the log; a plugin use case cannot be met by the four files; import would lose a
  ticket or a note other than edit-trail.
```
