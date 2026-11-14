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
```

The first line is the gate: exit 0 with `pending 0, failed 0`. The `--pm old` run
points at the old wt and the old pm. `-k` keeps tests whose id contains the name.
`--allow-pending` accepts verbs that answer exit 70 (not built). The last line runs the
plugin transcripts.

| Work | Read |
| --- | --- |
| A verb | [Contract](/wt/docs/contract.md), then that verb's cases in `tests/test_wt_cli.py` |
| The plugin in `pm-plugin/` | `tests/t/`, and pm's design section "Plugins" |
| A characterization test that looks wrong | Stop and report it. `tests/test_wt_cli.py` is accepted; edit it only on an explicit ruling |

wt never runs `git branch -D`, `git worktree remove --force` or `rm -rf`. A
port that needs one of them is wrong. The one exception is `selftest`, which
runs `rm -r` on its own scratch directory.

After a docs change, run `python3 -B docs/check_structure.py`.
