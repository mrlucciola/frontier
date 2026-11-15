# pm setup

`pm/cli/pm` is a standard-library Python script that needs only `/usr/bin/python3`. It
finds its component through its own symlink, so one link in `~/.local/bin` is the whole
install. Until the operator's cutover the `pm` on `PATH` is the frontier deployment at
`~/.local/libexec/pm`; the link is named `pm-next` so that one is untouched. At cutover
the link is named `pm` instead.

## Prerequisites

- `/usr/bin/python3` and `git`.
- `~/.local/bin` on `PATH`.
- This repository checked out; the commands assume `~/projects/frontier-clean`.

## Install

Side install, next to the existing `pm`:

```sh
mkdir -p ~/.local/bin
ln -s ~/projects/frontier-clean/pm/cli/pm ~/.local/bin/pm-next
```

### Plugins

A plugin is a directory under `~/.config/pm/plugins/` (or `$PM_PLUGINS`); its name is
the subcommand. Link the two shipped ones:

```sh
mkdir -p ~/.config/pm/plugins
ln -s ~/projects/frontier-clean/pm/plugins/dispatch ~/.config/pm/plugins/dispatch
ln -s ~/projects/frontier-clean/pm/plugins/pilot ~/.config/pm/plugins/pilot
```

`pm-next dispatch <id>` and `pm-next pilot` then work. Plugin scripts call `pm` by
name, so they reach the frontier pm until the cutover.

## Verify

```sh
pm-next help
```

It prints the verb table, starting with `pm keeps this repo's tickets in .pm/.` and
listing `take [id]` through `hook event`.

## Disable

Remove the link; the component directory is untouched. A plugin is disabled by
removing its link.

```sh
rm ~/.local/bin/pm-next
rm ~/.config/pm/plugins/dispatch ~/.config/pm/plugins/pilot
```

## Remove

Remove the links as above, then delete the repository checkout if you no longer want
it. Removal changes no ticket data: each store is plain files under `.pm/` inside its
own repository, and a plugin's events stay in the log and are ignored. The registry
`~/.config/pm/stores` is not touched; delete it, or a line of it, by hand.

## Harness hooks

`pm hook session-start|prompt|stop` is what a harness runs; the Claude Code, opencode
and Codex wiring below only call it. Each needs the `pm` verbs merged to the main
checkout, because the commands name `~/projects/frontier-clean/pm/cli/pm`. The old
Claude hooks and opencode plugin stay registered until you replace them, and both
generations must not run in one session: do the replacement in one go. Codex has no
old pm hooks to replace.

### Claude Code

The registrations are `pm/config/claude/hooks.json`: SessionStart and UserPromptSubmit
stdout is added to the model's context, and a Stop hook that exits 2 blocks the stop
and shows its stderr to the model. Claude's settings are generated from
`~/frontier/config/claude/settings.config.json`; never edit `~/.claude/settings.json`.

1. In `/Users/matthias/frontier/config/claude/settings.config.json`, under
   `SessionStart` (lines 183-190 today).

   replace these lines:

   ```json
             {
               "args": [
                 "/Users/matthias/.claude/hooks/pm/session_start.py"
               ],
               "command": "/usr/bin/python3",
               "timeout": 10,
               "type": "command"
             }
   ```

   with this:

   ```json
             {
               "command": "/Users/matthias/projects/frontier-clean/pm/cli/pm hook session-start",
               "timeout": 10,
               "type": "command"
             }
   ```

2. In the same file, under `Stop` (lines 212-219 today).

   replace these lines:

   ```json
             {
               "args": [
                 "/Users/matthias/.claude/hooks/pm/stop.py"
               ],
               "command": "/usr/bin/python3",
               "timeout": 10,
               "type": "command"
             }
   ```

   with this:

   ```json
             {
               "command": "/Users/matthias/projects/frontier-clean/pm/cli/pm hook stop",
               "timeout": 10,
               "type": "command"
             }
   ```

3. In the same file, under `UserPromptSubmit`, add one more entry to the `hooks` list
   of its first group, after the last existing entry.

   add this:

   ```json
             {
               "command": "/Users/matthias/projects/frontier-clean/pm/cli/pm hook prompt",
               "timeout": 5,
               "type": "command"
             }
   ```

4. Preview, then deploy.

   ```sh
   python3 /Users/matthias/frontier/bin/deploy deploy config-claude --provider claude --dry-run
   ```

   Hand the line without `--dry-run` to the operator session that owns deploys.

#### Verify

In a fresh Claude session started in a repository with a `.pm/` store, the first
context holds `pm tickets in this repo:` and `All verbs: pm help`. Take a ticket
(`pm take`) and end the turn: the stop is blocked once with the four ways out. In a
directory without a store nothing is added.

```sh
printf '{"cwd":"%s","session_id":"x"}' "$PWD" | /Users/matthias/projects/frontier-clean/pm/cli/pm hook session-start
```

