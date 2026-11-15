# CWF maintenance

This component owns the standard-library CWF runtime, six skills, patterns,
schemas, installer and opencode pilot configuration. The imported 0.1.0 candidate
includes the macOS test-fixture repair from fc-14662f. Historical qualification
records describe their original runs; current evidence belongs in pm notes.

| Work | Read |
| --- | --- |
| Installation, disabling, removal or pilot preparation | [Setup](/cwf/INSTALL.md), then relevant [operations](/cwf/docs/OPERATIONS.md) sections |
| Runtime behavior | Owning module in `cwf/`, its tests and relevant schema |
| Skill behavior | Selected `skills/cwf-*/SKILL.md` and its referenced patterns |
| Behavioral qualification | [Pilot protocol](/cwf/docs/PILOT.md) and fc-e902b6 acceptance cases |

Run from this component directory:

```sh
python3 -B -m unittest discover -s tests -p test_pilot.py -v
python3 -B -m unittest discover -s tests -v
```

Do not add local plans, receipts, databases, logs or secrets to this directory:
every regular file here is copied into the installed release.

The default tests use disposable homes and repositories. There is no
installed-client probe for opencode: discovery of the installed skill links and
the instruction sources a session loads are checked by hand in a fresh session.

For fc-2e70b4, C2 alone owns the [global entry](/cwf/config/global-entry.md) and any
skill permission rules in the opencode config directory. Always plan CWF with
`guidance:false`; its installer must not write global prose. pm owns ticketed
continuation; CWF checkpoint/observe/worktree commands do not replace pm/wt.
No live activation before the ticket's isolated qualification and explicit
operator ruling. Keep source changes reviewable separately from activation.
