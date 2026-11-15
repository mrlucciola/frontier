# pm maintenance

Standard-library Python at `/usr/bin/python3`. Build to
[the design](/pm/docs/design.md) and the
[component principles](/docs/component-principles.md).

The gate is the transcripts in `tests/t/`, plus the unit tests for size budgets and
concurrency.

Run from the repository root.

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py
/usr/bin/python3 -B -m unittest discover -s pm/tests
```

`pm/tests/import_check.py` compares `pm import` against the installed frontier pm over
every registered store. It reads `~/frontier/runtime-tools/pm/stores.json`, works on
copies under `.tmp/`, and is run when `verbs/import.py` changes.

```sh
/usr/bin/python3 -B pm/tests/import_check.py
```

| Work | Read |
| --- | --- |
| Any verb, event or output | [Design](/pm/docs/design.md), then the transcripts in `tests/t/` |
| A transcript or the design that looks wrong | Stop and report what looks wrong. Never edit the design, `tests/t/` or `tests/fixtures/` |
| Size budgets or locking | `tests/test_budgets.py`, `tests/test_concurrency.py`, the design's "Size budgets" |
| The harness hooks | `tools/verbs/hook.py`, `config/claude/hooks.json`, `hooks/opencode/pm.ts`, the design's "Harness hooks" |
| The shipped plugins in `plugins/` (`dispatch`, `pilot`) or `tools/plugins.py` | The design's "Plugins" section, transcripts 15, 22 and 23 |
| The bun/TypeScript web dashboard in `dash-ui/` | `dash-ui/AGENTS.md` — the python gates above do not apply inside it |

After a docs change, run `python3 -B docs/check_structure.py`.
