# pm-wt-rewrite/02/02e wt pm plugin: pre-done, post-take, orient fc-262fa8:fc-347c67

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02e-pm-plugin.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/02e wt pm plugin: pre-done, post-take, orient fc-262fa8:fc-347c67

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02e-pm-plugin.md`

You are a worker on ticket fc-347c67. You start with zero context. Your worktree is
`/Users/matthias/projects/frontier-clean/.worktrees/fc-347c67` on branch `fc-347c67`; the
overseer created it. `WT/` is that worktree's `wt/`.

First read `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`:
its binding rules, code rules and report section bind you. Its suite gate does not apply
to you (you write no verb); yours is below.

## Deliver

Read `pm ticket show fc-347c67` (the spec) and
`/Users/matthias/projects/frontier-clean/pm/docs/design.md`, section "Plugins" (the four
hook files, the environment a hook receives: `PM_OP`, `PM_ID`, `PM_STORE` the repository
root, `PM_BY`, `PM_STATUS`, `PM_TEXT`, `PM_LABELS`, plus the caller's environment), and
the shipped plugins under `/Users/matthias/projects/frontier-clean/pm/plugins/` and their
transcripts 15, 22 and 23 under `pm/tests/t/` (read-only) for the pattern.

1. `WT/pm-plugin/` -- the directory the operator symlinks as `~/.config/pm/plugins/wt`:
   - `pre-done`: refuses while `$PM_STORE/.worktrees/$PM_ID` exists, unless
     `WT_CALLER=1`; the refusal (stdout, one line) names `wt finish <id>` and
     `wt park <id>`. It must stay under pm's refusal budget (design.md "Size budgets":
     300 bytes for any refusal).
   - `post-take`: prints `next: wt start <id>` when `$PM_STORE/.worktrees` exists and
     `WT_CALLER` is not `1`.
   - `orient`: one line per directory under `<store>/.worktrees/` whose ticket is
     `done` or has no holder (read with `pm get <id> status holder`); nothing when none.
     Name the line so an agent knows what to run (`wt finish <id>` for done, `wt start`
     or `wt park` for an unheld one: decide from the contract and say why in the report).
   Each an executable zsh file. Reading tickets only through `pm get`.
2. Transcripts in `WT/tests/t/` in the format of
   `/Users/matthias/projects/frontier-clean/pm/tests/run_transcripts.py` (read its
   docstring), run by that runner with `--dir`. Each transcript installs the plugin with
   `ln -s` into `$PM_PLUGINS` (the runner sets `PM_PLUGINS=$T/plugins`; the plugin dir is
   reachable from `$FIXTURES`, which is `pm/tests/fixtures` of the same checkout, as
   `$FIXTURES/../../../wt/pm-plugin`). Cover: `pm done` refused while the worktree
   exists, allowed with `WT_CALLER=1`, allowed once the worktree is gone; `post-take`
   hint present with a `.worktrees` dir, absent without one and absent under
   `WT_CALLER=1`; `orient` listing a done ticket's worktree and an unheld one, and silent
   otherwise. Make the worktree directories with `mkdir -p` (the plugin checks the
   directory, not git).
3. A line in `WT/README.md` or `WT/INSTALL.md` is not yours: the integration ticket
   writes the docs. Do not edit them.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-347c67/pm/tests/run_transcripts.py --cli /Users/matthias/projects/frontier-clean/.worktrees/fc-347c67/pm/cli/pm --dir /Users/matthias/projects/frontier-clean/.worktrees/fc-347c67/wt/tests/t
```

must exit 0 (`failed 0`). `/bin/zsh -n` on each plugin file, one call each. Paste the
runner's last two lines in EVIDENCE.

## Report

`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/02e-pm-plugin.md`
