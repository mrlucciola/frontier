# OpenCode session observations

`tools/opencode_session.py` measures one explicitly authorized OpenCode turn, in
a session that does not exist yet (`fresh`) or in an existing session named by
its exact ID (`resume`). It is separate from `tools/fresh_codex.py`: the two
surfaces report different quantities under different names and their rows are
never pooled.

## Use

Python 3 standard library only, on a host with an authenticated `opencode` CLI
on PATH. Run from an ordinary terminal: agent sandboxes that deny writes to
OpenCode's log directory fail before any measurement. Create the disposable
fixture directory first and supply the prompt inline.

```sh
mkdir -p /private/tmp/authorized-fixture
python3 ~/projects/frontier-clean/session-telemetry/tools/opencode_session.py --phase fresh --cwd /private/tmp/authorized-fixture --session ses_telemetry_example 'Authorized fresh measurement. Work only inside this disposable fixture. Explain the Gregorian leap-year rule in at most 80 words and say whether 1900, 2000 and 2024 are leap years.'
```

Resume the same session by its exact ID from a new process, after whatever host
change the scenario calls for:

```sh
python3 ~/projects/frontier-clean/session-telemetry/tools/opencode_session.py --phase resume --cwd /private/tmp/authorized-fixture --session ses_telemetry_example 'Authorized resume measurement. Using only what this session already established, say whether 2100 is a leap year.'
```

`--session` is optional for `fresh`; the runner then generates `ses_<32 hex>`
and prints it as `session_id`. `--model provider/model#variant` and `--agent`
are passed to `opencode run`; omitted means the host default. `--timeout` bounds
the turn (default 180 seconds, at most 600).

The runner prints one JSON object and creates no prompt or report file. Exit 0
means `completed_with_usage`, **not** an accepted quality outcome: the evaluator
scores `agent_messages`, checks the fixture and records corrections separately.

## What a run does

1. Reads `opencode --version` and `opencode debug paths`, and hashes the output
   of `opencode debug config` without retaining it.
2. Asks `opencode api --standalone session.get` for the session. `fresh` stops
   with `session_already_exists` if it is found; `resume` stops with
   `session_not_found` if it is not. For `resume` it records the session's
   cumulative totals and the IDs of its existing messages.
3. Runs `opencode run --standalone --format json --session <id>` followed by
   the prompt, one argument per word, with stdin closed and `PWD` set to
   `--cwd`. It never passes `--auto` and never answers a permission request. On
   timeout it terminates the process group.
4. Reads the session and its messages back through `opencode api --standalone`
   and reduces only the messages that did not exist before step 3.

The prompt is split on single spaces because OpenCode wraps an argument that
contains a space in double quotes, which would put the quotes in front of the
model. A prompt with a doubled, leading or trailing space, or with a word that
starts with `-`, cannot be passed that way; the runner refuses it as
`unsupported_prompt` before running anything.

`--standalone` gives every step a private server, so a running background
service with older configuration cannot serve the turn. Configuration,
instructions, skills, permissions and credentials are inherited from the host;
the runner changes none of them.

## Fields

- `phase` is `fresh_session_turn` or `resumed_session_turn`. `surface` is
  `opencode_run_standalone`.
- `configuration` holds the CLI version, the resolved `config`, `data`, `db`,
  `state` and `cache` paths, a SHA-256 and byte count of the config-source
  listing, the session's agent, model and location, and `step_models`: the
  distinct model references the steps of this turn reported. Compare with
  `requested`; a requested value is never substituted for an observation.
  `location_is_cwd` says whether the session's reported directory is `--cwd`.
  When it is not, the turn loaded another directory's instructions and files:
  the row carries the `location_not_cwd` diagnostic and cannot be
  `completed_with_usage`. `session_info_keys` lists the field names the real
  Session.Info carried; on 2.0.32 `session_agent` and `session_model` were null
  in the smoke rows, so read the agent and model from `steps`.
- `steps` has one entry per assistant message created by this turn, with its
  model, `finish`, `tokens`, `cost_usd`, `time` and any error type or retry
  attempt. `assistant_steps` is their count. It is a count of assistant
  messages, not a verified count of provider calls.
- Token fields keep OpenCode's names: `input`, `output`, `reasoning`,
  `cache_read`, `cache_write`. The runner computes no total, no uncached input
  and no Codex-style field, and missing fields stay `null`. On the one provider
  observed so far (see Verification status) `cache_read` was larger than `input`
  and `reasoning` was larger than `output`, so there `input` excludes cached
  tokens and `reasoning` is not part of `output`. Whether that holds for other
  providers is not established.