#### Disable

Delete the three `pm hook` entries from the source settings and deploy again; the
old `hooks/pm/*.py` entries (see steps 1 and 2) restore the previous behavior.

#### Remove

Same as disable; nothing else was installed, and no ticket data changes.

### opencode

`pm/hooks/opencode/pm.ts` builds the JSON and calls `pm hook`. It replaces the plugin
at `~/.config/opencode/plugins/pm/index.ts`, which `~/.config/opencode/opencode.json`
already lists under `plugins`, so the config needs no edit.

1. Keep the old plugin and link the new one in its place.

   ```sh
   mv ~/.config/opencode/plugins/pm/index.ts ~/.config/opencode/plugins/pm/index.ts.old
   ln -s ~/projects/frontier-clean/pm/hooks/opencode/pm.ts ~/.config/opencode/plugins/pm/index.ts
   ```

2. The plugin runs `$PM_BIN`, else `~/.local/bin/pm`. Until the cutover that is the
   old pm, which has no `hook` verb, so start opencode against the side install.

   ```sh
   PM_BIN=~/.local/bin/pm-next opencode
   ```

#### Verify

Start opencode as in step 2, in a repository with a `.pm/` store; send one prompt. The session's
`pm` instruction entry holds the `pm tickets in this repo:` text. Take a ticket, let
the turn go idle: one `[pm] You still hold ...` turn arrives, once.

#### Disable

Move the old file back over the link; the plugin entry in `opencode.json` stays.

```sh
mv ~/.config/opencode/plugins/pm/index.ts.old ~/.config/opencode/plugins/pm/index.ts
```

#### Remove

Delete the link and, if you do not want the old plugin, `index.ts.old`.

### Codex

The registrations are `pm/config/codex/hooks.json`, the same shape as Claude's. Codex
reads hooks from `~/.codex/hooks.json`, which an operator edits; the deploy never
writes it. Codex 0.167.0 is the client checked.

What is proven from the installed client (`/Users/matthias/.codex/packages/standalone/current/bin/codex`,
a native binary with no bundled docs, so the evidence is its own embedded text and one
earlier live session):

| Claim | Evidence |
| --- | --- |
| The `hooks` feature is stable and on | `codex features list` prints `hooks   stable   true` |
| Events `SessionStart`, `UserPromptSubmit`, `Stop` exist, plus `SessionEnd`, `PreToolUse`, `PostToolUse` and others | The binary embeds one JSON Schema per event, titled `session-start.command.input`, `user-prompt-submit.command.input`, `stop.command.input` and so on |
| The input has `cwd`, `session_id` and `hook_event_name` on all three; `prompt` on `UserPromptSubmit`; `stop_hook_active` and `last_assistant_message` on `Stop`; `source` (`startup`, `resume`, `clear`, `compact`, `fork`) on `SessionStart` | The same embedded schemas; these are exactly the keys `pm hook` reads, under Claude's names, so the fragment calls `pm hook <event>` with no adapter. `pm hook` ignores the extra keys |
| The file format is `{"hooks": {"<Event>": [{"hooks": [{"type": "command", "command", "timeout"}]}]}}` | `~/.codex/hooks.json` runs two `UserPromptSubmit` commands today |
| `UserPromptSubmit` stdout reaches the model as plain text | `/Users/matthias/frontier/hooks/graph-memory/docs/trust-model.md` Stage C3: `codex_recall.py` prints a bare block and "injection confirmed in a real Codex session" |
| `Stop` exiting 2 with text on stderr continues the turn with that text | The binary's own message `Stop hook exited with code 2 but did not write a continuation prompt to stderr`; the `Stop` schema also accepts `{"decision":"block","reason":...}` |
| A new hook is untrusted until approved | `~/.codex/config.toml` keeps `[hooks.state."<file>:<event>:<group>:<handler>"] trusted_hash`; `codex --help` lists `--dangerously-bypass-hook-trust` |

Not yet proven, each by the probe step named:

- `SessionStart` stdout that is plain text, not JSON, is added to the model's context
  (the schema's JSON form is `hookSpecificOutput.additionalContext`; the binary also
  says `hook returned invalid session start JSON output`). Proved by the Verify
  section below; probe step 4 only shows the event fires, with its `source`.
- The three events fire under `codex exec`, not only interactively (probe step 3).
- Whether a scratch `CODEX_HOME` keeps Codex's login. The binary reads `CODEX_HOME`;
  where the login lives I have not checked (probe step 2).

If `SessionStart` does not exist or its plain stdout is ignored, the repository
`AGENTS.md` line that `pm init` prints carries the guidance: `Tickets live in .pm/. Run
`pm`.` Codex reads `AGENTS.md` on its own. If the probe shows a field differing from
the table above, an adapter is needed; none is written.

#### Probe

