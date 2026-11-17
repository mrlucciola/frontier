# Instruction map

Where each line of the retired `worktree-lifecycle` skill and of wt's part of the global
instructions went. No skill is shipped for wt or pm: the guidance is what `wt help`,
`wt help <verb>` and wt's own output lines print, plus [the contract](/wt/docs/contract.md)
for what an agent reads once.

Sources, as read on 2026-11-14:

- `SKILL`: `/Users/matthias/frontier/skills/worktree-lifecycle/SKILL.md`, lines 1-120.
- `CLAUDE`: `/Users/matthias/frontier/instructions/claude-global/CLAUDE.md`, the "Worktrees
  and tickets" block (lines 142-145) and the section "Branches and worktrees (shared
  checkouts)" (lines 160-170).
- `OLD`: the old contract's environment sections, `git show 61b8f1d:wt/docs/contract.md`
  in frontier-clean.

Every row ends in exactly one disposition. `printed` names the file and line that print
it at the moment it applies (paths are under `wt/`). `contract` names the section of
`wt/docs/contract.md` that keeps it. `dropped` gives the reason. Cutting the global
instructions down to match is a change in `~/frontier/instructions/claude-global/`, outside
this repository; until it lands those lines stay in force and this map is what justifies
the cut.

## Skill

| Src | Lines | Says | Disposition | Where or why |
| --- | --- | --- | --- | --- |
| SKILL | 1-15 | front matter, trigger description | dropped | no skill is shipped; `wt help` is the entry point |
| SKILL | 16-20 | title; pointer to the instructions and the old README | dropped | the pointers target the skill and the retired README |
| SKILL | 21-25 | every worktree enters by start, leaves by finish or park; no-ticket worktree is an orphan | printed | cli/wt:24-26 (help header); tools/verbs/status.zsh:3 (orphan) |
| SKILL | 26-27 | heading: rules wt does not enforce | dropped | heading |
| SKILL | 28 | main checkout stays on its default branch | contract | "Rules wt does not enforce", first bullet |
| SKILL | 29-31 | one ticket, one worktree, one branch, never under `.tmp/` etc.; start before first edit; edit only under it | printed | tools/verbs/start.zsh:5-6 and :152 (edit only under it); the forbidden parents are in the contract, "Rules wt does not enforce", second bullet |
| SKILL | 32-34 | run wt from the main checkout; only the orchestrator runs wt | printed | cli/wt:25 (main checkout); orchestrator rule in the contract, "Rules wt does not enforce", third bullet |
| SKILL | 35-38 | `git -C`, explicit paths; branch check before commit; stop if main is off its default branch | printed | tools/verbs/start.zsh:152 (`git -C`, explicit paths); the branch check is in the contract, "Rules wt does not enforce", first bullet |
| SKILL | 39-42 | tickets live in `.pm/`; `pm ticket init`; the store is found by prefix, `--store`/`--repo` rarely | contract | "Verbs", the paragraph on `--store` and `--repo`; `pm init <prefix>` is in `pm help` (pm/cli/pm:35) |
| SKILL | 43-44 | a force-claimed ticket ends in park, never finish | printed | tools/verbs/start.zsh:7 (help) and :102 (the line printed on a forced claim) |
| SKILL | 45-48 | never `rm -r` a worktree, force-remove, switch or stash in main, `git add -A`, `branch -D` without the cherry check; hooks deny | printed | cli/wt:26 (never rm, switch or force-remove by hand); the cherry rule, `git add -A` and stash in the contract, "Rules wt does not enforce", fourth and fifth bullets; the hook denials are dropped, see OLD "What the hooks deny" |
| SKILL | 49-50 | built-in Claude worktrees are for throwaway work | contract | "Rules wt does not enforce", Claude Code's built-in worktrees |
| SKILL | 51-53 | blank; heading: which verb when | dropped | heading |
| SKILL | 54-55 | table header | dropped | table markup |
| SKILL | 56-57 | start, and the same verb resumes a parked ticket | printed | cli/wt:11; tools/verbs/start.zsh:3-4 |
| SKILL | 58 | finish after committed work; `--note`, `--findings`, gate, `--no-gate` | printed | cli/wt:12; tools/verbs/finish.zsh:1-5 |
| SKILL | 59 | land: merge now, ticket stays taken, start again to continue | printed | cli/wt:13; tools/verbs/finish.zsh:2 and :7-8 |
| SKILL | 60 | park when work must wait, with `--waits-on` | printed | cli/wt:14; tools/verbs/park.zsh:1 and :4-5 |
| SKILL | 61 | status | printed | cli/wt:15; tools/verbs/status.zsh:2 |
| SKILL | 62 | pending | dropped | `wt pending` is gone; parked tickets are `pm ls parked` (tools/verbs/status.zsh:3-4; cli/wt:77-78 answers `wt pending`) |
| SKILL | 63-64 | selftest; blank | printed | cli/wt:17; tools/verbs/selftest.zsh:2 |
| SKILL | 65-66 | `--as` defaults to `$WT_ACTOR` | printed | tools/verbs/start.zsh:4 |
| SKILL | 67-68 | heading: what each verb does | dropped | heading |
| SKILL | 69-70 | start claims or adopts, adds the worktree, resumes a parked branch rebased | printed | tools/verbs/start.zsh:2-4 |
| SKILL | 71-73 | finish: gate, rebase, ff-only merge, remove, close; list SKIP lines under NOT PROVEN | printed | tools/verbs/finish.zsh:3-5 |
| SKILL | 74-75 | park: commit WIP, remove worktree, keep branch; `.local/` blocks | printed | tools/verbs/park.zsh:3-4 and :8 |
| SKILL | 76 | status: live worktrees joined to tickets; FOREIGN/ORPHAN never touched | printed | tools/verbs/status.zsh:2-3; tools/verbs/status.zsh:43 prints the FOREIGN/ORPHAN label |
| SKILL | 77 | pending | dropped | `wt pending` is gone, see line 62 |
| SKILL | 78-79 | prune clears deferred-teardown registrations | printed | tools/verbs/prune.zsh:1-3 |
| SKILL | 80-81 | heading: reading wt output | dropped | heading |
| SKILL | 82 | `OK:` is success | contract | "Reading wt output", first bullet |
| SKILL | 83-84 | `wt:` is a failure naming the next step; `(reported: path)` means no ticket | printed | tools/lib/fail.zsh:55-62 (the line says so itself: "file no ticket", "reported") |
| SKILL | 85-86 | finish auto-parks on conflict or exhausted ff-only; resume with start | printed | tools/verbs/finish.zsh:6 (help); tools/verbs/park.zsh:161 (note on the ticket) |
| SKILL | 87-88 | after a park the directory is gone by design; status will not list it | printed | tools/verbs/park.zsh:6-7 |
| SKILL | 89 | not claimable: pick other work, never retry | printed | tools/verbs/start.zsh:89 and :97 (the line); :6 (help) |
| SKILL | 90-93 | deferred-teardown line is a success; run `wt prune`; hand the operator the prune line; never prune by hand | printed | tools/lib/teardown.zsh:128 (the line); tools/verbs/prune.zsh:2-3; tools/lib/teardown.zsh:256 (the operator line) |
| SKILL | 94-95 | heading: scratch and local state | dropped | heading |
| SKILL | 96 | `.tmp/` is scratch; never `rm` it | contract | "Rules wt does not enforce", scratch bullet |
| SKILL | 97-98 | `.local/` is durable; never delete, move or `git clean` it | printed | tools/verbs/park.zsh:8 (help) and :91 (refusal); the rest in the contract, same bullet |
| SKILL | 99-100 | a fresh worktree has no installs or env; never copy secrets in | contract | "Rules wt does not enforce", scratch bullet |
| SKILL | 101-103 | gitignore `.tmp/`, `.local/`, `.wt/`; heading: provider notes | contract | "Rules wt does not enforce", scratch bullet |
| SKILL | 104-105 | Claude block markers | dropped | markup |
| SKILL | 106 | wt is allow-listed; stay rooted in the main checkout | contract | "Sandbox notes", Claude, first bullet and "Stay rooted" bullet |
| SKILL | 107-108 | each worktree adds deny paths; budget a restart (E2BIG) | contract | "Sandbox notes", Claude, first bullet |
| SKILL | 109-110 | EPERM on the admin dir is the deferred teardown; a tracked `.vscode/` breaks add and remove | printed | tools/lib/teardown.zsh:128 (deferred line); tools/verbs/start.zsh:120 (add-failure hint); tools/lib/teardown.zsh:187 (`.vscode` refusal) |
| SKILL | 111-112 | block end and Codex block marker | dropped | markup |
| SKILL | 113-114 | Codex needs the maintainer profile; stop and report; never escalate | contract | "Sandbox notes", Codex, profile bullet and the no-escalation bullet |
| SKILL | 115-117 | launch at the main checkout; a teardown `Operation not permitted` is a posture regression | contract | "Sandbox notes", Codex, launch and `failed to delete` bullets |
| SKILL | 118-120 | start as `--as codex`; session from `$PM_SESSION_ID` or `$CODEX_THREAD_ID`, else `--session` | contract | "Sandbox notes", Codex, start-as-codex bullet; `wt help start` prints `--as` and `--session` |

