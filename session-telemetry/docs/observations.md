# Fresh observation contract

Read this when interpreting observations or changing the reducer, transport,
output fields, or classification. [Usage](/session-telemetry/README.md) covers invocation and
[qualification](/session-telemetry/docs/qualification.md) records the evidence and its limits.

## Lifecycle and outcomes

The runner starts the installed `codex app-server` over stdio, initializes a client,
creates exactly one **ephemeral root thread**, and starts one turn. The model
and effort are invocation settings; sandbox, approval policy, instructions,
plugins and hooks are inherited from the host. The runner does not modify
configuration, log in, copy credentials, suppress hooks or use bypass flags.
An interactive server request (including an approval) ends the measurement as
`interactive_request_required`; it is never automatically approved. It sends
an interrupt only for its own new turn on timeout/failure. Default observation
limit is 180 seconds (`--timeout` may lower it). The server runs in its own
session; if it has not exited two seconds after its input closes, its whole
process group gets SIGTERM, then SIGKILL, two seconds apart, so cleanup can
add up to six seconds. Children the server moved to another process group are
outside this cleanup. A terminal turn allows up to five seconds to drain
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

## Usage, configuration and timing

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
