VERDICT: PARTIAL (no code/test/schema hit; 4 LIVE doc lines in pm/README.md and pm/AGENTS.md would mislead once pm/v2 is gone, and must be edited in the same step)
FINDINGS:
/Users/matthias/projects/frontier-clean/pm/README.md:9 [LIVE] `pm/v2/` holds the ported pm, kept for reference until this epic's last ticket deletes (line continues; paragraph needs rewording)
/Users/matthias/projects/frontier-clean/pm/README.md:20 [LIVE] | [Cut list of the port](/pm/v2/docs/cut-list.md) | Deciding whether a verb, flag or config key of the old store belongs | (dead link; docs/check_structure.py may flag it)
/Users/matthias/projects/frontier-clean/pm/README.md:21 [LIVE] | [Store format, spec v2](/pm/v2/docs/spec/v2/SPEC.md) | Reading the old `.pm/` format, as import does | (dead link)
/Users/matthias/projects/frontier-clean/pm/AGENTS.md:24 [LIVE] | The ported pm in `pm/v2/` | Read-only reference; do not edit or run it |
/Users/matthias/projects/frontier-clean/.gitignore:128 [OTHER] `# spec/v2/SPEC.md section 1).` Comment only (a citation of spec v2), no path or rule breaks. It is a stale citation after deletion, so consider rewording.
/Users/matthias/projects/frontier-clean/pm/docs/design.md:4 [OTHER] "for the pm that replaces the ported one." Prose "ported"; no path reference.
/Users/matthias/projects/frontier-clean/pm/docs/design.md:170 [OTHER] "`find_duplicates` from the ported `create.py`, unchanged." Mentions the port without a path. It is a design note, and the port source is gone after deletion.
/Users/matthias/projects/frontier-clean/pm/docs/design.md:361 [OTHER] "Keep spec v2 and the ported code: carries the rewrite-and-commit machinery forever." Rejected-alternative prose, no path.
/Users/matthias/projects/frontier-clean/pm/tools/verbs/new.py [OTHER] No mention of the port, `copied` or `v2` anywhere in the file. It has only the imports at lines 7-14, so nothing to classify or change there.
/Users/matthias/projects/frontier-clean/pm/tests/t/19-import.t:3 [OTHER] `cp "$FIXTURES"/v2/* .pm/ && pm import`. This uses pm/tests/fixtures/v2/, a different directory that is not under pm/v2/ and is unaffected.
/Users/matthias/projects/frontier-clean/pm/INSTALL.md:6,23,28,54,85,110,123,145 [OTHER] `pm/cli/pm` is the NEW dispatcher path, not pm/v2/cli/pm. Unaffected.
/Users/matthias/projects/frontier-clean/pm/config/claude/hooks.json:8,18,28 [OTHER] `pm/cli/pm hook ...` is the new path, unaffected.
/Users/matthias/projects/frontier-clean/pm/tests/run_transcripts.py:4,155 [OTHER] `pm/cli/pm` is the new path, unaffected.
/Users/matthias/projects/frontier-clean/cwf/schemas/config.schema.json:3 and /Users/matthias/projects/frontier-clean/cwf/MANIFEST.json:53 [OTHER] Unrelated cwf schema of the same name.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/03-delivery/INITIATIVE.md:53 [OTHER] `deploy/gitcommit.py` is a different file, not the pm port's gitcommit.py.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/PLAN.md:83,84,97 [HISTORY] Plan: the first ticket moves the port to pm/v2, the last deletes it, and fc-d6c61c removes it.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/INITIATIVE.md:12,21,36,104,116,126 [HISTORY] Ledger mentions of pm/v2, `pm/v2/tools/verbs/create.py`, and the routing.py/gitcommit.py/ticket line counts.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/seed.md:47,57,84 [HISTORY] Seed text.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/01-core-a-move.md:7,18 [HISTORY] Move report.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-a-move.md:1,13,32-35,43,46,51-53,75 [HISTORY] Prompt: the move and the names of the tests that were moved.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-b-dispatcher.md:18,29 [HISTORY] Prompt.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-c-store.md:32 [HISTORY] Prompt cites pm/v2/tools/verbs/create.py.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03a-plugins.md:32,33 [HISTORY] Prompt cites pm/v2/tools/verbs/lint.py and summary.py.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/03c-import.md:29 [HISTORY] Prompt cites pm/v2/docs/spec/v2/SPEC.md.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-c-remove-v2.md:1,13,18,28,31,34,44,53 [HISTORY] The removal prompt itself. Line 44 holds its own check command, `rg -n 'pm/v2' --glob '!docs/programs/**' .`.
/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/04-integration-d-docs.md:18 [HISTORY] Prompt says pm/v2/ is gone by then.
Coverage: no hits in wt/, the root README.md/AGENTS.md, tools/, deploy/, .github/ or docs/*.md. The `.worktrees/` and `.context/` directories were excluded from the search; I did not check them, and I did not check other worktrees' copies of these files. The bare names SPEC.md/CHANGELOG.md/invariants.md and the other bare filenames had no hits outside pm/v2, apart from those listed above.
RE-VERIFY: rg -n 'pm/v2|v2/tools/verbs|spec/v[12]|cut-list\.md|run_parity|test_cli_parity|test_cli_contract|test_gitcommit|golden_diff' /Users/matthias/projects/frontier-clean --glob '!docs/programs/**' --glob '!pm/v2/**' --glob '!pm/dash-ui/**' --glob '!.worktrees/**' --glob '!.context/**'  (expect only the .gitignore:128 comment, or no match once it is reworded)
