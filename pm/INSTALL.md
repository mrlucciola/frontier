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

`pm hook session-start|prompt|stop` is what the harness runs; the registration below
only calls it. It needs the `pm` verbs merged to the main checkout, because the
command names `/Users/matthias/projects/frontier-clean/pm/cli/pm`.

### Kiro

The registration is `pm/config/kiro/hooks.json`: `SessionStart` and `UserPromptSubmit`
stdout is added to the model's context, and a `Stop` hook that exits 2 blocks the stop
and shows its stderr to the model. Kiro reads hooks from `~/.kiro/hooks/`; the trust
and registration mechanics are CONFIRM recon items, as is the shape of the stdin each
event sends — see [the branch policy](/docs/kiro-branch.md).

1. Place the fragment where kiro reads hooks.

   ```sh
   mkdir -p ~/.kiro/hooks
   cp ~/projects/frontier-clean/pm/config/kiro/hooks.json ~/.kiro/hooks/pm.json
   ```

2. Start `kiro-cli --v3` in the repository and let it trust the three hooks if it
   asks (CONFIRM).

#### Verify

In a fresh `kiro-cli --v3` session started in a repository with a `.pm/` store, the
first context holds `pm tickets in this repo:` and `All verbs: pm help`. Take a ticket
(`pm take`) and end the turn: the stop is blocked once with the four ways out. In a
directory without a store nothing is added.

```sh
printf '{"cwd":"%s","session_id":"x"}' "$PWD" | /Users/matthias/projects/frontier-clean/pm/cli/pm hook session-start
```

#### Remove

Delete `~/.kiro/hooks/pm.json`; nothing else was installed, and no ticket data
changes. Disabling and re-enabling are the same delete and copy.