## Global instructions

| Src | Lines | Says | Disposition | Where or why |
| --- | --- | --- | --- | --- |
| CLAUDE | 142 | block title "Worktrees and tickets" | dropped | heading |
| CLAUDE | 143 | tickets are `pm ticket <verb>`, bare `pm` | dropped | the command is `pm <verb>` now (`pm help`); pm's recipe, not wt's |
| CLAUDE | 144-145 | a ticket in another repo's store: no flag, the prefix routes; `--store` and `--repo` only when needed | contract | "Verbs", the paragraph on `--store` and `--repo` |
| CLAUDE | 160-161 | section title; main checkout stays on its default branch, branch check before every commit | contract | "Rules wt does not enforce", first bullet; cli/wt:25 prints "from the main checkout" |
| CLAUDE | 162 | main checkout stays on its default branch, stop and report | contract | "Rules wt does not enforce", first bullet |
| CLAUDE | 163 | one worktree per ticket, enter and leave only through wt, the three verbs, park removes the directory, `wt pending`, start before the first edit, never stash, never work a ticket you do not hold | printed | cli/wt:24-26 and :11-14 (rule and verbs); tools/verbs/park.zsh:6-7 (directory gone); tools/verbs/start.zsh:5-6 and :152 (edit only under it); tools/verbs/start.zsh:89 (not held, refused); `wt pending` dropped, see SKILL 62; stash in the contract, "Rules wt does not enforce", fourth bullet |
| CLAUDE | 164 | tickets in `.pm/`; pm skill has the verbs; init before the first worktree; finish, park or release every held ticket before the final response; Stop hook | printed | tools/verbs/start.zsh:152 (end with finish or park); the final-response rule in the contract, "Rules wt does not enforce"; the skill pointer and `pm ticket init` are dropped (no skill; `pm help init`); the Stop hook is dropped (the hook prints its own reminder) |
| CLAUDE | 165 | stage explicit paths only; only the orchestrator runs wt | printed | tools/verbs/start.zsh:152 (explicit paths); orchestrator rule in the contract, "Rules wt does not enforce", third bullet |
| CLAUDE | 166 | teardown is finish or park only; never rm -rf, force-remove, `branch -D` without the cherry check, escalate, ask for an allow rule; prune clears a deferred teardown; never prune or `branch -d` by hand; index.lock | printed | cli/wt:26; tools/lib/teardown.zsh:116 (STOP line: do not escalate); tools/verbs/prune.zsh:2-3; tools/verbs/finish.zsh:8 (index.lock); cherry rule in the contract, "Rules wt does not enforce", fifth bullet; allow rule in the contract, "Sandbox notes", Codex |
| CLAUDE | 167 | when blocked: one plain line plus commands to the operator; the fault is recorded once; no per-incident ticket | printed | tools/lib/fail.zsh:55-62 (recorded, no ticket); tools/lib/teardown.zsh:116 (hand the operator this cleanup) |
| CLAUDE | 168 | a worktree with no ticket is an orphan: report it, never remove it | printed | tools/verbs/status.zsh:3 and :43 |
| CLAUDE | 169-170 | pointer to the skill for verbs, output lines, sandbox notes | dropped | no skill; `wt help` and the contract replace it |

