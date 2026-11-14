# pm-wt-rewrite/02/01a wt core: dispatcher and lib fc-262fa8:fc-122c0d

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/01a-core.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/01a wt core: dispatcher and lib fc-262fa8:fc-122c0d

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/01a-core.md`

You are a worker on ticket fc-122c0d, part 1 of 2. You start with zero context. Your
worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d` on branch
`fc-122c0d`; the overseer created it. `WT/` is that worktree's `wt/`.

## Binding rules

`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md` binds you:
read it first. Never run `wt` (the installed one is the old tool that runs this epic),
never mutate tickets with `pm ticket`, never merge. Stop at 80k tokens or 40 tool calls,
commit what is green, report the rest under NOT DONE. Read-only: everything under
`~/frontier`, `~/.local`, `~/.config/pm`, provider config dirs, this repo's `pm/`, and
**`WT/tests/test_wt_cli.py` and `WT/tests/run_wt.py`** (accepted; a test that looks wrong
is reported in NOT DONE, never edited). The code under `wt/` is never put on `PATH`.

## Read

1. `pm ticket show fc-122c0d` -- the spec. Where it and the rulings below differ, the
   rulings win.
2. `/Users/matthias/projects/frontier-clean/docs/component-principles.md` -- the code
   standard; and `WT/AGENTS.md`.
3. `WT/docs/contract.md` -- the behavior to keep.
4. `WT/tests/test_wt_cli.py` -- the accepted black-box suite (125 tests). It is the
   gate for the verbs; read how it sets up env (`WtCase.setUp`), which variables wt
   must honor, and the exact first words it pins for failure lines.
5. `/Users/matthias/projects/frontier-clean/pm/docs/design.md`, sections "Identity",
   "Verbs" and "Plugins"; and `pm/cli/pm` (the dispatcher pattern to mirror in zsh).
6. Old source, read-only: `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`
   (`run`, `git`, `pm`, `repo_root`, `resolve_target_repo`, `default_branch`,
   `worktree_path`, `branch_exists`, `list_worktrees`, `_guard`, `_fixed_line`,
   `_fail`, `resolve_store_repo`, `read_gate`, `read_findings_required`,
   `read_known_red`), `src/faultreport.py`, `src/crossrepo.py`.

## Overseer rulings (binding)

- **Fault dir variable** is `WT_FAULT_REPORT_DIR` (not `WT_FAULT_DIR`), default
  `/Users/matthias/frontier/docs/backlog/inbox/infra-faults`, rows in the old file shape:
  one file per root cause and day, one row appended per occurrence (port
  `faultreport.append`; markdown, no JSON).
- **Cross-repo guard.** The pairs file `$GIT_PAIRS_FILE` (default
  `~/.claude/git-pairs.json`, old shape `{"pairs":[{"source","targets","git"}]}`) is
  JSON, and zsh never parses JSON (principle 3). The check is a stdlib Python helper,
  `WT/tools/lib/crossrepo.py`, run with `/usr/bin/python3 -B`, that ports
  `crossrepo.refuse` (same-repository mapping through linked worktrees, per-subcommand
  `git` list, fail-closed on a missing or unreadable file); it prints the refusal reason
  and exits 1, or exits 0. `fail.zsh` calls it and owns the refusal line.
- **The new side's gate label** is the literal `.wt/gate`; a `.wt/gate` that exists and
  is not executable refuses with a `wt:` line that contains `gate` and
  `fix it or pass --no-gate.` (the suite pins this).
- **Status words.** pm prints `open taken parked done`; wt compares those.
- Teardown helpers (keep entry, deferred-teardown detection and line, the `STOP.` line
  and per-shape cleanup steps, undeletable-path refusal, merged marker) are part 2,
  `WT/tools/lib/teardown.zsh`. Do not write them here.

## Deliver

