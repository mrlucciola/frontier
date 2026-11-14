# pm

Ticket store for agent work: an append-only event log per repository, in `.pm/`.

Each verb records a step of an agent's work (take, note, done, park, drop) and prints the
next thing to do. Plugins add subcommands and hooks by file presence; pm names none of
them. The design is [pm/docs/design.md](/pm/docs/design.md).

The installed `pm` stays the frontier one in `~/frontier/runtime-tools/pm` until the
operator's cutover. This pm runs as `pm/cli/pm`, a standard-library Python script;
[Setup](/pm/INSTALL.md) installs it beside the old one as `pm-next`.

## Entry point and verbs

`pm/cli/pm` dispatches to `pm/tools/verbs/<verb>.py`. Bare `pm` shows what you hold and
what is ready; `pm help <verb>` prints one verb in detail. `[id]` left out means the
ticket this session holds.

| Verb | Does |
| --- | --- |
| `take [id]` | Take the top ready ticket, or the one named, and print it |
| `note [id] "text"` | Add a note |
| `done [id] -m "text"` | Finish it |
| `park [id] -m "text"` | Stop with work unfinished and say what it waits on |
| `drop [id]` | Give it back untouched |
| `hold [id] -m "text"` | Keep it across a pause |
| `new "title"` | File a ticket and print its id |
| `edit id` | Change title, body, priority, labels or epic |
| `link a blocks b` | Order two tickets; or `link a related b` |
| `unlink a b` | Remove the links between two tickets |
| `reopen id` | Make a done or parked ticket open again |
| `show [id]` | One ticket with its links and notes |
| `ls [words]` | List: `ready mine open taken parked done all epics under:id label:x`, or text |
| `get id field` | Print one field per line, for scripts |
| `log [id]` | Print the raw events |
| `emit id ns.name k=v` | Record a plugin event |
| `init prefix` | Start a store in this directory |
| `stores` | List every store on this machine |
| `doctor` | Check this store |
| `restore` | Bring back a lost log from its git backup |
| `import` | Fill a new log from a spec v2 `.pm/tickets.jsonl`; the format is in git history: `git show 7e17357:pm/v2/docs/spec/v2/SPEC.md` |
| `hook event` | Print what an agent harness should inject |

## Registry

`~/.config/pm/stores`, or the file named by `$PM_STORES`, maps prefixes to stores, one
`prefix path` per line, with ` ro` appended for a read-only store. `pm init` adds its
line and `pm stores` lists them. An id is routed by its prefix from any directory.

## Plugins

A plugin is a directory under `~/.config/pm/plugins/`, or under `$PM_PLUGINS`, usually
a symlink into the component that owns it. pm runs executables found by name inside it:
`cmd` (the subcommand `pm <plugin>`), `pre-<op>`, `post-<op>` and `orient`. Two ship in
`pm/plugins/`:

| Plugin | Gives |
| --- | --- |
| `dispatch` | `pm dispatch id`: checks that a ticket body has the four headings a worker needs |
| `pilot` | `pm pilot`: lists open tickets labelled `pilot` whose `review_by:` line is missing or past; adds overdue pilots to `orient` and a `pre-done` guard |

## Harness hooks

`pm hook session-start|prompt|stop` reads one JSON object on stdin and answers in plain
text. Registrations for Claude Code are `pm/config/claude/hooks.json`; opencode uses
`pm/hooks/opencode/pm.ts`. Setup is in [pm/INSTALL.md](/pm/INSTALL.md#harness-hooks).

## Routes

| Document | Read when |
| --- | --- |
| [Design](/pm/docs/design.md) | Building or judging any verb, event or output |
| `pm/tests/t/` and `pm/tests/run_transcripts.py` | Checking a build against the transcripts that gate it |
| [Maintenance](/pm/AGENTS.md) | Changing code or tests here |
| [Setup](/pm/INSTALL.md) | Installing, verifying, disabling or removing |
