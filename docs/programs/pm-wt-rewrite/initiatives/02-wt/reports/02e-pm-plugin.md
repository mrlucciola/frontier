# 02e wt pm plugin (fc-347c67)

## DONE
- `wt/pm-plugin/{pre-done,post-take,orient}` (executable zsh); transcripts `wt/tests/t/01-pre-done.t`, `02-post-take.t`, `03-orient.t`.
- pre-done refusal: one line, under 300 bytes, names `wt finish <id>` and `wt park <id>`; passes with `WT_CALLER=1` or no worktree dir.
- post-take: `next: wt start <id>` iff `$PM_STORE/.worktrees` exists and `WT_CALLER` != 1.
- orient: done ticket -> `wt finish <id>`; unheld (open/parked) -> `wt start <id>` to resume or `wt park <id>`; ids pm does not know are skipped silently.

## Decisions
- Unheld ticket advice offers both start and park; I did not check wt/docs/contract.md for a single ruling. Orient falls back to `$PWD` if `PM_STORE` is unset (not exercised).

## NOT DONE
- Commit: see below. No docs edited (integration ticket's).

## EVIDENCE
```
cli under test: .../fc-347c67/pm/cli/pm
transcripts: passed 3, failed 0
```
`/bin/zsh -n` clean on all three files. wt suite gate not applicable (no verb).
