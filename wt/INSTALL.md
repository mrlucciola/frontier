# wt setup

`wt/cli/wt` is a zsh script that finds its component through its own symlink, so one link
in `~/.local/bin` is the whole install. It calls `pm` by name, so `pm` must be on `PATH`
(see [pm setup](/pm/INSTALL.md)).

## Prerequisites

- `zsh`, `git`, `/usr/bin/python3`, and `pm` on `PATH`.
- `~/.local/bin` on `PATH`.
- This repository checked out; the commands assume `~/projects/frontier-clean`.

## Install

The `wt` on `PATH` is an older deployment until the operator's cutover; these steps
replace it.

```sh
mkdir -p ~/.local/bin ~/.config/pm/plugins
ln -sfn ~/projects/frontier-clean/wt/cli/wt ~/.local/bin/wt
ln -sfn ~/projects/frontier-clean/wt/pm-plugin ~/.config/pm/plugins/wt
```

## Verify

```sh
wt selftest
```

It runs the lifecycle in a throwaway repo and ends with `SELFTEST PASSED`. Any other
last line starts `SELFTEST FAILED`.

## Configure

Per repository, in the repo root:

- `.wt/gate`: an executable (`chmod +x`) that `finish` and `land` run in the worktree;
  non-zero refuses.
- `.wt/known-red`: one `<ticket id> <text>` per line.

Environment variables wt reads:

| Variable | Effect |
| --- | --- |
| `WT_ACTOR` | Default for `--as` on `start` |
| `PM_SESSION_ID` | Session token for claims; first choice |
| `CODEX_THREAD_ID` | Session token when `PM_SESSION_ID` is unset |
| `CLAUDE_CODE_SESSION_ID` | Session token when both above are unset (`start`'s adoption check) |
| `WT_FAULT_REPORT_DIR` | Directory for the deduplicated fault rows; default `$HOME/frontier/docs/backlog/inbox/infra-faults` |
| `GIT_PAIRS_FILE` | Git-pairs file read by the cross-repo guard; default `~/.claude/git-pairs.json` |

## Disable and remove

Remove the links; the component directory and all tickets are untouched. Worktrees and
`.wt/` files in repositories stay.

```sh
rm ~/.local/bin/wt
rm ~/.config/pm/plugins/wt
```

Delete the repository checkout if you no longer want it.
