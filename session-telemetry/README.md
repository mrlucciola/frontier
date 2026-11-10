# Session telemetry

`tools/fresh_codex.py` is a one-turn observation runner for authorized fresh Codex tasks. It
reads only its newly created thread stream. Historical readers, session-cost
ledger schemas and compare remain in Frontier under fr-87c29f; this component
has no import or runtime dependency on that repository. Measurements require an authenticated host that
can actually launch the installed CLI; synthetic fixture passes do not prove
that route. See fr-55af2f notes for the current real-run qualification status.

Run from an ordinary authenticated terminal with an explicitly authorized,
disposable fixture directory that already exists. Supply the prompt inline:

```sh
python3 ~/projects/frontier-clean/session-telemetry/tools/fresh_codex.py --cwd /private/tmp/authorized-fixture --model gpt-6.1-sol --effort high 'Authorized fresh measurement. Work only inside this disposable fixture. Do not read live memory or transcripts, change configuration, create tickets or start agents. Explain the Gregorian leap-year rule in at most 80 words and say whether 1900, 2000 and 2024 are leap years.'
```

This starts the installed `codex app-server` over stdio, initializes a client,
creates exactly one **ephemeral root thread**, and starts one turn. The model
and effort are invocation settings; sandbox, approval policy, instructions,
plugins and hooks are inherited from the host. The runner does not modify
configuration, log in, copy credentials, suppress hooks or use bypass flags.
An interactive server request (including an approval) ends the measurement as
`interactive_request_required`; it is never automatically approved. It sends
an interrupt only for its own new turn on timeout/failure. Default observation
limit is 180 seconds (`--timeout` may lower it); bounded process cleanup can
add up to four seconds. A terminal turn allows up to five seconds to drain
shutdown output, including late usage. An abnormal exit or truncated stream
cannot qualify as a successful measurement.

The runner emits one JSON object on stdout and creates no prompt or report
file. Exit 0 means `completed_with_usage`, **not** an accepted quality outcome.
The evaluator must score `agent_messages`, check fixture behavior and record
corrections/interventions independently. Other outcomes exit 1, including
`failed`, `interrupted`, unavailable/partial/all-zero usage, protocol errors,
timeouts and process failures. Failed runs retain any observed usage. Missing
fields stay `null`, including cache-write even if the protocol gives it a
default. Do not treat a failed/zero-usage run as free accepted work.

Observation semantics (installed 0.167.0 schema, not a durable ledger contract):

- `configuration` records the returned thread/start model, provider, effort,
  service tier, policy, instruction paths and CLI version. Compare it with
  `requested`; never substitute requested values for unavailable observations.
  The configured model is not per-call execution telemetry. `executed_model`
  is null; `model_reroutes` preserves any explicit reroute notifications.
- `usage_snapshot.total` is the latest cumulative thread total; `last` is the
  latest reported response breakdown. These are provider fields, never added
  together. Intermediate/duplicate snapshots are not extra calls or usage.
  Fields retain Codex names: `inputTokens`, `cachedInputTokens`,
  `cacheWriteInputTokens`, `outputTokens`, `reasoningOutputTokens`, `totalTokens`.
  Reasoning output is a subset of output, not an added charge. No pricing or
  uncached-input conversion is attempted. Invalid/regressing totals cannot
  qualify. The single fresh turn makes its thread total scoped to that run;
  do not reuse this reducer for historical or resumed threads.
- `model_calls` remains null: token updates lack a response identity and cannot
  establish a call count. `retry_notice_receipts` counts received `willRetry`
  notices, including possible retransmissions without event IDs, not model
  calls or a proven count of network attempts.
- `server_turn` retains `startedAt`, `completedAt` and `durationMs` when
  provided. Duration is the server's turn duration, including work/tools; it
  is not inference-only latency. `observer_process_elapsed_s` and
  `observer_turn_request_to_exit_s` are separate monotonic observer intervals,
  including startup/transport/shutdown. They are not task/server latency and
  cannot repair missing server duration or prove deadlines during suspension.
- `tool_items` are deduped by item ID and retain type/status/duration only.
  Commands, tool arguments/results and reasoning text are discarded. Final
  agent messages are retained for the authorized task's rubric. stderr is
  counted/hashed without printing its contents. Conflicting completions,
  malformed usage or protocol failures cannot yield a qualifying result.

Keep this surface (`codex_app_server_stdio`, fresh ephemeral root turn) separate
from connected child agents, normal `codex exec`, Claude CLI, native persisted
restart, warm continuation and fresh checkpoint recovery. No injection parity
or cache coldness is assumed. The runner supports neither resume nor fork and
does not fill missing metrics from another surface. Reuse A2 quality evidence
only with its recorded surface and configuration limits.

Protocol references: [Codex app server](https://learn.chatgpt.com/docs/app-server)
and [exec JSON stream](https://learn.chatgpt.com/docs/non-interactive-mode).
The installed CLI can generate its own version-matched schema with
`codex app-server generate-json-schema --out <disposable-directory>`.

## Use, validation and removal

Python 3 standard library only, on a host with the authenticated `codex` CLI
on PATH. Run directly from this checkout; no installer, hooks, service, SDK
or global configuration changes are required. Create the explicitly authorized
fixture before the measurement command above, for example:

```sh
mkdir -p /private/tmp/authorized-fixture
python3 ~/projects/frontier-clean/session-telemetry/tools/fresh_codex.py --help
```

Component gate, from the repository root:

```sh
python3 -W error::ResourceWarning -m unittest discover -s session-telemetry/tests
```

These tests use schema-shaped streams and real local Python pipe subprocesses;
they never invoke Codex or read session logs. They cover failure/zero/missing
usage, scope filtering, duplicates, late events, interactive requests, invalid
protocol, timeout and process cleanup. No unrelated Frontier tests are imported.

To stop using the tool, stop invoking it; it installs no files outside this
component. Dispose of only the test fixtures you explicitly created. Normal
Codex behavior may still have its own host-side effects; ephemeral mode does
not promise that host hooks or all diagnostic logging are disabled.

## Adoption provenance and qualification

Adopted from Frontier fr-55af2f commit
`7206911c0a9eaea4a0e4315769338d0f8eefd2fd`, limited to the fresh runner and its
tests/docs. The existing non-negative integer helper is local to the runner;
no historical session-cost module was copied. Existing consumers need no
migration; output retains the prototype's observation semantics. This is not
a versioned durable ledger API.

Ticket fr-55af2f notes preserve an operator-run successful host Q sample using
the prototype with CLI 0.167.0: configured gpt-6.1-sol/high/openai, raw input
24995, cached input 0, cache write 0, output 120 (including reasoning 38), total
25115, server turn duration 5151 ms. The answer passed the recorded leap-year
rubric. The returned source was `vscode` despite stdio transport. These are
provenance for that recorded surface/configuration, not a new destination run
or a representative baseline. Calls, executed model and USD were unavailable.

A2 remains fc-92ecfa under fc-63bffb. Its existing connected-child quality
cohort cannot be pooled with this root-stdio sample. Resume/native restart
and Claude measurements are outside this component. Follow the A2 ticket's
cohort and configuration requirements before collecting further samples;
fixture tests alone do not establish real model cost or quality.
