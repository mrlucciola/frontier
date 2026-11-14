# pm maintenance

Standard-library Python at `/usr/bin/python3`. Write code to the
[component principles](/docs/component-principles.md): one file per verb under
`tools/verbs/`, shared code only in `tools/store.py`, `tools/routing.py` and
`tools/gitcommit.py`. A verb file exposes `register(subparsers)` and `run(args)`;
`tools/ticket` holds the kept-verb tuple and routes ids before `run`. Anything not
kept is cut: nothing under `tools/` calls `store.unbuilt` any more, and the
unbuilt-verb mechanism is gone. `tests/run_parity.py` still carries its pending
bookkeeping; with every verb built it reports none.

| Work | Read |
| --- | --- |
| Adding or changing a verb | [Cut list](/pm/docs/cut-list.md), then that verb's tests in `tests/test_cli_parity.py` |
| Anything that reads or writes `.pm/` | [Spec v2](/pm/docs/spec/v2/SPEC.md); the on-disk format does not change |
| The view renderers (`board`, `overview`) | `tests/test_views.py` |
| A parity test that looks wrong | Stop and report it. Do not edit `tests/test_cli_parity.py` |

Run from the repository root.

```sh
/usr/bin/python3 -B -m unittest discover -s pm/tests
```

That discovers `test_cli_contract.py` (refusal texts and exit codes per verb),
`test_gitcommit.py` (the store-commit helper), `test_views.py` (board and overview
output) and, slowly, `test_cli_parity.py`, the parity suite against the old CLI. Run
the parity suite through its runner, where `--cli` names the ticket CLI under test and `-k`
narrows to a class or test name. The full run takes minutes.

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k StoreRoutingTest
```

To confirm the suite itself, run it against the old CLI, which must stay green until
cutover:

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli /Users/matthias/frontier/runtime-tools/pm/ticket/src/ticket
```

The golden diff runs the old and new CLIs over the live registered stores and
compares output. It reads those stores read-only. Exit 0 means every comparison is
the same, 1 any difference, 2 any unruled skip. A skip on a store with a
`history-pending` deferred marker is ruled and does not fail.

```sh
/usr/bin/python3 -B pm/tests/golden_diff.py
```

After a docs change, run `python3 -B docs/check_structure.py`.
