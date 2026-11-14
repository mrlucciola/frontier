# pm-wt-rewrite/04/01a pm log core: quarantine the port to pm/v2 fc-2a6562:fc-dac416

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-a-move.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/01a pm log core: quarantine the port to pm/v2 fc-2a6562:fc-dac416

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-a-move.md`

Ticket **fc-dac416**, first of four serial workers on its branch. You move the ported
pm out of the way so the new pm is born at its final paths, and fix the routing
documents. You write no new pm code. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416`.

## Read first

`pm/docs/design.md` sections "Why" and "Source tree"; `docs/contributing.md` (what a
component's README, AGENTS and INSTALL must hold); the current `pm/README.md`,
`pm/AGENTS.md`, `pm/INSTALL.md`; `docs/programs/pm-wt-rewrite/PLAN.md` "Run 04".

## Deliver

1. With `git -C <worktree> mv`, move each of these to the same path under `pm/v2/`,
   and change nothing inside them: `pm/cli`, `pm/tools`, `pm/docs/cut-list.md`,
   `pm/docs/spec`, and from `pm/tests` exactly `run_parity.py`, `test_cli_parity.py`,
   `test_cli_contract.py`, `test_gitcommit.py`, `test_views.py`, `golden_diff.py`.
   Leave `pm/tests/run_transcripts.py`, `pm/tests/t/`, `pm/tests/fixtures/`,
   `pm/docs/design.md` and the untracked `pm/dash-ui/` where they are. One commit,
   moves only, so `git log --follow` keeps history.
2. Only if `docs/check_structure.py` flags a link inside a moved markdown file: change
   that link's target to the moved path. Nothing else in a moved file changes.
3. Rewrite `pm/README.md`, `pm/AGENTS.md` and `pm/INSTALL.md` for the new layout:
   - README: pm is being rebuilt as the event-log pm of `pm/docs/design.md`; the
     installed `pm` stays the frontier one until the operator's cutover; `pm/v2/` holds
     the ported pm, kept for reference until this epic's last ticket deletes it, and is
     not run. Routes table: the design, the transcripts, maintenance, setup, and the
     port under `pm/v2/` (its cut list and spec v2, which import reads).
   - AGENTS: build to `pm/docs/design.md` and `docs/component-principles.md`; the
     gate is the transcripts, run as
     `/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending` from the
     repository root; the pending rule in two sentences; never edit the design,
     `tests/t/` or `tests/fixtures/`, report what looks wrong; `pm/v2/` is read-only
     reference. Drop every instruction about the parity suite, `tools/ticket`,
     `routing.py` and `gitcommit.py` as current practice.
   - INSTALL: the new pm is not ready to install; until cutover the install is the
     frontier one. Keep the side-install link (`pm-next`) steps, verification that
     works on today's code after the remaining workers land (`pm-next help` prints the
     verb list), disable and remove. Every command runnable as written.
4. Fix any other in-repo reference that `check_structure.py` reports as broken by the
   move. Do not edit files outside `pm/` except to fix such a reference.

## Gate

Run from the worktree root:

```sh
python3 -B docs/check_structure.py
```

It must report no violation in `pm/`. A violation elsewhere that also exists at the
branch's base commit is not yours: list its text in NOT DONE. `pm/cli/pm` does not
exist after your move, so do not run the transcripts.

## Report

Commit messages `pm log core: move the port to pm/v2` (the moves) and
`pm log core: routing documents for the new layout` (the docs). Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/01-core-a-move.md`.