- `step_usage_sum` adds the turn's steps field by field. `session_totals_before`
  and `session_totals_after` are the session's cumulative totals as reported,
  and `session_usage_delta` is their difference (for `fresh`, the totals
  themselves). The delta can exceed the step sum because OpenCode also records
  usage that belongs to no step, such as title generation. Report both; never
  add them.
- `step_span` gives the earliest step `created` and the latest step `completed`
  in the units OpenCode reports. `observer_run_elapsed_s` is the observer's own
  monotonic interval around the `opencode run` process, including server
  startup and shutdown. Neither is inference-only latency.
- `tool_items` keep the tool part ID, name, status, `executed` flag and times.
  Tool input, tool output and reasoning text are discarded. `skills` keep the
  skill ID and name of each skill message. `context_messages` keep the
  description, SHA-256 and byte length of each system or synthetic message, not
  its text. `agent_messages` keep assistant text for the task's rubric.
- `completion_evidence` says what showed the turn ended: `idle_message`,
  `session_outcome`, or `final_step_finish` (exit 0 and a last step that
  finished with `stop`).
- `run_stream` counts bytes, JSON lines, other lines and event types of the
  `opencode run` output, and lists the session IDs its events name. That
  stream's event schema is not published, so nothing else is read from it.
  stderr is counted and hashed, never printed.
- `user_message_texts` keeps the SHA-256 and byte length of each user message
  the turn added, beside `prompt_sha256` and `prompt_bytes`. `prompt_echoed` is
  true when one of them is exactly the prompt. When none is, the turn measured
  a different prompt: the row carries the `prompt_not_verbatim` diagnostic and
  cannot be `completed_with_usage`.

Outcomes other than `completed_with_usage` exit 1: `failed`, `interrupted`,
`incomplete`, `process_failed`, `timed_out`, `interactive_request_required`,
`completed_usage_unavailable`, `completed_usage_partial`, `completed_zero_usage`,
`invalid_telemetry`, `unsupported_prompt`, `session_already_exists`,
`session_not_found`, `session_not_created`, `api_error` and `launch_error`. A failed or timed-out
turn keeps whatever usage the session recorded; it is not free work.

## Not available on this surface

Recorded as unavailable, not as zero:

- The paths of the instruction files a session loaded. Only hashes of system
  and synthetic messages and of the config-source listing are kept.
- The permission rules and sandbox in effect.
- A verified provider call count, and reasoning effort apart from any model
  `variant`.
- Cache coldness. A fresh session is not evidence of an empty provider cache.

## State a run leaves behind

Each run persists its session in OpenCode's database (the `db` path in
`configuration`) and may write OpenCode logs. Nothing is installed and no
configuration is changed. To remove a measured session:

```sh
opencode session delete ses_telemetry_example
```

Dispose only of fixtures you created. To stop using the tool, stop invoking it.

## Verification status

Response shapes come from the published API description
(<https://opencode.ai/docs/openapi.json>, fetched 2026-11-12). Checked against
the installed OpenCode 2.0.32 without a model turn: the `run`, `api` and
`debug` flags used here, and that `opencode api --standalone session.get` for an
unknown session prints a `SessionNotFoundError` body and exits 1. Fixture tests
exercise the reducer against schema-shaped data and a fake CLI; they do not
prove the real route.

Operator-run fresh and resume rows (2026-11-12 and 2026-11-13, OpenCode 2.0.32,
provider `lai`, model `Qwen3.8-Flash-Next-oQ4e-fp16-mtp`, recorded on ticket
fc-3868ea) showed:

- `--session` creates a session under a caller-chosen `ses_...` ID, and a second
  process resumes it by that ID.
- Idle messages carry the outcome. Step times are epoch milliseconds;
  `firstToken` was absent. The session itself reported no agent or model, only
  the steps did. No system or synthetic messages were projected.
- A fresh session's totals exceeded its one step (by 637 input, 7 output and 375
  reasoning tokens in one row; by 5, 20 and 372 in another). A resumed turn's
  delta equalled its step both times.
- Before the runner set `PWD`, the session was located in the caller's
  directory. With `PWD` set to `--cwd`, a run launched from another directory
  reported the session in `--cwd`.
- With the prompt passed as one argument, the user message was the prompt
  wrapped in double quotes (the digests match exactly). Passing it one word per
  argument has passed fixture tests only; it has not been rerun against the
  client.

Not checked against the client: word-by-word prompt delivery, pagination, tool
and skill messages, failed and interrupted turns, and permission requests.
