# pm-wt-rewrite/04/02c pm structure verbs and the duplicate guard fc-2a6562:fc-8b871a

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02c-structure.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/02c pm structure verbs and the duplicate guard fc-2a6562:fc-8b871a

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/02c-structure.md`

Ticket **fc-8b871a**, one of four step-2 workers running in parallel on separate
branches. The core (dispatcher, store, who, render, registry, `init new show stores`)
is merged. Read and obey `docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md`
first, especially "Module contract" and "Shared files in a parallel step".

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-8b871a`.

## Read first

`pm/docs/design.md` sections "Events", "Verbs" (the duplicates rule) and "Output";
transcripts `08-note-edit.t`, `09-link.t`, `11-duplicate.t`, and the `--from` step of
`04-done-findings.t`; `pm/tools/verbs/new.py` and `pm/tools/store.py` as core left
them (`new.py` already holds the copied `find_duplicates` and `dup_tokens`).

## Deliver

1. `pm/tools/verbs/note.py`: `pm note [id] "text" [-k decision|finding|measurement]`;
   a first word that is a number or an id is the ticket, not the text (transcript 12).
2. `pm/tools/verbs/edit.py`: the design's fields, `--under none` clears, the result
   line `<id> edited: <fields>` in the order the transcripts show; nothing to change
   is a usage error. `--under` refuses a ticket that is not an epic, as `new` does.
3. `pm/tools/verbs/link.py`: `pm link a blocks|related b [c ...]`; `blocks` stores
   `blocked-by` on the blocked ticket; `related` shows on both sides; the cycle check;
   a link that exists prints its line and appends nothing. All ids checked before the
   one `change`.
4. `pm/tools/verbs/unlink.py`: removes every link between the two, in either direction.
5. In `new.py`: replace `store.unbuilt("link")` with `--from`, `--blocks` and
   `--blocked-by`, appended in the same `change` as the `new` event; replace
   `store.unbuilt("duplicate")` with the refusal of transcript 11 and `--new`, which
   files anyway. The duplicate measure stays the copied code, unchanged.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 08-note-edit -k 09-link -k 11-duplicate -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending -v
```

The second exits 0 with `failed 0`, and its `unbuilt verbs still needed` line names
none of `note edit link unlink duplicate`. For each of your three transcripts that is
still pending, name the verb it waits on (another ticket's) and confirm every step
before that call matches.

## Report

Commit message `pm structure verbs: note edit link unlink, new's links and duplicate guard`.
Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-8b871a/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/02c-structure.md`.
