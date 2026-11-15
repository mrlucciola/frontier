# INITIATIVE: pm follow-ups after delivery (fc-359b5b)

Run in the delivery overseer's session (7eb34f41), 2026-11-15, on the operator's
request after fc-ccecda closed.

## State

Filled from `pm ticket tree fc-359b5b` at each update.

## Next batch

Turn 1, in parallel: fc-5e5a20 (`prompts/01-nested.md`), fc-d3d87b
(`prompts/03-prompt-once.md`), fc-8ef942 (`prompts/04-link-note.md`), and fc-419332
(`prompts/05-runbook.md`). fc-c8212a (`prompts/02-backup.md`) follows once fc-5e5a20
merges, because both change `pm/tools/store.py`.

## Owed operator actions

None.

## Facts not to re-derive

- **Rulings 2026-11-15.** Sharing across clones is dropped. dash-ui is a top-level
  nested repo that reads pm, and nothing under `pm/` may know of it. Recorded in
  PLAN.md.
- **Spec first.** The design changes are on main (`pm/docs/design.md`: Store,
  Backup, the Verbs `link` row, the Harness hooks `prompt` row, and Not carried over).
  The overseer writes each transcript on the ticket branch before dispatch. Workers
  edit neither.
- **Known structure-check violation.** `pm/README.md:76` links to the dash-ui README
  that moved away. It is the operator's to rule on, so workers ignore exactly that
  line.
- **Stray backup refs.** These exist before any import:
  - `/Users/matthias/frontier` `refs/pm/log` f5775a9f4d1f2499808e372073ef278e94d050fd
  - `/Users/matthias/projects/frontier-clean` `refs/pm/log` d5fe02f404b4b0568ee16d653b48f9f526a35139
