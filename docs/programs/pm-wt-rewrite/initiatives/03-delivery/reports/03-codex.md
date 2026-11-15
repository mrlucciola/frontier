TICKET: fc-2c0656 -- Codex: record what lifecycle hooks exist and wire pm guidance to what is supported
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/pm/INSTALL.md: new "Codex" subsection under "Harness hooks" (proven table, not-yet-proven list, Probe, Register, Verify, Disable, Remove) and an intro line naming Codex.
DID: pm/config/codex/hooks.json: Codex registration fragment calling `pm hook session-start|prompt|stop`, no adapter (payload keys match).
DID: pm/tests/codex/probe.py and pm/tests/codex/hooks.json: recorder script and its registration for the scratch-home probe.
EVIDENCE:
- `/Users/matthias/.codex/packages/standalone/current/bin/codex --version` -> `codex-cli 0.167.0` (the `~/.local/bin/codex` symlink is blocked in the sandbox; the target needed `dangerouslyDisableSandbox`, read-only commands only: --version, --help, features list, debug --help, and reading the binary's strings with a .tmp script).
- `codex features list` -> `hooks                                    stable             true`.
- The binary embeds JSON Schemas titled `session-start.command.input`, `user-prompt-submit.command.input`, `stop.command.input` (also session-end, pre/post-tool-use, permission-request, pre/post-compact, subagent-start/stop, interrupt). Inputs: SessionStart {cwd, hook_event_name, model, permission_mode, session_id, source(startup|resume|clear|compact|fork), transcript_path}; UserPromptSubmit adds {prompt, turn_id}; Stop {cwd, hook_event_name, last_assistant_message, model, permission_mode, session_id, stop_hook_active, transcript_path, turn_id}. These are exactly the keys `pm hook` reads (cwd, session_id, prompt, stop_hook_active), same names as Claude's; extras are ignored by pm/tools/verbs/hook.py.
- Outputs: SessionStart/UserPromptSubmit accept `hookSpecificOutput.additionalContext`; Stop accepts `decision:"block"` + `reason`. Binary strings: `Stop hook exited with code 2 but did not write a continuation prompt to stderr` (exit 2 + stderr is the continuation path, matching `pm hook stop`).
- Plain stdout on UserPromptSubmit reaches the model: /Users/matthias/frontier/hooks/graph-memory/docs/trust-model.md Stage C3 ("injection confirmed in a real Codex session") and codex_recall.py ("Codex appends hook stdout to context as-is").
- /Users/matthias/.codex/hooks.json (read only) is the file format example; /Users/matthias/.codex/config.toml `[hooks.state."<file>:<event>:<group>:<handler>"] trusted_hash` shows the trust model; `codex --help` lists `--dangerously-bypass-hook-trust`.
- Probe run by hand: `printf '{"cwd":"/x","hook_event_name":"SessionStart","session_id":"s1","source":"startup","transcript_path":null,"model":"m","permission_mode":"default"}' | /usr/bin/python3 -B pm/tests/codex/probe.py <worktree>/.tmp/probe-capture.jsonl SessionStart` -> no output, exit 0; captured line: `{"event": "SessionStart", "argv": ["/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/.tmp/probe-capture.jsonl", "SessionStart"], "stdin": "{\"cwd\":\"/x\",\"hook_event_name\":\"SessionStart\",\"session_id\":\"s1\",\"source\":\"startup\",\"transcript_path\":null,\"model\":\"m\",\"permission_mode\":\"default\"}"}`
- Gate (run by absolute path from the worktree; the bare relative form from the Bash default cwd hit the main checkout, which I noticed and reran): `/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/pm/tests/run_transcripts.py` -> `transcripts: passed 25, failed 0`; `/usr/bin/python3 -B -m unittest discover -s /Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/pm/tests` -> `Ran 7 tests ... OK`; `/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/docs/check_structure.py` -> `check_structure: ok (7 components, 3 exempted)`.
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656 e52e909 (branch fc-2c0656; the report commit follows it on the same branch). check-required: no.
NOT DONE:
- No Codex session was run (not allowed), so these are not proven live: (a) SessionStart plain-text stdout reaches the model (the schema's own form is JSON `additionalContext`; if plain text is ignored, `pm hook session-start` needs a Codex adapter emitting `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":...}}`, not written here); (b) the three events fire under `codex exec`; (c) `Stop` exit 2 continuation behaves live (proven only by the binary's message); (d) whether a scratch `CODEX_HOME` keeps the login (I did not check where Codex stores it).
- No official Codex documentation was found on disk; the event list rests on strings embedded in the 0.167.0 binary. Other events exist (SessionEnd, PreToolUse etc.) and are not wired.
- The AGENTS.md fallback is documented but applies only if the probe or Verify disproves SessionStart; all three events exist per the schemas.
- The gate's bare `pm/tests/...` paths ran against the main checkout from the default cwd; absolute-path reruns in the worktree are what is quoted above.
BLOCKED ON OPERATOR:
1. Trigger: the pm verbs are merged to the main checkout (the probe and fragment name `~/projects/frontier-clean/pm/...`). Create the scratch Codex home with the recorder registration.
   ```sh
   mkdir -p /Users/matthias/projects/frontier-clean/.tmp/codex-probe/home
   cp /Users/matthias/projects/frontier-clean/pm/tests/codex/hooks.json /Users/matthias/projects/frontier-clean/.tmp/codex-probe/home/hooks.json
   ```
2. Sign in to the scratch home (login carry-over unknown).
   ```sh
   CODEX_HOME=/Users/matthias/projects/frontier-clean/.tmp/codex-probe/home /Users/matthias/.local/bin/codex login
   ```
3. Run one short session.
   ```sh
   CODEX_HOME=/Users/matthias/projects/frontier-clean/.tmp/codex-probe/home /Users/matthias/.local/bin/codex exec --dangerously-bypass-hook-trust -C /Users/matthias/projects/frontier-clean "Reply with the single word ok."
   ```
4. Read the capture; expect one line each for SessionStart, UserPromptSubmit and Stop, and send it to the overseer. If fewer than three, rerun interactively as pm/INSTALL.md "Probe" step 3 says.
   ```sh
   cat /Users/matthias/projects/frontier-clean/.tmp/codex-probe/capture.jsonl
   ```
5. After the capture matches, register per pm/INSTALL.md "Codex" > "Register" (edit /Users/matthias/.codex/hooks.json lines 17-22, accept the trust prompt, then the Verify section proves the SessionStart claim). Tell me when done - the rest is mine.
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/pm/INSTALL.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/pm/config/codex/hooks.json
/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/pm/tests/codex/probe.py
/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/pm/tests/codex/hooks.json
/Users/matthias/projects/frontier-clean/.worktrees/fc-2c0656/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/03-codex.md
