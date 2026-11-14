# Step 3 worker rules (pm rewrite, fc-c3514f)

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md`

Every `03*` prompt cites this file; it is binding for the worker that runs one. It is
not launched on its own.

## State you start from

`pm/cli/pm`, `pm/tools/ticket` (entry, kept-verb tuple, routing before `run`),
`pm/tools/store.py`, `pm/tools/routing.py`, `pm/tools/gitcommit.py` and the verbs
`init create show where stores` are merged. A verb file exposes `register(subparsers)`
and `run(args)`; read `pm/tools/verbs/show.py` and `create.py` for the shape. Up to
three other workers are building other verb files on other branches at the same time.

## Where you work

- Only in the worktree your prompt names (`/Users/matthias/projects/frontier-clean/.worktrees/<ticket>`,
  branch `<ticket>`). Every git command is `git -C <worktree> ...`. `cd` is refused by a
  hook: use absolute paths. Temp stores and git repos go in `$TMPDIR` (tempfile
  defaults); `git init` inside the repo's `.tmp/` is denied by the sandbox. If the
  worktree does not exist, stop and report.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
  You never run `wt`, `pm ticket` writes, rebase or merge. Commit on the branch and stop.
- Budget: 80k tokens / 40 tool calls. Near it, commit what is green and list the rest in
  NOT DONE; a partial report is expected when a verb is larger than it looked.
- Code standard: `docs/component-principles.md`; a reviewer reads each verb file cold
  against its three questions.

## Rules

- Your write set is the verb files your prompt names, plus additive helpers in
  `pm/tools/store.py` (and `routing.py` or `gitcommit.py` only where the prompt says).
  Additive means new functions or new keyword arguments with defaults; a change to an
  existing function's signature or behavior stops you: report it in NOT DONE.
- A helper earns `store.py` when three verbs need it; until then it lives in the verb.
  Before writing one, `rg -n 'def <name>' pm/tools` to reuse what exists.
- Output, refusal texts and exit codes are byte-identical to the old CLI: the
  integration ticket diffs both CLIs on live stores. Old source, read-only:
  `/Users/matthias/frontier/runtime-tools/pm/ticket/src/ticket` and `ticket_core.py`.
  Line numbers move as the old pm changes; find functions with `rg -n 'def <name>'` and
  read only them, never a whole file.
- Anything you do not build calls `store.unbuilt("<name>")`, never fails silently.
- Never edit `pm/tests/test_cli_parity.py`, `pm/tests/run_parity.py` or `pm/docs/spec/`;
  a parity test that looks wrong goes in NOT DONE with its name and why. Never write
  under `~/frontier`. Edit `pm/docs/cut-list.md` only where your prompt says.
- `pm/tests/test_cli_contract.py` skips a refusal case as `unbuilt: <verb>` while the
  verb file is missing. When your verb lands, its cases run: they must pass, or you
  fix the test's argv shape for your verb and say so in DID.

## Gate, common to every step-3 worker

Run from the worktree root, by absolute path. Redirect each parity run to a file under
the worktree's `.tmp/` and read only its tail.

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k <your classes or tests> --allow-pending
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

Every run exits 0 with `failed 0`. The full run (about two to four minutes) runs once,
at the end; paste its `parity:` and `unbuilt verbs still needed:` lines, and the
`parity:` line of the narrow run with every `pending:` line it printed.

## Report

Commit on your branch with explicit `git add` paths and the message your prompt gives,
plus the trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the
report in the worker-brief shape to the path your prompt names, commit it on the same
branch, and print only that path.
