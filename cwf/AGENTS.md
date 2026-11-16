# CWF maintenance

This component owns the standard-library CWF runtime, six skills, patterns,
schemas, and `deploy.sh` with the opencode instruction block it maintains. The
imported 0.1.0 candidate includes the macOS test-fixture repair from fc-14662f.
Historical qualification records describe their original runs; current evidence
belongs in pm notes.

| Work | Read |
| --- | --- |
| Deployment or removal | [Setup](/cwf/INSTALL.md), then relevant [operations](/cwf/docs/OPERATIONS.md) sections |
| Runtime behavior | Owning module in `cwf/`, its tests and relevant schema |
| Skill or pattern text | `scripts/author_content.py` generates `skills/` and `patterns/`: edit it, then run `python3 -B cwf/scripts/author_content.py` |
| Behavioral qualification | [Pilot protocol](/cwf/docs/PILOT.md) and fc-e902b6 acceptance cases |

Run the cwf checks from the repository root.

```sh
python3 -B cwf/tests/test_cwf.py
python3 -B cwf/tests/test_deploy.py
```

Do not add local plans, databases, logs or secrets to this directory.

The default tests use disposable homes and repositories; `test_deploy.py` runs
`deploy.sh` only against a temporary `HOME`. There is no installed-client probe for
opencode: discovery of the linked skills and the instruction sources a session
loads are checked by hand in a fresh session.

pm owns ticketed continuation; CWF checkpoint/observe/worktree commands do not
replace pm/wt. Keep source changes reviewable separately from activation.
