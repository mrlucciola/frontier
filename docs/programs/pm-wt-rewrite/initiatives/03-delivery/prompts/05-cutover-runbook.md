# pm-wt-rewrite/03/05 cutover runbook, written and run by nobody here fc-ccecda:fc-10981e

```
cd ~/projects/frontier-clean/.worktrees/fc-10981e && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/05-cutover-runbook.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
the fc-10981e worktree; nothing to paste. In-session, the overseer dispatches it as a
subagent by path, once per part, and names the part in the dispatch.

---

# pm-wt-rewrite/03/05 cutover runbook, written and run by nobody here fc-ccecda:fc-10981e

`docs/programs/pm-wt-rewrite/initiatives/03-delivery/prompts/05-cutover-runbook.md`

You are a worker for ticket **fc-10981e** (epic fc-ccecda). You start with zero
context. The worker brief binds you and is not restated here:
`/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`.
Read it first.

The runbook is written in two parts, by two workers in turn, in the same worktree.
Your dispatch names your part. Do only that part. If you are Part B, Part A's text is
already committed on the branch; read it and append, do not rewrite it.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-10981e`, branch
  `fc-10981e`. The overseer created it. Every edit is under it; every git command is
  `git -C <that path> ...`. You never run `wt`, never merge, never run
  `pm ticket close|note|claim`.
- Write set: `docs/programs/pm-wt-rewrite/CUTOVER.md`, and one link to it from
  `docs/programs/pm-wt-rewrite/PLAN.md` "Cutover" (Part A only). Nothing else.
- **Nothing in the runbook is run by you.** You read the files the steps change, so
  that each step names real coordinates, and you may run read-only commands
  (`rg`, `ls`, `wc`, `git --no-pager -C ... log/show`, `--help`, `--dry-run` where
  the tool has one and it writes nothing). You never run `pm import`, `ln`,
  `bin/deploy` (not even `--dry-run`: it writes its registry), and you never write
  under `~/frontier`, `~/.claude`, `~/.codex`, `~/.config`, `~/.local`.

## The spec

`pm ticket show fc-10981e --all-notes` is the spec: ten numbered steps in the body,
and six notes that each add a requirement. Read every note; each one must show up in
the runbook as a step, a decision the operator makes (with the options and your
recommendation), or a trigger.

### The shape

Every step follows "Handed-off actions" in
`/Users/matthias/frontier/references/protocols/handoff-contract/README.md` (read it;
your global instructions carry the same rules): one numbered step per physical
action, a short imperative title, one line on what it buys, then ONE fenced block
holding the commands that make the change and prove it, with at most one `#` line
above a non-obvious command. A file edit gives the command that opens it, then
`replace these lines:` / `with this:` blocks quoting the current text at its line
range. Every step names which repo a commit lands in. Never guess a coordinate:
write "I have not opened X" where that is true.

Open the runbook with: what must be true first (triggers: fc-ccecda's tickets closed;
fr-453840 landed, from the session-cost note; anything else you find), the before
and after numbers from `pm/docs/cost.md` (cite, do not re-measure), and the
rollback summary.

### Facts already established (verify each before you rely on it)

- The new pm's registry is `~/.config/pm/stores`, or the file in `$PM_STORES`
  (`pm/docs/design.md` "Ids and the registry"). The old registry is
  `~/frontier/runtime-tools/pm/stores.json`. The ticket body and one note disagree on
  the new file's name; the design wins.
- Install steps already written: `pm/INSTALL.md` (install, plugins, harness hooks for
  Claude Code, opencode, and Codex) and `wt/INSTALL.md`. Cite them by section; do not
  restate them, except where the runbook must order them.
- Claude hook registration lives in `~/.claude/settings.json`, which is generated from
  `~/frontier/config/claude/` by the `config-claude` package. That deploy is
  operator-run: the runbook gives the source edit in `~/frontier/config/claude/`, then
  `python3 /Users/matthias/frontier/bin/deploy deploy config-claude --provider claude --dry-run`
  for review and the same line without `--dry-run` for the operator.
- Content-plane deploys (skills, hooks, tools): `python3 /Users/matthias/frontier/bin/deploy deploy <package> --provider <provider>`
  then `verify`. Retiring a package is a frontier change; find how frontier retires
  one (`rg -n 'retire' /Users/matthias/frontier/bin /Users/matthias/frontier/deploy`)
  and use that, rather than inventing deletions.
- The measured cost baseline and the stale deployed worktree-lifecycle skill:
  `pm/docs/cost.md`.

## Part A: switching over (steps 1-6 and 10)

Freeze, import every store and prove it, the registry, the symlinks and plugin links,
the config-key moves, harness registration for Claude Code, opencode and Codex (from
`pm/INSTALL.md`; for Codex, its "Probe" section comes first and its result gates
"Register": the runbook says what to do if the probe disproves a claim), the two
frontier-coupled wt defaults and the old refusal texts as
operator decisions, and rollback. For step 2, list every store in
`~/frontier/runtime-tools/pm/stores.json` by name and path, and give the
`pm/tests/import_check.py` command that proves the imports. For step 5, list which
stores set `gate` or `known_red` today, with the value, read from each store's
`.pm/config.json`.

## Part B: retiring the frontier side (steps 7-9)

Step 7: the deploy close-check as a pre-done plugin owned by frontier: find the
close-check in `~/frontier` (`rg -n 'close' /Users/matthias/frontier/deploy`), name
the plugin file, give its full text, and how it is linked into
`~/.config/pm/plugins/`. Step 8: re-run the inbound-reference searches and list every
hit as `file:line`. At least `rg -n 'runtime-tools/pm|runtime-tools/wt|skills/pm|worktree-lifecycle|pm-hooks|hooks/pm' /Users/matthias/frontier`,
and `rg -n "pm ticket|\bwt (start|finish|park|land|status|prune|pending)" /Users/matthias/frontier/hooks/core-hooks`.
Give each hit a line in the runbook: what it does today and the exact change. For each
core-hooks policy that matches `pm ticket` or `wt` command lines, also say what it must
match now: the new verbs are in `pm/cli/pm help` and `wt/cli/wt help`. The ledger's
starting list is in
`docs/programs/pm-wt-rewrite/initiatives/03-delivery/INITIATIVE.md` "Facts not to
re-derive". Step 9: the pm and wt parts of
`~/frontier/instructions/claude-global/CLAUDE.md` shrunk to pointers. Use
`wt/docs/instruction-map.md` to say which lines go and why, and give the replacement
text. The file is generated by `tools/gen_instructions.py` from a source; find the
source and edit that.

## Gate

```sh
python3 -B docs/check_structure.py
```

From the worktree root. Also a `.tmp/` python script that lists every `file:line`
coordinate in `CUTOVER.md` that points at a missing file or a line past its end.
Paste its output in EVIDENCE, and expect none. Do not commit the script.

## Budget and report

Stop at 80k tokens or 40 tool calls. If you get there, commit what is complete and
list the remaining steps in NOT DONE; the overseer re-dispatches them.

Commit on branch `fc-10981e` with explicit `git add` paths. The commit message ends
with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write your
report in the worker-brief shape to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-10981e/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/05-cutover-<a|b>.md`
(your part's letter), commit it on the same branch, and print only that path.
