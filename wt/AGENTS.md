# wt maintenance

zsh, with tests in standard-library Python that run the real executable. Write
code to the [component principles](/docs/component-principles.md): one file
per verb under `tools/verbs/`, shared helpers only in `tools/lib/`.

Run from the repository root.

```sh
/usr/bin/python3 -B wt/tests/run_wt.py --cli wt/cli/wt --pm new
/usr/bin/python3 -B wt/tests/run_wt.py --cli <old wt> --pm old
/usr/bin/python3 -B wt/tests/run_wt.py --cli wt/cli/wt --pm new -k StartTest
/usr/bin/python3 -B pm/tests/run_transcripts.py --dir wt/tests/t
/usr/bin/python3 -B -m unittest discover -s wt/tests -p 'test_budgets.py'
```

The first line is the gate: exit 0 with `pending 0, failed 0`. The `--pm old` run
points at the old wt and the old pm. `-k` keeps tests whose id contains the name.
`--allow-pending` accepts verbs that answer exit 70 (not built). The last line runs the
plugin transcripts.

| Work | Read |
| --- | --- |
| A verb | [Contract](/wt/docs/contract.md), then that verb's cases in `tests/test_wt_cli.py` |
| Help text, byte ceilings, or what an agent is told | [Instruction map](/wt/docs/instruction-map.md), then `tests/test_budgets.py` |
| The plugin in `pm-plugin/` | `tests/t/`, and pm's design section "Plugins" |
| A characterization test that looks wrong | Stop and report it. `tests/test_wt_cli.py` is accepted; edit it only on an explicit ruling |

wt never runs `git branch -D`, `git worktree remove --force` or `rm -rf`. A
port that needs one of them is wrong. The one exception is `selftest`, which
runs `rm -r` on its own scratch directory. wt does print `rm -rf` and
`git worktree remove --force` in its failure lines as commands for the operator; it
hands them over, quoted, and never runs them.

Recorded exceptions to "shared helpers need three callers":

- `wt_findings_required` is shared by finish and park.
- `wt_stop_remove_failed`, `wt_deferred_line`, `wt_refuse_undeletable` and
  `wt_merged_route` are shared by finish and park: finish auto-parks through park, so
  they are one teardown family.

`--session` overrides the environment in every verb except park's pm calls, where a suite
test needs the environment to win (see the comment in `tools/verbs/park.zsh`).

After a docs change, run `python3 -B docs/check_structure.py`.
