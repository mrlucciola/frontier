# Session telemetry maintenance

This component owns the fresh Codex app-server observation runner and its fixtures.

| Change | Read |
| --- | --- |
| Use the runner or change its CLI | [Usage guide](README.md) |
| Usage fields, event reduction, outcomes, or timing | [Observation contract](docs/observations.md) before changing the runner or fixtures |
| Evaluate qualification or reuse measurements | [Qualification record](docs/qualification.md) and the referenced ticket evidence |

Run the component check from the repository root.

```sh
python3 -B -W error::ResourceWarning -m unittest discover -s session-telemetry/tests
```

Fixtures exercise local streams and subprocesses. Live model measurements need
an authorized test task and separate evidence from the fixture checks.
