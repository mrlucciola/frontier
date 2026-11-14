# pm setup

`pm/cli/pm` is a standard-library Python script that needs only `/usr/bin/python3`.
It finds its component through its own symlink, so one link in `~/.local/bin` is the
whole install.

The `pm` on `PATH` today is the frontier deployment at `~/.local/libexec/pm`. Switching
`pm` to this component is a separate operator-run cutover runbook. The steps below are
for a machine without `pm`, or for a side install under another name (`pm-next`) that
leaves the existing `pm` untouched.

## Prerequisites

- `/usr/bin/python3` and `git`.
- `~/.local/bin` on `PATH`.
- This repository checked out; the commands assume `~/projects/frontier-clean`.

## Install

Side install, next to an existing `pm`:

```sh
mkdir -p ~/.local/bin
ln -s ~/projects/frontier-clean/pm/cli/pm ~/.local/bin/pm-next
```

On a machine without `pm`, link it as `pm` instead:

```sh
mkdir -p ~/.local/bin
ln -s ~/projects/frontier-clean/pm/cli/pm ~/.local/bin/pm
```

Run `ls -l ~/.local/bin/pm` first. If it exists, `ln -s` refuses; leave it and use
`pm-next`.

## Verify

```sh
pm-next --help
pm-next ticket stores
```

`--help` prints `usage: pm <family> <verb> [args...]` and the two families, `ticket`
and `view`. `stores` lists the registered stores and exits 0; it prints nothing when
no registry file exists yet (see the registry in the [README](/pm/README.md)).
To start a store in a repository, run `pm-next ticket init --prefix <prefix>` from
its root.

## Disable

Remove the link; the component directory is untouched.

```sh
rm ~/.local/bin/pm-next
```

## Remove

Remove the link as above, then delete the repository checkout if you no longer want
it. Removal changes no ticket data: each store is plain files under `.pm/` inside its
own repository, and the registry (`~/.config/pm/stores.json`) is a separate file this
component never deletes. The frontier `pm` reads the same `.pm/` stores.
