# CWF maintenance

This component owns the standard-library CWF runtime, six skills, patterns,
schemas, and `deploy.sh` with the opencode instruction block it maintains.
Historical qualification records describe their original runs.

| Work | Read |
| --- | --- |
| Scope, a new mechanism, or whether to keep one | [Product requirements](/cwf/docs/PRD.md) first; it wins over the specification |
| Deployment or removal | [Setup](/cwf/INSTALL.md), then relevant [operations](/cwf/docs/OPERATIONS.md) sections |
| Runtime behavior | Owning module in `cwf/`, its tests and relevant schema |
| Skill or pattern text | `scripts/author_content.py` generates `skills/` and `patterns/`: edit it, then run `python3 -B cwf/scripts/author_content.py` |
| Behavioral qualification | [Pilot protocol](/cwf/docs/PILOT.md) and the acceptance cases in [specification](/cwf/docs/SPECIFICATION.md) section 14 |

Run the cwf checks from the repository root.

```sh
python3 -B cwf/tests/test_cwf.py
python3 -B cwf/tests/test_deploy.py
python3 -B cwf/tests/test_budgets.py
```

`test_budgets.py` holds the skill catalog and the instruction block to byte
ceilings, because both cost tokens on every step. A change that grows either
raises the ceiling in the same commit and records the measured bytes.

Do not add local plans, databases, logs or secrets to this directory.

The default tests use disposable homes and repositories; `test_deploy.py` runs
`deploy.sh` only against a temporary `HOME`. There is no installed-client probe for
opencode: discovery of the linked skills and the instruction sources a session
loads are checked by hand in a fresh session.

Checkpoint, observe and worktree commands are for work no ticket tracks. Where
the repository tracks work, its ticket notes and worktree tool own continuation
and checkouts. Keep source changes reviewable separately from activation.
