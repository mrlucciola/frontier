# pm-wt-rewrite/02/00-1 wt characterization: runner, pm adapter, start fc-262fa8:fc-30c060

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-1-start.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/00-1 wt characterization: runner, pm adapter, start fc-262fa8:fc-30c060

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/00-characterize-1-start.md`

You are a worker on ticket fc-30c060, part 1 of 4. You start with zero context. The
overseer already ran `wt start fc-30c060`; your worktree is
`/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060` on branch `fc-30c060`.
Every edit and every commit happens there. Below, `WT/` means
`/Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you
(branch rules, never run `wt` or `pm ticket` mutations, budget, report shape). Read it
first. Its budget: stop at 80k tokens or 40 tool calls, commit what is green, and report
the rest under NOT DONE.

Read-only, never written: everything under `~/frontier`, `~/.local`, `~/.config/pm`,
provider config directories, and the `pm/` directory of this repo. No test may touch a
real repository or a registered store: every repo a test builds lives under a fresh
`tempfile.mkdtemp()` (honoring `$TMPDIR`), and every wt and pm call runs with `cwd`
inside it and the isolated environment below.

## Read, in this order

1. `pm ticket show fc-30c060` -- the ticket body is the spec for the whole suite.
2. `WT/docs/contract.md` -- the behavior to pin. Sections "Verbs" and "Settled
   decisions" for `start`.
3. `/Users/matthias/projects/frontier-clean/pm/tests/run_transcripts.py` -- the runner
   `run_wt.py` mirrors (private HOME, private bin with a `pm` symlink, fixed git
   identity, `GIT_CONFIG_GLOBAL=/dev/null`, temp dirs under `$TMPDIR`; it runs
   `git init`, commits and `git worktree add` inside the sandbox).
4. `/Users/matthias/projects/frontier-clean/pm/docs/design.md` sections "Store",
   "Verbs" and "Plugins" -- the new pm the `new` adapter side drives.
5. Old wt source, read-only: `/Users/matthias/frontier/runtime-tools/wt/cli/wt` and
   `src/wt_core.py` (`cmd_start`, `cmd_selftest` for how it isolates itself). The old
   `tests/test_wt_core.py` is reading material for cases, not a pattern: it imports
   internals; your suite never does.
6. `/Users/matthias/projects/frontier-clean/docs/component-principles.md`.

## Footing facts (verified by the overseer; do not re-derive)

- The old wt calls `pm` from `PATH`. The old pm is `/Users/matthias/.local/libexec/pm/cli/pm`
  (what `~/.local/bin/pm` points at). The new pm is `pm/cli/pm` in this repo, reached
  by path relative to the test file. The private bin dir's `pm` symlink points at the
  old or the new one by side; `PATH` is that bin dir plus `/usr/bin:/bin`.
- Old wt and old pm isolation: `WT_FAULT_REPORT_DIR` (fault rows; the new wt will honor
  the same name), `PM_STORES_FILE` (old registry: write `{"stores": []}` to a private
  file), `PM_TELEMETRY_DIR=-` (telemetry off), `GIT_PAIRS_FILE` (old crossrepo guard;
  default `~/.claude/git-pairs.json` -- point it at a private empty-pairs file if the
  old wt needs one; read `src/crossrepo.py` for the shape). New pm isolation: `PM_STORES`
  (private registry file), `PM_PLUGINS` (private plugins dir), private `HOME`.
- Unset every inherited identity variable before each call: `CLAUDE_CODE_SESSION_ID`,
  `CLAUDECODE`, `CODEX_THREAD_ID`, `CODEX_AGENT_IDENTITY`, `PM_AGENT`, `WT_ACTOR`,
  `PM_SESSION_ID`, `PM_ACTOR`. Then set a fixed `PM_SESSION_ID` per test where a test
  needs one.
- Old store: `pm ticket init --prefix <p> --dir <repo>`; tickets are tracked in
  `.pm/tickets.jsonl` and every `pm ticket` mutation commits. Old gate config:
  `.pm/config.json` keys `gate` (argv list), `known_red`, `findings_required`.
- New store: `pm init <prefix>`; `.pm/log.jsonl` is untracked. New-side gate config is
  wt's own: an executable `.wt/gate` and `.wt/known-red` (one `<ticket id> <text>` per
  line); `findings_required` is a `.pm/config.json` key, as in the old store.
- Status words in assertions are the new ones: claimed is `taken`, done-unmerged is
  `parked`, closed is `done`, open is `open`.
