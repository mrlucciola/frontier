TICKET: fc-a731f4

DID:
- pm/tools/plugins.py: lists plugin dirs under $PM_PLUGINS or ~/.config/pm/plugins in name order, finds executables, builds the hook environment, runs cmd and hooks. The only place plugin files run.
- pm/cli/pm: `pm <name> args` runs `<name>/cmd` (exit code passed through, PM_STORE set when a store is found); `pm help` ends with `plugins: <names>`; the `unbuilt("plugins")` is gone. A verb name wins over a plugin of the same name.
- pm/tools/store.py `change`: check runs on an unlocked replay, `pre-<op>` runs for each event outside the lock (non-zero: plugin output on stderr, exit 1, nothing appended), then lock, replay, check again, append, release the lock, then `post-<op>` runs. Post stdout is queued and written by an atexit hook, so it follows the verb's own output with no per-verb code. dry_run runs pre and skips post. Post runs after the lock is released so a post hook may call pm. check is unchanged and stays pure.
- pm/tools/verbs/orient.py: appends each plugin's `orient` stdout after the sections; unbuilt call removed.
- pm/plugins/dispatch/cmd (sh), pm/plugins/pilot/{cmd,orient,pre-done,pilot.py} (/usr/bin/python3; they read tickets only through `pm get` / `pm ls --json`).
- pm/AGENTS.md routes row for pm/plugins/.

EVIDENCE:
- run_transcripts -k 15-plugins -k 17-help -k 22-plugin-dispatch -k 23-plugin-pilot -v: `passed 4, pending 0, failed 0`, exit 0.
- run_transcripts --allow-pending -v: `passed 21, pending 2, failed 0`; `unbuilt verbs still needed: hook, import` (no plugins).
- python3 -B docs/check_structure.py: `check_structure: ok (7 components, 4 exempted)`.

COMMITS: one commit, `pm plugins: cmd, pre, post and orient; dispatch and pilot` (SHA from: git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-a731f4 rev-parse --short HEAD).

NOT DONE:
- hook's session-start should call plugins.orient_text() for plugin orient lines (design says orient runs on the session-start hook); the hook ticket owns it.
- Plugin hooks get no timeout.
- Post hook's non-zero exit is ignored. A pre hook's PM_STATUS is from the unlocked replay.
- PM_LABELS is space-separated (matches `pm get labels`); the design does not fix a separator.
- Not run: test_budgets.py (I did not check whether it exists in this worktree).

BLOCKED ON OPERATOR: none.

ARTIFACTS: none outside the diff.
