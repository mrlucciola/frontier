# pm-wt-rewrite/01/01d pm core test_cli_contract.py fc-c3514f:fc-2b34c9

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-d-contract-tests.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/01d pm core test_cli_contract.py fc-c3514f:fc-2b34c9

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/01-core-d-contract-tests.md`

You are a worker on ticket **fc-2b34c9** (pm core), last of four serial workers on its
branch. Earlier workers built the entry, `store.py`, `gitcommit.py` and the verbs
`init`, `create`, `show`; their reports are `reports/01-core-a.md`, `01-core-b.md` and
`01-core-c.md` under `docs/programs/pm-wt-rewrite/initiatives/01-pm/` in the worktree.
You write `pm/tests/test_cli_contract.py`: black-box tests for what the new CLI must
do and the old one does not. You fix CLI code only where a test you write exposes a
defect in this ticket's surface, and you say so.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9`, branch
  `fc-2b34c9`. Every path you edit is under it; every git command is
  `git -C <worktree> ...`. If the worktree does not exist, stop and report.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`
  (branch and write rules, budget, report shape). You never run `wt`, `pm ticket`
  writes, rebase or merge. Commit on the branch and stop.
- Code standard: `docs/component-principles.md` rule 5: the tests run the real
  executable and read its output and exit code; they import nothing from `pm/tools`.

## Read first (selectively: budget is 80k tokens / 40 tool calls)

- The three reports; `pm ticket show fc-2b34c9` (body and notes);
  `pm/docs/cut-list.md` ("What the cuts change", "New-contract tests").
- `pm/tests/test_cli_parity.py` lines 1-72 for the harness idiom to copy (empty
  registry via `PM_STORES_FILE`, `run()`), and `pm/tools/store.py` for the compacted
  and archived refusal texts.
- Old core tests, read-only, for the compacted-row fixture and expectations:
  `/Users/matthias/frontier/runtime-tools/pm/ticket/tests/test_ticket_core.py`
  1541-1660. The old fixture builds compacted rows with the sweep, which is deferred;
  yours writes the epic's `subtasks` entry into `.pm/tickets.jsonl` directly, in the
  shape SPEC.md section 4 gives.

## Deliver

`pm/tests/test_cli_contract.py`, standard-library `unittest`, runnable with
`/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'`,
driving `pm/tools/ticket` as a subprocess. Cases:

1. Each dropped verb (`upgrade`, `adopt`, `fix-labels`, `notes-prune`) exits 2.
2. No call writes a telemetry file: with `HOME` pointed at a temp dir and
   `PM_TELEMETRY_DIR` unset, run `init`, `create`, `show`, and assert nothing appears
   under the temp home except what the store itself writes.
3. `show <id> --field <name>`: repeatable, one line per field in order, lists
   comma-joined, null as an empty line, booleans `true`/`false`; an unknown field
   exits 1; `--field` with `--json` exits 2.
4. Compacted rows: an epic carrying a `subtasks` array loads; `show --json <compacted
   id>` answers with `compacted: true` and `status: closed`; text `show` of it says
   `compacted into <epic> on close`; text `show` of the epic lists `subtasks:`.
5. Every mutating kept verb refuses a compacted id with exit 1 and the store's
   compacted-refusal text, and an archived id with `<id> is archived; it cannot be
   changed. File a new ticket.` (write the archived row and its
   `archive-index.jsonl` entry by hand, per SPEC.md section 6). A verb whose file
   does not exist yet under `pm/tools/verbs/` is skipped with
   `self.skipTest("unbuilt: <verb>")` so the count is visible; the integration
   ticket removes that branch.
6. `validate` fix hints never name a dropped verb: same skip rule while
   `pm/tools/verbs/validate.py` does not exist.
7. The unbuilt contract: with `PM_UNBUILT_LOG` set to a temp file, a kept verb with no
   file exits 70, prints `pm: '<verb>' is not built yet`, and appends its name to the
   log. Pick the verb at run time from the kept list as one with no file; skip when
   every kept verb is built.

Do not edit `pm/tests/test_cli_parity.py`, `pm/tests/run_parity.py` or anything under
`pm/docs/`. Never write under `~/frontier`.

## Gate (run from the worktree root, all must pass)

```sh
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py' -v
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k test_create_show_roundtrip
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

Paste the contract run's summary and every `skipped` line. The last must exit 0 with
`failed 0`; paste its `parity:` line.

## Report

Commit on `fc-2b34c9` with explicit `git add` paths, message `pm core: CLI contract
tests (fc-2b34c9)` plus the trailer
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write the report, in
the worker-brief shape, to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-2b34c9/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/01-core-d.md`,
commit it on the same branch, and print only that path.
