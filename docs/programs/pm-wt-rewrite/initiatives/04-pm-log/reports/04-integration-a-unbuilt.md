# 04-integration-a-unbuilt report

TICKET
fc-d6c61c (04a), worked on branch fc-d6c61c.

DID
- Removed `unbuilt` from pm/tools/store.py and both calls in pm/cli/pm (`help_verb`, `run_verb`). A missing verb file now raises from `open` or the loader and reaches the dispatcher's internal-error path.
- pm/AGENTS.md: dropped the pending-rule paragraph; gate command is `/usr/bin/python3 -B pm/tests/run_transcripts.py`.

EVIDENCE
- `/usr/bin/python3 -B pm/tests/run_transcripts.py`: exit 0, `transcripts: passed 24, pending 0, failed 0`
- `rg -n 'unbuilt|PM_UNBUILT_LOG' pm/cli pm/tools`: no output, exit 1
- `python3 -B docs/check_structure.py`: `check_structure: ok (7 components, 4 exempted)`

COMMITS
Commit `pm integration: remove the unbuilt mechanism` (this report included).

NOT DONE
- pm/tests/run_transcripts.py still has `--allow-pending` handling; overseer owns it.
- Did not verify that a missing verb file yields the `pm: internal error:` line; no transcript covers it.

BLOCKED ON OPERATOR
None.

ARTIFACTS
pm/cli/pm, pm/tools/store.py, pm/AGENTS.md, this report.