- The sandbox may refuse deleting a worktree's admin dir (`Operation not permitted`).
  The contract calls that deferred teardown. Where the contract allows both, accept
  both the clean and the deferred `OK:` line.

## Deliver (this part)

1. **`WT/tests/run_wt.py`** -- `/usr/bin/python3 -B wt/tests/run_wt.py --cli <wt>
   --pm old|new [-k NAME ...] [--allow-pending] [-v]`. It sets `WT_CLI_UNDER_TEST`
   (absolute path of `--cli`), `WT_PM_SIDE` (`old`/`new`) and `WT_UNBUILT_LOG` (a fresh
   temp file), runs `WT/tests/test_wt_cli.py` with stdlib `unittest`, and prints exactly
   these last two lines:
   `cli under test: <path> (pm <side>)` and
   `wt suite: passed N, pending P, skipped S, failed F`.
   Exit 0 only when `failed 0` and, without `--allow-pending`, `pending 0`. A skipped
   test prints its name and reason (with or without `-v`).
   **Pending rule** (mirrors `PLAN.md` "The pending rule"): the suite's one helper that
   runs wt checks, after every call, whether that call exited 70 and appended a line to
   `$WT_UNBUILT_LOG`; if so it ends the test as pending at once. So a test whose first
   wrong step comes at or after an unbuilt verb is pending, and one that fails before any
   is failed. Implement pending as a distinct outcome the runner counts, not as a skip.
2. **`WT/tests/test_wt_cli.py`** -- stdlib `unittest`, no imports from wt or pm. Holds:
   - the isolated environment and the one wt-runner helper (returns exit code, stdout,
     stderr separately and combined);
   - a **repo fixture**: a fresh temp dir with `git init -b main`, one commit, and a
     store, created through the adapter;
   - the **pm adapter**, one class per side behind one interface, chosen by
     `WT_PM_SIDE`: make a store (prefix, optional `findings_required`), file a ticket,
     read status (in new words), holder, and note texts, take a ticket as a given
     actor/session (to set up foreign or own claims), set the gate (argv, or a malformed
     value on the old side), add a known red, and make a guard refuse `done` after the
     merge (old side: what the old pm's deploy close-check does -- read the old pm to
     find how a throwaway repo provokes it; new side: a `pre-done` file in the private
     `PM_PLUGINS`). Implement every method now, both sides, even those only later parts
     use; a method you cannot implement on one side raises with a clear message and is
     listed in NOT DONE.
   - **`AdapterTest`**: a few tests that exercise the adapter alone, no wt, so the `new`
     side is proven before any new wt exists (make store, file, take, read status and
     holder, set gate, add known red).
   - **`StartTest`**: from the contract -- claim and add the worktree at
     `<repo>/.worktrees/<id>` on branch `<id>`; resume an existing worktree; adopt your
     own claim (the `adopting existing claim` line; same actor and same session token);
     refuse a foreign claim (different token, different actor, bare-name claim) with the
     `is not claimable` line; `--force` and its park-not-finish reminder; `--as` defaulting
     to `$WT_ACTOR`; refusing to resume a branch whose tip is a mass-deleting
     `WIP: park` commit; anything else in the contract about `start`.
   Each test's docstring quotes the contract phrase it pins, so a reviewer can map suite
   to contract line by line. Assert exit codes and the first words of wt's own `OK:`,
   `wt:` and `STOP.` lines (up to their first variable part, plus the ticket id), never
   text that pm prints. Tests for later verbs come in parts 2 to 4; leave clearly named
   room for `FinishTest`, `ParkTest`, `StatusPruneTest`, `ResolutionTest`.
3. **`WT/docs/uncovered.md`** -- only if a contract case of `start` cannot run in the
   sandbox: the case, why, and the exact operator-terminal command that covers it. Do
   not fake such a case.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old
```

must exit 0 with `failed 0, pending 0` and no skips except ones you justify in the report.
Also run it with `--pm new --allow-pending -k AdapterTest`: the adapter tests must pass
on the new side. Both runs' last two lines go in EVIDENCE verbatim.

If the old wt does something the contract says it should not, or a contract line is
ambiguous: do not encode a guess. Pin what the old wt does, name the test and the
contract line in NOT DONE, and keep going.

## Stop and report

Commit on branch `fc-30c060` with explicit `git -C <worktree> add <paths>`; the
message ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write
your report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/00-characterize-1-start.md`
(the main checkout, not the worktree; do not commit it) in the worker-brief shape, and
print only that path.
