# Session telemetry maintenance

This component owns the fresh Codex app-server observation runner, the OpenCode
fresh/resume session runner, and their fixtures.

| Change | Read |
| --- | --- |
| Use the runner or change its CLI | [Usage guide](/session-telemetry/README.md) |
| Usage fields, event reduction, outcomes, or timing | [Observation contract](/session-telemetry/docs/observations.md) before changing the runner or fixtures |
| OpenCode runner (`tools/opencode_session.py`), its fields or fake CLI (`tests/fake_opencode.py`) | [OpenCode guide](/session-telemetry/docs/opencode.md) before changing the runner or fixtures |
| Evaluate qualification or reuse measurements | [Qualification record](/session-telemetry/docs/qualification.md) and the referenced ticket evidence |

Run the component check from the repository root.

```sh
python3 -B -W error::ResourceWarning -m unittest discover -s session-telemetry/tests
```

Fixtures exercise local streams and subprocesses. Live model measurements need
an authorized test task and separate evidence from the fixture checks.
