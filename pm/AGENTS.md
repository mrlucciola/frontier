# pm maintenance

Standard-library Python at `/usr/bin/python3`. Write code to the
[component principles](/docs/component-principles.md): one file per verb under
`tools/verbs/`, shared code only in `tools/store.py`, `tools/routing.py` and
`tools/gitcommit.py`.

| Work | Read |
| --- | --- |
| Adding or porting a verb | [Cut list](/pm/docs/cut-list.md), then that verb's tests in `tests/test_cli_parity.py` |
| Anything that reads or writes `.pm/` | [Spec v2](/pm/docs/spec/v2/SPEC.md); the on-disk format does not change |
| A parity test that looks wrong | Stop and report it. Do not edit `tests/test_cli_parity.py` |

Run from the repository root. `--cli` names the ticket CLI under test; `-k`
narrows to a class or test name.

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k StoreRoutingTest
```

The full suite takes about five minutes. To confirm the suite itself, run it
against the old CLI, which must stay green until cutover:

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli /Users/matthias/frontier/runtime-tools/pm/ticket/src/ticket
```
