# CWF maintenance

This component owns the standard-library CWF runtime, six skills, patterns,
schemas, installer and Codex pilot configuration. The imported 0.1.0 candidate
includes the macOS test-fixture repair from fc-14662f. Historical qualification
records describe their original runs; current evidence belongs in pm notes.

| Work | Read |
| --- | --- |
| Installation, disabling, removal or pilot preparation | [Setup](INSTALL.md), then relevant [operations](docs/OPERATIONS.md) sections |
| Runtime behavior | Owning module in `cwf/`, its tests and relevant schema |
| Skill behavior | Selected `skills/cwf-*/SKILL.md` and its referenced patterns |
| Behavioral qualification | [Pilot protocol](docs/PILOT.md) and fc-e902b6 acceptance cases |

Run from this component directory:

```sh
python3 -B -m unittest discover -s tests -p test_pilot.py -v
python3 -B -m unittest discover -s tests -v
```

After intentional component changes, regenerate integrity metadata with
`python3 -B scripts/package.py`, then run checks against that exact bundle.
Do not add local plans, receipts, databases, logs or secrets to this directory:
all regular files become part of the release manifest.

The default tests use disposable homes and repositories. The opt-in
`python3 -B tests/qualify_codex.py` probe starts fresh installed-client threads
without model turns. Run it from an ordinary operator terminal when a nested
sandbox cannot start the client's filesystem helper. It neither installs into
the live home nor reads/copies credentials.

For fc-2e70b4, C2 alone owns the temporary global override. Always plan CWF with
`guidance:false`; its installer must not write global prose. pm owns ticketed
continuation; CWF checkpoint/observe/worktree commands do not replace pm/wt.
No live activation before the ticket's isolated qualification and explicit
operator ruling. Keep source changes reviewable separately from activation.
