# pm-wt-rewrite/01/04d2 pm review fixes: verb files fc-c3514f:fc-59011f

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04d2-review-fixes-verbs.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/04d2 pm review fixes: verb files fc-c3514f:fc-59011f

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/04d2-review-fixes-verbs.md`

Ticket **fc-59011f** (pm integration). The review is
`docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04-review.md`; the previous
worker fixed the shared-module items (report `04d1-review-fixes-shared.md`). You fix the
verb-local items below. The overseer's rulings decide scope. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` ("Where you work"
and "Rules").

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f`.

## Fix (each is a review finding; read its line there)

1. `validate.py` I-19: the hint names a flag `edit` lacks. Replace it with
   `operator: {lineno} /closure_reason: set it to null by hand` (so `agent_may_fix` is
   false), and record old and new text in `pm/docs/cut-list.md`'s fix-hint bullet.
2. `summary.py`: docstring says what it does (reads the store; retries an owed history
   snapshot); semaphores through `store.is_semaphore`.
3. `edit.py`: docstring says only priority and body leave edit-trail notes.
4. `note.py`: delete the unreachable `spec_version < 2` refusal.
5. `stores.py`: delete the dead `elif` that appends to an unread list.
6. `note.py`, `edit.py`, `reparent.py`: use `store.locked_verb(args, "<verb>")` and
   inline the trampoline; `dep.py` and `unlink.py` pass the subject string directly.
   Commit subjects stay byte-identical (the parity suite checks commit logs).
7. `validate.py`: add `run_code(args) -> int`; `lint.py` calls it instead of catching
   `SystemExit`; `return run_workspace(args)` / `return run_dispatch(args)` where the
   call ends in exit; inline `_relpath`; `lint.py` opens the store once.
8. `overview.py`: the generated file's regenerate line names
   `pm view overview --store <root> --out <file>`; update `pm/tests/test_views.py`
   where it pins the old line.

## Gate

```sh
/usr/bin/python3 -B -m unittest discover -s pm/tests
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket
/usr/bin/python3 -B pm/tests/golden_diff.py
rg -n 'closure-reason null|Reads only; never writes|spec_version.*< *2' pm/tools/verbs
```

All pass; parity ends `pending 0, failed 0`; the golden diff exits 0; the `rg` prints
nothing. Redirect long runs to the worktree's `.tmp/` and paste their summary lines.

## Report

Commit message `pm integration: review fixes in verb files (fc-59011f)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-59011f/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04d2-review-fixes-verbs.md`.
