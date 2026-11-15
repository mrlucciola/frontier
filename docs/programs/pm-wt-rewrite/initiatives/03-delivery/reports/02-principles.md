TICKET: fc-121923 -- Finalize component principles and the behavioral contract from the pm and wt builds
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-121923/docs/component-principles.md out of draft: ten rules with rule 1, 2, 5, 6, 9 and 10 amended, contribution standards linked, evidence table "Rulings and evidence" at the end
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-121923/README.md: one new contract bullet, "Output that teaches" (refusal names the next command, help short, no injected text outside a component's workspace)
DID: /Users/matthias/projects/frontier-clean/.worktrees/fc-121923/docs/contributing.md: two sentences under "Documentation and validation" (record departures from the principles in the component's AGENTS.md; name frozen-behavior tests in the route table with who may change them)
EVIDENCE:
$ python3 -B docs/check_structure.py
check_structure: ok (7 components, 3 exempted)
Rulings (rule, ruling, evidence):
- 1, kept + "never imports another verb": pm-e report (523ae74, 04-integration-e-review.md) "Rule 1" sound list; wt/tools/verbs/finish.zsh:171-176 runs park through the dispatcher
- 1 proposal (verb = verb + X may import), declined: lint and validate are gone (pm/docs/design.md:337); no file in pm/ or wt/ imports a verb (rg of verbs imports finds only pm/cli/pm:91 loader)
- 2, changed (identical-rule and one-family cases; two-verb helpers recorded in AGENTS.md): be4de0b 01-pm/reports/04-review.md store.py pairs; bd6a9c5 02-wt/reports/01-review.md finding 13; wt/AGENTS.md:33-38
- 2 proposal (identical rule), accepted: current pm store.backup_blob (pm/tools/verbs/doctor.py:73, restore.py:26), store.locate_dir (import.py:158, restore.py:20)
- 2 proposal (one family, wt finish/park), accepted: wt_findings_required (finish.zsh:194, park.zsh:100), wt_merged_route (finish.zsh:85, park.zsh:73), the other three in wt/tools/lib/teardown.zsh called from both verbs
- 3, kept: 02-wt 01-review "No JSON is parsed in zsh"; wt/tools/lib/findings_required.py, crossrepo.py
- 4, kept: imports in pm/tools, pm/cli, wt/tools/lib/*.py are stdlib only (rg "^(import|from) \w+")
- 5, changed (transcript before code; a review defect gets a transcript): pm/docs/design.md:1-5, pm/tests/t/, be4de0b review test_gitcommit.py:20,99,121 (private names), pm-e report untested cases pinned in pm/tests/t/25-review-edges.t; all four pm/tests/*.py are black-box (scripted check)
- 5 proposal (transcripts as the contract), folded into rule 5
- 6, kept; refusal sentence moved to the contract: pm-e orient.py:13 _rank, import.py:56 unused by=, refusals without next command park.py:28 hold.py:28 reopen.py:24
- 7, kept: rg for ticket ids over pm/ and wt/ source prints nothing; be4de0b review found ticket ids in pm/tools/ticket:49 and init.py:12 in the port
- 8, kept: pm/docs/design.md:330-346; wt/cli/wt:22
- 9, changed (plugins by file presence folded in): pm/docs/design.md:246-272; rg "\bwt\b|worktree" pm/tools pm/cli prints nothing; wt/pm-plugin/{orient,post-take,pre-done}; wt/tools/lib/pm.zsh:7
- 9 proposal (plugins by file presence), folded into rule 9
- 10, changed (byte ceilings): pm-e replay O(n^2) "measure before claiming"; pm/tests/test_budgets.py:16; pm/docs/design.md:234-244
- 10 proposal (size budgets as tests), folded into rule 10
Contract and contributing additions, with gap evidence:
- Contract "Output that teaches": pm/docs/design.md:15-20 and :222-224; wt/docs/contract.md:86 and :146; both builds shipped pinned refusals with no next command (be4de0b review "Inherited"; pm-e done.py:43 list), so the rule had no owner
- Contributing "record departures": wt review finding 13 ("the ruling is not recorded in the component docs"); recorded at wt/AGENTS.md:33-38
- Contributing "name frozen tests": pm/AGENTS.md route row 2 and wt/AGENTS.md route row 3 each invented it
COMMITS: /Users/matthias/projects/frontier-clean/.worktrees/fc-121923 39a2e45 (docs); report commit follows on the same branch (tip SHA: git -C /Users/matthias/projects/frontier-clean/.worktrees/fc-121923 rev-parse --short HEAD)
NOT DONE:
- The rule 2 record requirement makes pm non-conforming, code untouched: pm/AGENTS.md records no two-verb helper. Add a "Recorded exceptions" paragraph naming store.backup_blob (doctor, restore) and store.locate_dir (import, restore), as wt/AGENTS.md:33-38 does. I have not opened store.py to check whether next_id, home, locate and now (one outside caller each in the scripted count: new.py, new.py, doctor.py, new.py) are used inside store.py; if not, rule 2 says they belong in their verb.
- wt has no byte ceiling on help or refusals (rule 10 now asks for one); I did not check whether the wt help ticket (prompt 01) added one.
- Rule 1's "no import" sentence rests on pm's lint/validate being gone; the ruling does not cover Python plugins in pm/plugins (pilot.py is imported by its own plugin files only, not checked).
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-121923/docs/component-principles.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-121923/README.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-121923/docs/contributing.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-121923/docs/programs/pm-wt-rewrite/initiatives/03-delivery/reports/02-principles.md
