# 01b report: dispatcher, help, the unbuilt report

TICKET
fc-dac416 (worker 2 of 4). Branch fc-dac416.

DID
- `pm/cli/pm` (executable, `#!/usr/bin/python3`): finds its component by `os.path.realpath(__file__)`; one `VERBS` list of (verb, usage, summary) and the six aliases; `pm help` prints the table; `pm help <verb>` prints the verb file's docstring (read with `ast`, no import); unknown word prints the `no verb` line with `Closest:` from difflib over verbs and aliases, exit 2; bare `pm` runs `verbs/orient.py`; a verb with no file calls `store.unbuilt`; non-SystemExit exceptions become `pm: internal error: <Type>: <message>`, exit 1. Verb files load via `spec_from_file_location`, `sys.exit(module.run(argv))`.
- `pm/tools/store.py`: `unbuilt(name)` only.
- `pm/tools/render.py`: `refuse`, `usage_error`, `parser` (argparse error becomes `usage_error`; message lowercased first letter, trailing period).

EVIDENCE
- `/usr/bin/python3 -B pm/tests/run_transcripts.py -k 17-help -v`: `17-help.t: pending (take)`, passed 0, pending 1, failed 0.
- `/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending`: passed 0, pending 23, failed 0; unbuilt: hook, import, init, new, take.
- By hand in `.tmp/hand` (script `.tmp/hand.py`), no traceback:
  - `pm clam` -> `pm: no verb "clam". Closest: claim. All verbs: pm help` [2]
  - `pm xyzzy` -> `pm: no verb "xyzzy". All verbs: pm help` [2]
  - `pm help clam` -> same as `pm clam` [2]
  - `pm help` -> header, blank line, 22-row table as transcript 17 [0]
  - `pm help take` -> `pm: take is not built yet.` [70]; `pm help close` -> `pm: done is not built yet.` [70]; bare `pm` -> `pm: orient is not built yet.` [70]

COMMITS
`pm log core: dispatcher, help and the unbuilt report` (see `git log` on fc-dac416).

NOT DONE
- `pm help <alias>` resolves the alias to its verb, so the unbuilt line names the verb (`done`), not the alias.
- None else; `pm help` is 1464 bytes (design cap 1600).
- Plugin subcommands in the dispatcher (design "Source tree") are not built; not in this prompt.

BLOCKED ON OPERATOR
None.

ARTIFACTS
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/cli/pm
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/tools/store.py
- /Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/pm/tools/render.py
