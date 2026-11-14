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

`pm hook session-start|prompt|stop` is what a harness runs; the Claude Code and
opencode wiring below only call it. Both need the `pm` verbs merged to the main
checkout, because the commands name `~/projects/frontier-clean/pm/cli/pm`. The old
hooks and plugin stay registered until you replace them, and both generations must
not run in one session: do the replacement in one go.

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
