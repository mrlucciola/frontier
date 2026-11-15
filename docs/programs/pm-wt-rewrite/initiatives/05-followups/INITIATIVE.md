# INITIATIVE: pm follow-ups after delivery (fc-359b5b)

Status: closed 2026-11-15. Run in the delivery overseer's session (7eb34f41), at the
operator's request after fc-ccecda closed.

## State

```text
fc-359b5b  P2  closed        pm follow-ups after delivery: nested stores, per-store backup, prompt once per session, link --note, runbook additions [epic]
impacts (transitively blocks):
  (none)
blocked-by chain:
  (none)
epic subtree:
  fc-5e5a20  P1  closed        pm: a nested store with config.json but no log.jsonl silently resolves to the parent store's log
  fc-c8212a  P1  closed        pm backup ref is per git repo, not per store: any scratch or test store inside a repo overwrites that repo's refs/pm/log
  fc-d3d87b  P2  closed        pm hook prompt: mention each ticket once per session
  fc-8ef942  P2  closed        pm link --note: the reason for a link, as a note on each ticket after the relation
  fc-419332  P2  closed        CUTOVER.md additions: stray refs/pm/log before import, the dropped board views, sharing across clones dropped
```

## Next batch

None. The epic is closed.

## Owed operator actions

The operator rules on two lines that still name dash-ui inside pm:
`pm/AGENTS.md:32`, a route row, and `pm/README.md:76`, a link the move broke. The
second makes `docs/check_structure.py` report a violation. The stray-ref deletion is
CUTOVER.md step 1A.

## Facts not to re-derive

- **Rulings 2026-11-15.** Sharing across clones is dropped. dash-ui is a top-level
  nested repo that reads pm, and nothing under `pm/` may know of it. Both are recorded
  in PLAN.md.
- **Each transcript reproduced its defect before the fix.**
  - 26-nested: an inner store's ticket landed in the outer store.
  - 18-backup: a scratch store replaced the checkout's 3-event backup with its own
    1-event log.
- **Dropped from fc-c8212a's body:** the restore-hint prefix check. With
  `store.has_backup`, no new stray ref can be written, and step 1A removes the two
  that exist.
