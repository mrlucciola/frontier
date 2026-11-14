# pm setup

The new pm is not ready to install. Until the operator's cutover, the `pm` on `PATH` is
the frontier deployment at `~/.local/libexec/pm`; use that.

Once the build lands, `pm/cli/pm` is a standard-library Python script that needs only
`/usr/bin/python3`. It finds its component through its own symlink, so one link in
`~/.local/bin` named `pm-next` is a side install that leaves the existing `pm`
untouched.

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

## Verify

Works once the `pm/cli/pm` dispatcher exists.

```sh
pm-next help
```

It prints the verb list.

## Disable

Remove the link; the component directory is untouched.

```sh
rm ~/.local/bin/pm-next
```

## Remove

Remove the link as above, then delete the repository checkout if you no longer want
it. Removal changes no ticket data: each store is plain files under `.pm/` inside its
own repository.