- **`WT/cli/wt`** (zsh, executable): resolve its own path through symlinks; the verb
  table `start finish land park status prune selftest` (`land` is its own entry that
  the finish file serves; decide whether `land` gets a `land.zsh` that sources
  `finish.zsh` or the dispatcher maps it -- say which in the report); source
  `WT/tools/lib/*.zsh` it needs and run `WT/tools/verbs/<verb>.zsh`. A verb with no file
  appends its name to `$WT_UNBUILT_LOG` when set, prints `wt: '<verb>' is not built yet`
  to stderr and exits 70. No verb or an unknown one: one usage line naming the verbs,
  exit 2. `wt pending` is not in the table (dropped for `pm ls parked`): it gets the
  unknown-verb answer plus a hint to run `pm ls parked`.
- **`WT/tools/lib/git.zsh`**: repo root of a path, the main checkout of a linked
  worktree, default branch, worktree path for an id, branch exists, worktree list
  (porcelain parsed in zsh, no JSON), is-ancestor.
- **`WT/tools/lib/pm.zsh`**: `get`, `take`, `done`, `park`, `drop`, `emit` through `pm`
  on `PATH`, each with `WT_CALLER=1` exported for that call; the store of a ticket
  (`pm get <id> store`; a ticket pm cannot find falls back to the cwd repo, as the old
  wt did for an unregistered prefix), and `--store`/`--repo` resolution as the old
  `resolve_store_repo`/`resolve_target_repo` do; `--session X` reaches pm as
  `PM_SESSION_ID=X` for that call.
- **`WT/tools/lib/fail.zsh`**: the one fixed failure line (`wt: <what>. <next step>`,
  with `(reported: <path>)` for non-infra rows and `Recorded in <path>. This is
  infrastructure, not a finding` for infra rows, as the old `_fail` words them), the
  fault-row writer, and the cross-repo refusal calling `crossrepo.py`.
- **`WT/tools/lib/config.zsh`**: find and validate `.wt/gate` in the store repo, read
  `.wt/known-red` (`<ticket id> <text>` per line; blank lines and `#` lines skipped),
  read `findings_required` from the store's `.pm/config.json` without parsing JSON in
  zsh: a small stdlib helper file beside `crossrepo.py` (no `python3 -c` strings in
  zsh). Do not use `pm done --dry-run` as the findings check: it also runs every
  `pre-done` plugin, so a guard meant to refuse after the merge would refuse before
  it, and the suite pins the merge landing first
  (`test_refusal_after_merge_leaves_ticket_taken`).
- **`WT/tools/lib/crossrepo.py`** as ruled above.

Rules: `emulate -L zsh` in every function, quoted paths, explicit `return`s, no
`git branch -D`, no `git worktree remove --force`, no `rm -rf`. Comments only for
constraints the code cannot show; no ticket ids in code. Each lib function has exactly
the callers the contract implies (three verbs or more); if one would have fewer, leave
it to its verb and say so.

## Gate

```sh
/bin/zsh -n /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/cli/wt
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.worktrees/fc-122c0d/wt/cli/wt --pm new --allow-pending
```

`zsh -n` on every `.zsh` file you wrote, one call each: exit 0. The suite: exit 0, with
`failed 0` (every wt test pending, two skips). Also prove by hand, with throwaway calls
under the worktree's `.tmp/` (never a real repo): `wt/cli/wt` with no args exits 2;
`wt/cli/wt pending` exits 2 and names `pm ls parked`; `WT_UNBUILT_LOG=<file> wt/cli/wt
start x` exits 70 and appends `start`; `crossrepo.py` refuses an undeclared pair and
allows a declared one (two cases, a pairs file you write under `.tmp/`). Paste each
command and its result in EVIDENCE.

## Stop and report

Commit on branch `fc-122c0d` with explicit `git -C <worktree> add <paths>`; the message
ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Write the report to
`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01a-core.md`
(main checkout; do not commit it) in the worker-brief shape, and print only that path.
List every lib function you wrote, one line each with its intended callers, under DID or
ARTIFACTS so the next workers can use them.
