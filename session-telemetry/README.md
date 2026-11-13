# Session telemetry

`tools/fresh_codex.py` observes one authorized fresh Codex task through its newly
created thread stream. Measurements require an authenticated host that can launch
the installed CLI. Read the [qualification record](/session-telemetry/docs/qualification.md) for
provenance, component boundaries, and measured limits.

`tools/opencode_session.py` observes one authorized OpenCode turn in a fresh
session or a session resumed by exact ID. Its invocation, fields, unavailable
quantities and the session state a run leaves behind are in the
[OpenCode guide](/session-telemetry/docs/opencode.md). Its rows are never pooled with Codex rows.

## Read by task

| Work | Guide |
| --- | --- |
| Run an authorized fresh observation | Invocation and local setup below |
| Run an authorized OpenCode fresh or resumed observation | [OpenCode guide](/session-telemetry/docs/opencode.md) |
| Interpret output or change event semantics | [Observation contract](/session-telemetry/docs/observations.md) |
| Reuse measurement evidence | [Qualification record](/session-telemetry/docs/qualification.md) |
| Develop or validate the runner | [Maintenance instructions](/session-telemetry/AGENTS.md) |

## Run an observation

Run from an ordinary authenticated terminal with an explicitly authorized,
disposable fixture directory that already exists. Supply the prompt inline:

```sh
python3 ~/projects/frontier-clean/session-telemetry/tools/fresh_codex.py --cwd /private/tmp/authorized-fixture --model gpt-6.1-sol --effort high 'Authorized fresh measurement. Work only inside this disposable fixture. Do not read live memory or transcripts, change configuration, create tickets or start agents. Explain the Gregorian leap-year rule in at most 80 words and say whether 1900, 2000 and 2024 are leap years.'
```

Exit 0 reports `completed_with_usage`. Score the returned answer separately against
the task rubric. See the [observation contract](/session-telemetry/docs/observations.md#lifecycle-and-outcomes)
for failure outcomes and measurement limits.

## Local setup, validation and removal

Python 3 standard library only, on a host with the authenticated `codex` CLI
on PATH. Run directly from this checkout; no installer, hooks, service, SDK
or global configuration changes are required. Create the explicitly authorized
fixture before the measurement command above, for example:

```sh
mkdir -p /private/tmp/authorized-fixture
python3 ~/projects/frontier-clean/session-telemetry/tools/fresh_codex.py --help
```

The component gate is documented in [maintenance instructions](/session-telemetry/AGENTS.md).
Tests use schema-shaped streams and real local Python pipe subprocesses;
they never invoke Codex or read session logs. They cover failure/zero/missing
usage, scope filtering, duplicates, late events, interactive requests, invalid
protocol, timeout and process cleanup. No unrelated Frontier tests are imported.

To stop using the tool, stop invoking it; it installs no files outside this
component. Dispose of only the test fixtures you explicitly created. Normal
Codex behavior may still have its own host-side effects; ephemeral mode does
not promise that host hooks or all diagnostic logging are disabled.
