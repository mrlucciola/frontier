# 02a pm routing module (fc-459fe0)

## DID

- `pm/tools/routing.py` (new): registry (`PM_STORES_FILE`, else `~/.config/pm/stores.json`), `load_registry`, `resolve_store`, `route_ids`, `cwd_store_role`, `registry_entry`, `frozen_notice`, `refuse_if_frozen`, owners dedupe, cross-store row lookup (`cross_target`, `cross_blockers`, `unsatisfied_cross`, `cross_blocks_of`, `cross_label`). Reuses `store.owned_prefixes`, `ref_prefix`, `local_id`.
- `pm/tools/ticket`: `ROUTED_VERBS` (all but `dep`/`unlink`) and `route_args` run before `module.run`; unbuilt verbs still stop first.
- `pm/tools/store.py`: `Store.cross_cache` attribute; `is_ready` counts unsatisfied cross-store blockers (function-level `import routing`); `locked_store` calls `routing.refuse_if_frozen` before locking. No signature changed. `edge_target`'s `unbuilt("cross-store-edge")` left for fc-c10bcf.
- `pm/tools/verbs/show.py`: all three `unbuilt("routing")` sites replaced (remote-id check removed, cross blockers in `blocked_by` text, reverse "blocks (other stores)" line); dead `_registry_lists_a_store` removed.
- Error texts changed: collision text and routed-frozen text now name `registry_path()` instead of `runtime-tools/pm/stores.json`. Kept verbatim: the no-owner text ("add the repo to ~/frontier/runtime-tools/pm/stores.json and deploy pm"), asserted by parity tests (`test_where_refuses_with_the_design_text...`, `test_findings_unowned_prefix...`).

## Gate (verbatim)

- StoreRoutingTest, before (main d1f9da9) and after: `parity: passed 0, pending 67, failed 0, skipped 0` / `unbuilt verbs still needed: claim`. Every test in the class is pending because its `setUp` calls `claim`, so the class cannot prove anything yet; I verified by hand instead (below).
- test_cli_contract.py: `OK (skipped=21)`; test_gitcommit.py: `Ran 24 tests ... OK`.
- Full: `parity: passed 20, pending 242, failed 0, skipped 9`; `unbuilt verbs still needed: archive, claim, close, cross-store-edge, dep, edit, history, hold, lint, list, note, ready, release, reparent, stores, summary, validate` (no `routing`).
- Manual smoke (`.tmp/smoke.py`, temp stores in $TMPDIR): show by bare and `bb/` id routes to the owner; frozen row readable; `create` from frozen cwd and `--store <frozen>` refused naming the registry; unowned prefix gives the design text; `blocked_by: bb/<id> (open)` and reverse `blocks (other stores): aa/<id>`; unparsable registry refuses `create`, `show` still works with "(unresolved: ...)".

## NOT DONE

- Parity coverage of routing/frozen/is_ready is unproven by the suite until `claim`, `close`, `list` etc. exist; re-run `-k StoreRoutingTest` after those verbs land.
- `where`, `stores` (next worker); `dep`/`unlink`/`create --discovered-from` cross-store edges (fc-c10bcf); `close --findings` routing (fc-d73327).
- `summary` waiting-gates and `tree` leaves will use `routing.cross_blockers` when built; not wired.

## Findings

- `store.py` still carries its own `is_remote_ref`; now used only by `edge_target`. Not touched.
