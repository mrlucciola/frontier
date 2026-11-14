# Step 2 common brief (read by every step-2 worker; not launched on its own)

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`

Your own prompt names your ticket, your worktree and your deliverable. This file holds
what every step-2 worker shares. Where your own prompt and this file differ, your prompt
wins.

## Binding rules

- `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds
  you: read it first. Work only in the worktree your prompt names; every git command is
  `git -C <worktree> ...`. Never run the installed `wt` (it is the old tool running this
  epic), never mutate tickets with `pm ticket`, never merge.
- Stop at 80k tokens or 40 tool calls, commit what is green, report the rest under NOT
  DONE.
- Read-only: everything under `~/frontier`, `~/.local`, `~/.config/pm`, provider config
  dirs; this repo's `pm/`; **`wt/tests/test_wt_cli.py` and `wt/tests/run_wt.py`**
  (accepted: a test that looks wrong is reported in NOT DONE, never edited); and
  **`wt/cli/wt` and `wt/tools/lib/`** (the core: a change you need goes in NOT DONE with
  the exact edit, and the overseer makes it). You write only the files your prompt names.
- **Throwaway repos for hand checks live under `$TMPDIR`**, the way the suite builds
  them, never under a worktree's `.tmp/` (the sandbox refuses `git init` there, and git
  then falls through to the real repository: this happened once). A driver script stops
  at once if `git init` fails. Prefer running the suite over hand drivers.
- The code under `wt/` is never put on `PATH`. Tests reach it by path.

## The core you build on

`wt/cli/wt` sources every `wt/tools/lib/*.zsh`, sources `wt/tools/verbs/<verb>.zsh`, then
calls `wt_verb "$@"`; your verb file defines `wt_verb` and returns its exit status.
Globals for verbs: `WT_TOOLS`, `WT_COMPONENT`, `WT_VERB` (`land` is dispatched to
`finish.zsh` with `WT_VERB=land`). The lib functions and their intended callers are listed
in `docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01a-core.md` and
`01b-teardown.md` (main checkout). Read both and the lib files before writing; use the
lib, do not re-implement it.

## Rules for verb code

zsh only; `emulate -L zsh` in every function; quoted paths; explicit `return`s. JSON is
never parsed in zsh: read a ticket with `pm get <id> <field>` (one value per line), change
it with `pm take`, `pm done`, `pm park`, `pm drop`, keep wt's facts with
`pm emit <id> wt.<name> key=value`, read them back with `pm get <id> wt.<key>`; every pm
call goes through the lib's `wt_pm*` wrappers, which export `WT_CALLER=1`. Never
`git branch -D`, `git worktree remove --force` or `rm -rf`. Comments only for constraints
the code cannot show; no ticket ids in code. Arguments are parsed in the verb file
(principle 1). Every refusal names what was refused and the next command to run.

## Facts and rulings (overseer; do not re-derive)

- New pm facts: `pm get <id> store` prints the store's repo root; an unregistered prefix
  exits 1 with `pm: no store has prefix <p>. Known: ...`; an unknown id exits 1 with
  `pm: no ticket <id>. ...`. Identity: `by` is `<actor>#<token>`, the token from
  `PM_SESSION_ID`, then `CLAUDE_CODE_SESSION_ID`, then `CODEX_THREAD_ID`.
- **Adoption needs actor and token.** pm calls a ticket "yours" when the tokens match,
  whatever the actor; `start` adopts only when the holder's actor and token both equal
  the ones it would take with, else refuses (`test_refuses_foreign_claim_other_actor`).
- **The gate**: an executable `.wt/gate` in the store repo; its label in wt's lines is
  the literal `.wt/gate`; a non-executable one refuses (`wt:` line with `gate` and
  `fix it or pass --no-gate.`). Known reds: `.wt/known-red`.
- **Findings** are checked by reading `findings_required` through the lib, never by
  `pm done --dry-run` (it also runs `pre-done` plugins, which would move a guard's
  after-merge refusal to before the merge).
- **`refs/wt/merged/<id>` stays a git ref** (the suite reads it); a `pm emit` of the
  same fact is optional.
- **Fault rows**: `$WT_FAULT_REPORT_DIR`, one file per root cause and day.
- **Where the old wt deviates from the contract** a test pins the contract on the new
  side (docstring `Old wt deviates from the contract:`); you build the new-side
  behavior.
- **finish -> park interface.** `finish` auto-parks by running the dispatcher as a
  subprocess: `"$WT_COMPONENT/cli/wt" park <id> --auto [--store S] [--repo R]`. With
  `--auto`, park prints only its note (the old `cmd_park(auto=True)` return value, ending
  `; auto-parked by an infrastructure fault, not a finding: file no ticket`) on stdout,
  prints no `OK:` line, defaults findings to `none` on a `findings_required` store, and
  exits 0; finish wraps the note in its own line, as the old `cmd_finish` does.

## Gate (every step-2 worker)

```sh
/usr/bin/python3 -B <worktree>/wt/tests/run_wt.py --cli <worktree>/wt/cli/wt --pm new --allow-pending
```

must exit 0 (`failed 0`), and every test still pending must name, as its first unbuilt
step, a verb that is not yours. Your prompt names the test classes that must have no
pending or failed test at all. Also `/bin/zsh -n` on each file you wrote, one call each.
Paste the runner's last two lines and every `pending:` line that names one of your verbs
(there must be none) in EVIDENCE.

## Report

Commit on your ticket branch with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
the path your prompt names (main checkout; do not commit it) in the worker-brief shape,
and print only that path.