Registers a recorder for the three events in a scratch Codex home, runs one short
session and reads what Codex sent. Nothing in `~/.codex` changes. Start after the
`pm` verbs are merged to the main checkout.

1. Create the scratch home and the recorder registration.

   ```sh
   mkdir -p /Users/matthias/projects/frontier-clean/.tmp/codex-probe/home
   cp /Users/matthias/projects/frontier-clean/pm/tests/codex/hooks.json /Users/matthias/projects/frontier-clean/.tmp/codex-probe/home/hooks.json
   ```

2. Sign in to the scratch home, since I could not tell whether the login carries over
   from `~/.codex`. If you would rather not sign in again, tell me.

   ```sh
   CODEX_HOME=/Users/matthias/projects/frontier-clean/.tmp/codex-probe/home /Users/matthias/.local/bin/codex login
   ```

3. Run one short session. The flag skips the trust prompt for this run only.

   ```sh
   CODEX_HOME=/Users/matthias/projects/frontier-clean/.tmp/codex-probe/home /Users/matthias/.local/bin/codex exec --dangerously-bypass-hook-trust -C /Users/matthias/projects/frontier-clean "Reply with the single word ok."
   ```

   If step 4 shows fewer than three lines, `exec` does not fire every event: run
   `CODEX_HOME=... /Users/matthias/.local/bin/codex --dangerously-bypass-hook-trust -C /Users/matthias/projects/frontier-clean`
   interactively, send the same prompt, and exit.

4. Read the capture.

   ```sh
   cat /Users/matthias/projects/frontier-clean/.tmp/codex-probe/capture.jsonl
   ```

   Expect one line each for `SessionStart`, `UserPromptSubmit` and `Stop`; each `stdin`
   holds `cwd` and `session_id`, `UserPromptSubmit` holds `prompt`, and `Stop` holds
   `stop_hook_active`. Send me the file.

5. Sign the scratch home out, so no login stays in the repository's `.tmp/`. `codex
   --help` lists `logout` ("Remove stored authentication credentials"). I have not
   checked how Codex stores the login: if the `ls` still shows a login file (for
   example `auth.json`), remove that file by hand.

   ```sh
   CODEX_HOME=/Users/matthias/projects/frontier-clean/.tmp/codex-probe/home /Users/matthias/.local/bin/codex logout
   ls -a /Users/matthias/projects/frontier-clean/.tmp/codex-probe/home
   ```

   Expect no login file in the listing; `hooks.json` and Codex's own state files may
   remain.

Unregister by not setting `CODEX_HOME`. The scratch home is ignored by git and holds no
login after step 5.

#### Register

Trigger: the `pm` verbs are merged to the main checkout and the probe capture matches
the table. This adds the three `pm hook` entries to `~/.codex/hooks.json`; the two
existing `UserPromptSubmit` entries stay.

1. Open the file.

   ```sh
   $EDITOR /Users/matthias/.codex/hooks.json
   ```

   replace these lines (17-22 today):

   ```json
             }
           ]
         }
       ]
     }
   }
   ```

   with this:

   ```json
             },
             {
               "type": "command",
               "command": "/Users/matthias/projects/frontier-clean/pm/cli/pm hook prompt",
               "timeout": 5
             }
           ]
         }
       ],
       "SessionStart": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "/Users/matthias/projects/frontier-clean/pm/cli/pm hook session-start",
               "timeout": 10
             }
           ]
         }
       ],
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "/Users/matthias/projects/frontier-clean/pm/cli/pm hook stop",
               "timeout": 10
             }
           ]
         }
       ]
     }
   }
   ```

2. Check the file parses and equals the shipped fragment's three events.

   ```sh
   /usr/bin/python3 -c 'import json; print(sorted(json.load(open("/Users/matthias/.codex/hooks.json"))["hooks"]))'
   ```

   Expect `['SessionStart', 'Stop', 'UserPromptSubmit']`.

3. Start Codex in `/Users/matthias/projects/frontier-clean`. It asks to trust the three
   new hooks (`/hooks` lists them); accept each.

4. Verify as below.

#### Verify

In a fresh Codex session in a repository with a `.pm/` store, ask what the context says
about `pm tickets in this repo`. It quotes the `pm tickets in this repo:` text from
`SessionStart`; that is the one claim marked not yet proven. Send a prompt that
names a ticket id: the model sees `mentioned:` and the line. Take a ticket (`pm take`)
and end the turn: Codex continues once with the four ways out. In a directory without a
store nothing is added.

```sh
printf '{"cwd":"%s","session_id":"x"}' "$PWD" | /Users/matthias/projects/frontier-clean/pm/cli/pm hook session-start
```

#### Disable

Delete the three `pm hook` entries from `~/.codex/hooks.json`; the two existing
`UserPromptSubmit` entries are the original file.

#### Remove

Same as disable; nothing else was installed, and no ticket data changes. The
`[hooks.state]` entries Codex wrote to `config.toml` are inert and may stay.
