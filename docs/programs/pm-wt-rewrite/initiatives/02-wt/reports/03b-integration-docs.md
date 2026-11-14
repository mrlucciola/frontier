TICKET: fc-8c1f62 -- wt integration: component docs and contract (part 2 of 2)
DID: rewrote wt/docs/contract.md (own reference, dropped/changed list, trimmed sandbox notes) and wrote wt/README.md, wt/INSTALL.md, wt/AGENTS.md
DID: deleted the wt A-RUN row from the exemptions table in docs/contributing.md
DID: wrote nothing outside those five files; no wt run, no pm ticket mutation
EVIDENCE:
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/docs/check_structure.py
  check_structure: ok (7 components, 3 exempted)   (exit 0)
rg -n 'frontier/|runtime-tools|fr-[0-9a-f]{6}|cl-[0-9a-f]{6}' <the four wt docs>
  no output (exit 1)
COMMITS: frontier-clean 5b2e29a on branch fc-8c1f62 (no check required; docs only)
NOT DONE:
- Test suites not run (docs-only prompt; gate was the two commands above).
- Unverified claims: contract.md says `start` takes `--session` and that the done-refusal line reads "<id> is already merged into <branch> but pm done failed (<reason>)"; taken from finish.zsh:400 and the old contract, not exercised. `OK: ... ticket closed` line text in the deferred-teardown bullet is kept from the old contract, not re-checked against test_wt_cli.py.
- Dropped from contract.md on purpose: "What the hooks deny" section, "wt is allow-listed", E2BIG deny-path budget, Codex profile/session-root detail, Layout and Cross-repo sections (frontier posture/deploy mechanics, Python module names), and the old `ticket NOT closed: deployed copy` output line (replaced by the generic pm-done-refused line). Overseer: confirm those drops.
- Finding: wt/tools/lib/fail.zsh:3 hardcodes a /Users/matthias/frontier/... default for WT_FAULT_DIR_DEFAULT; INSTALL.md says only "a built-in default". Needs a code ticket if the default should be frontier-free.
- Finding: wt/tools/lib/crossrepo.py defaults GIT_PAIRS_FILE to ~/.claude/git-pairs.json (documented in INSTALL.md).
- Finding: INSTALL.md instructs installing over the existing ~/.local/bin/wt; `ln -sfn` replaces the old deployment symlink. Cutover runbook should note the old link is overwritten.
BLOCKED ON OPERATOR: NONE
ARTIFACTS:
/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/README.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/AGENTS.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/INSTALL.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/docs/contract.md
/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/docs/contributing.md
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/03b-integration-docs.md
