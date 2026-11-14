# pm-wt-rewrite/01/01a pm core entry, store.py, init fc-c3514f:fc-2b34c9

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-a-entry-store-init.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/01a pm core entry, store.py, init fc-c3514f:fc-2b34c9

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-a-entry-store-init.md`

You are a worker on ticket **fc-2b34c9** (pm core). This prompt is the first of four
serial workers on that ticket's branch; you build the entry, the store module and
`init`. Later workers build `gitcommit.py`, then `create` and `show`, then
`test_cli_contract.py`. Do only your part.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9`, branch
  `fc-2b34c9`. Every path you edit is under it; every git command is
  `git -C <worktree> ...`. If the worktree does not exist, stop and report.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`
  (branch and write rules, budget, report shape). You never run `wt`, `pm ticket`
  writes, rebase or merge. Commit on the branch and stop.
- Code standard: `docs/component-principles.md`. Read it first; a reviewer reads each
  file you write cold against its three questions.

## Read first (selectively: budget is 80k tokens / 40 tool calls)

- `pm/AGENTS.md`, `pm/docs/cut-list.md` (kept verbs, dropped verbs, compacted rows).
- `pm ticket show fc-2b34c9`: the body and its note are the spec.
- `pm/docs/spec/v2/SPEC.md` sections 1 (layout), 3 (`config.json`), 4 (rows), 6
  (archive), 9 (`init` contract).
- `pm/tests/run_parity.py` (the pending rule and `$PM_UNBUILT_LOG`).
- Old source, read-only reference, at
  `/Users/matthias/frontier/runtime-tools/pm/ticket/src/`. Do NOT read whole files
  (`ticket` 3114 lines, `ticket_core.py` 2783). Read these ranges with offset/limit:
  `ticket_core.py` 792-870 (`_worktree_main`, `find_store`), 871-1060 (`Store`: load,
  `get`, the compacted and archived refusals at 920-935, `compacted` at 990),
  1240-1330 (row checks incl. `subtasks`), 1721-1755 (`read_archive_index`,
  `open_store`), 2142-2222 (`locked_store`); `ticket` 107-112 (`die`), 160-173 (`locked`), 244-266
  (`cmd_init`), 1361-1374 (`_write_gitignore_v2_lines`), 2747-2800 and the
  `_main` parser build after it (global flags, epilog with exit codes).

## Deliver

1. `pm/cli/pm`: executable dispatcher. `pm ticket <verb> ...` and `pm view <verb> ...`
   exec `/usr/bin/python3 <component>/tools/ticket <verb> ...`. Anything else prints
   usage and exits 2. Resolve the component dir through symlinks.
2. `pm/tools/ticket`: Python script, no extension, `#!/usr/bin/python3`, executable.
   The harness runs `[sys.executable, pm/tools/ticket, <verb>, ...]`.
   - One fixed tuple of every kept verb, in the cut list's order:
     `init create show list ready tree summary claim hold release close reopen note
     edit dep unlink reparent where stores history validate lint archive board
     overview`. A verb not in it (`upgrade`, `adopt`, `fix-labels`, `notes-prune`)
     exits 2 as argparse's unknown choice.
   - Global `--store`/`--repo` (same dest; old code calls it `repo`) accepted before or
     after the verb.
   - Lazy import: only the named verb's module `tools/verbs/<verb>.py` is imported.
     Each verb module exposes `register(subparsers)` and `run(args)`, nothing else
     required. A kept verb with no file calls `store.unbuilt(<verb>)`, including for
     `<verb> --help`.
   - Top-level `--help` epilog states the exit codes exactly as
     `HelpTextTest.test_epilog_exit_codes` expects (read that test).
3. `pm/tools/store.py`: the shared store module.
   - `unbuilt(name)`: append `name` plus newline to the file in `$PM_UNBUILT_LOG` when
     set, print `pm: '<name>' is not built yet` to stderr, exit 70.
   - Find the store from cwd or `--store`; a linked worktree resolves to the main
     checkout's store. Load `config.json` and `tickets.jsonl`; refuse a store below
     spec v2 with a message naming the old `pm ticket upgrade` in
     `~/frontier/runtime-tools/pm` (cut list, "What the cuts change").
   - Load and check rows to the depth the old `Store` load does; an epic may carry
     `subtasks`. Read lookup answers a compacted id with the synthesized closed row
     (`compacted: true`); the mutation lookup refuses a compacted id and an archived
     id with exactly the old texts (`<id> is archived; it cannot be changed. File a
     new ticket.`). The archived lookup lives here, not in verbs.
   - `.pm/lock` with `fcntl.flock`, atomic write (temp file + `os.replace`), one
     context manager a mutating verb uses: lock, load, yield, write, commit.
   - Commit: one function the write path calls. `gitcommit.py` does not exist yet;
     when the store sits in a git work tree this function calls
     `unbuilt("gitcommit")`, otherwise it does nothing. The next worker replaces its
     body. Say so in a one-line comment.
   - Write only what `init`, `create` and `show` will need plus what the body above
     names. No routing, no registry (fc-459fe0 owns them).
4. `pm/tools/verbs/init.py`: port of `cmd_init`, same output, same refusals, same
   `.gitignore` lines, `--prefix`, `--dir`, and the `--store`/`--dir` conflict.

Do not write `gitcommit.py`, `create.py`, `show.py`, `test_cli_contract.py`, any doc,
or a README. Do not edit `pm/tests/test_cli_parity.py`, `pm/tests/run_parity.py` or
anything under `pm/docs/`; a parity test that looks wrong goes in NOT DONE with the
test name and why. Never write under `~/frontier`.

## Gate (run from the worktree root, all must pass)

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_init -k HelpTextTest.test_epilog_exit_codes
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

The first must end `parity: passed 3, pending 0, failed 0, skipped 0`
(`test_init_store_flag_targets_given_root_not_cwd_store`,
`test_init_cwd_form_still_works`, `test_epilog_exit_codes`). The second must exit 0 with `failed 0`; paste its last three lines. The full
run takes about four minutes; iterate with `-k` and run it once at the end.

## Report

Commit on `fc-2b34c9` with explicit `git add` paths, message `pm core: entry, store
module, init (fc-2b34c9)` plus the trailer
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write the report, in
the worker-brief shape, to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-a.md`,
commit it on the same branch, and print only that path.
