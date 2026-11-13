# wt maintenance

zsh, with tests in standard-library Python that run the real executable. Write
code to the [component principles](/docs/component-principles.md): one file
per verb under `tools/verbs/`, shared helpers only in `tools/lib/`.

| Work | Read |
| --- | --- |
| Porting a verb | [Behavior contract](/wt/docs/contract.md), then that verb's cases in `tests/test_wt_cli.py` |
| A characterization test that looks wrong | Stop and report it. Do not edit `tests/test_wt_cli.py` after it is accepted |

wt never runs `git branch -D`, `git worktree remove --force` or `rm -rf`. A
port that needs one of them is wrong.

The test suite and its commands are added by the first ticket of the wt epic,
which writes `tests/test_wt_cli.py` and proves it green against the old wt.
