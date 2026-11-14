# 04c docs report (fc-59011f)

## DID

- `pm/INSTALL.md`: symlink install (`pm-next` side install, or `pm` on a machine without
  one), prerequisites, verify (`--help`, `ticket stores`), disable, remove; removal leaves
  `.pm/` data and the registry untouched; cutover stated as a separate operator runbook.
- `pm/README.md`: what pm is, the two entry points, verb table, registry default
  `~/.config/pm/stores.json` and `PM_STORES_FILE`, routes table; "being rewritten" line
  replaced with the installed-pm-stays-frontier note.
- `pm/AGENTS.md`: verb-file shape, routes, unittest discover gate, parity runner,
  `golden_diff.py` documented as a gate that reads live stores read-only (exit 0/1/2,
  ruled history-pending skip), unbuilt mechanism gone from `tools/`.
- Root `README.md` pm row: unchanged (purpose text "Ticket store for agent work" still matches).

## GATE

- `python3 -B docs/check_structure.py`: `check_structure: ok (7 components, 4 exempted)`.
  The known `docs/contributing.md:149 X-STALE exemption cwf L-ROOT` violation did not
  show in the worktree.
- `/usr/bin/python3 -B -m unittest discover -s pm/tests`: started (includes the slow
  parity suite); first 120s of output all `.`/`s`, no failure; the final summary line was
  not readable to me (background output file denied). Not confirmed to completion.

## NOT DONE

- Final line of the full unittest run not seen (see GATE). Re-run it to confirm.
- `INSTALL.md` verification was run by invoking `pm/cli/pm` directly, not through a
  created symlink (no write to `~/.local/bin`). `ticket stores` printed nothing, exit 0,
  with no registry present.
- `tests/run_parity.py` still has pending/unbuilt bookkeeping; not edited (out of write set).
- `routing.py` and `store.py` error texts still name `~/frontier/runtime-tools/pm/stores.json`
  as the registry source; code, not touched.
