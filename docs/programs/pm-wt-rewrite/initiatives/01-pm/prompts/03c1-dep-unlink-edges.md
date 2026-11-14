# pm-wt-rewrite/01/03c1 pm verbs dep unlink and cross-store edges fc-c3514f:fc-c10bcf

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03c1-dep-unlink-edges.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/03c1 pm verbs dep unlink and cross-store edges fc-c3514f:fc-c10bcf

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03c1-dep-unlink-edges.md`

Ticket **fc-c10bcf** (structure verbs), first of two serial workers on its branch; the
second builds `reparent`, `edit`, `note`. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/03-common.md` first.

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf`.
- Spec: `pm ticket show fc-c10bcf` (body and notes). The duplicate guard is already
  built in `create.py` (overseer decision in the notes); do not touch it.

## Deliver

1. `pm/tools/verbs/dep.py` and `unlink.py`: `dep SRC blocks|related DST` with the cycle
   check, cross-store `blocks` placed as `blocked-by` on the blocked ticket in its own
   store (printing the arrow), cross-store `related` kept on the source as
   `<prefix>/<id>`, the `<prefix>:<id>` refusal, an unresolvable other side refused
   naming the registry; `unlink --type` removing an edge in either written form.
2. Edge routing in `pm/tools/ticket`: route `dep` and `unlink` to the store that holds
   the edge, as the old `route_edge` does. This is the one edit you make to the entry;
   keep it to that.
3. `store.edge_target`'s cross-store branch (today `unbuilt("cross-store-edge")`)
   resolves through `routing.py`, so `create --discovered-from <prefix>/<id>` works.

Old source by name: `ticket`: `is_remote_ref`, `edge_target`, `cmd_dep`, `cmd_unlink`,
`route_edge`, their `add_parser` blocks; `ticket_core.py`: `Store.would_cycle`,
`Store.cross_target`, `local_id`, `resolve_store`.

## Gate

The common gate with `-k dep -k unlink -k cycle -k CrossStoreEdgeTest -k test_discovered_from`.
The full run's `unbuilt verbs still needed:` line names none of `dep`, `unlink`,
`cross-store-edge`.

## Report

Commit message `pm structure: dep, unlink, cross-store edges (fc-c10bcf)`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-c10bcf/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/03c1-dep-unlink-edges.md`.
