# Tool usage

Use `~/.local/bin/cwf`, a link to `cwf.py` in the checkout. Requests are JSON files or stdin (`--input -`). Never interpolate task text into a shell command. Use a safely written request file and quote paths. `--home` is for explicit target homes, especially isolated tests; do not change HOME.

Example discovery request:

```json
{"scope":"/absolute/workspace","domain":"build","query":"widget value modification","files":["src/component.ts"]}
```

Run `cwf discover --input request.json`. Codes: 0 complete/intentional skip; 2 invalid; 3 blocked; 4 required check failed; 5 partial; 6 local/internal failure. Code 5 is useful evidence with incomplete coverage, not “nothing found.” Inspect `data.findings`, `data.coverage`, and `data.conflicts`. Lexical discovery does not determine semantic conflicts.

Use `inspect-source` with `scope`, `domain`, relative `path`, optional `line` and `lines`. Use `--ephemeral` for discovery without durable storage. Discovery refreshes on demand; there is no background watcher. Cached fingerprint matches are reported after re-reading/hashing sources, not assumed from timestamps.

For meaningful continuation, `checkpoint` takes `scope`, `expected_revision` (0 for create), and a `record` conforming to `schemas/task.schema.json`. `resume` takes `scope` and `id`; stale sources must be reconciled. Record a small next action and accessible evidence, not hidden reasoning or a transcript. Tools refuse silent lost updates.

`observe` stores a provenance-backed local observation. Accepted claims need attribution and acceptance source. Never record personal unrelated content or promote a hypothesis automatically.

`batch validate` takes `scope` and `batch` matching `schemas/batch.schema.json`. It checks declared dependencies/ownership only. It does not schedule agents or prove semantic independence. Worktree helpers use explicit scope/path/base and optional branch. Never force removal or discard uncommitted work.

`check` accepts `scope` and `checks`: either `absent_literal` with explicit paths/literal, or `command` with argv, timeout, expected_exit and an authorization reference. Commands execute only under existing user/runtime authority. A reference string is not proof of permission. Raw command output is not retained by CWF; use ordinary authorized tools if diagnostics are needed.

Setting `mode` off in the config changes future tool behavior but cannot retract context already loaded. Consult `cwf/docs/OPERATIONS.md` for deployment and state management, not during ordinary work.