## Old contract environment sections

Source `OLD` (`61b8f1d:wt/docs/contract.md`). The ticket's note lists these as dropped
from the rewritten contract on purpose; each is accounted for here.

| Section | Says | Disposition | Where or why |
| --- | --- | --- | --- |
| What the hooks deny | `rm -r` of `.wt`, `branch -D` without the cherry check, `worktree remove --force`, `git switch`/`stash`/`add -A` are denied or asked | dropped | the hooks print their own denial with a remedy (`~/frontier/hooks/core-hooks`); wt prints the one-line form in cli/wt:26 and the contract keeps the rules, "Rules wt does not enforce" |
| wt is allow-listed | `wt *` runs with no prompt | contract | "Sandbox notes", Claude, first bullet |
| Deny-path budget (E2BIG) | about three deny paths per worktree; restart near 220 | contract | "Sandbox notes", Claude, first bullet |
| Linked-worktree admin dirs | `EPERM` on `rmdir` depends on when the sandbox was rebuilt; deferred teardown handles it | contract | "Sandbox notes", Claude, first bullet there; printed at tools/lib/teardown.zsh:128; the probe history and the deny-list numbers are dropped (measurements, not instructions) |
| `.vscode` segment deny | tracked `.vscode/*` breaks add and remove; `.claude/` leaves residue | contract | "Sandbox notes", Claude, `.vscode` bullet; printed at tools/lib/teardown.zsh:187 and tools/verbs/start.zsh:120 |
| `.git/config` and `.git/hooks` write-deny | `branch -d` prints a config error and still deletes; `git init` cannot run sandboxed | contract | "Sandbox notes", Claude, `.git/config` bullet; the `git init` clause is dropped: `wt selftest` handles its own scratch repo and prints its own failures |
| Stay rooted in the main checkout | no `cd`; `git -C .wt/<id>`; commits pass the git guard | contract | "Sandbox notes", Claude, last bullet; tools/verbs/start.zsh:152 prints `git -C` |
| Codex: profile | lifecycle needs the maintainer profile; under the floor stop and report | contract | "Sandbox notes", Codex, first bullet |
| Codex: session root | launch at the main checkout | contract | "Sandbox notes", Codex, second bullet |
| Codex: no escalation | the lifecycle works with no rule; never ask for an allow rule | contract | "Sandbox notes", Codex, no-escalation bullet |
| Codex: directory deletes | deny globs make `rmdir` fail; `failed to delete` means posture regressed | contract | "Sandbox notes", Codex, `failed to delete` bullet; the deny-glob measurements (codex-cli version, ticket ids) are dropped: they belong to the posture docs |
| Codex: store and session | start as `codex`; session from `$PM_SESSION_ID` or `$CODEX_THREAD_ID`, else `--session` | contract | "Sandbox notes", Codex, start-as-codex bullet; the same flags are in `wt help start` |
