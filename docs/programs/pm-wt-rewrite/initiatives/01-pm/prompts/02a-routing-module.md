# pm-wt-rewrite/01/02a pm routing.py and its call sites fc-c3514f:fc-459fe0

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/02a-routing-module.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/01/02a pm routing.py and its call sites fc-c3514f:fc-459fe0

`docs/programs/pm-wt-rewrite/initiatives/01-pm/prompts/02a-routing-module.md`

You are a worker on ticket **fc-459fe0** (pm routing), first of two serial workers on
its branch. fc-2b34c9 is merged: `pm/cli/pm`, `pm/tools/ticket`, `pm/tools/store.py`,
`pm/tools/gitcommit.py` and the verbs `init`, `create`, `show` exist, and every place
that needed routing calls `store.unbuilt("routing")`. You build
`pm/tools/routing.py` and replace those call sites. The next worker builds the `where`
and `stores` verbs. Do only your part.

## Where you work

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0`, branch
  `fc-459fe0`. Every path you edit is under it; every git command is
  `git -C <worktree> ...`; `cd` is refused by a hook, so use absolute paths. If the
  worktree does not exist, stop and report.
- Binding worker rules: `/Users/matthias/frontier/docs/programs/frontier-tooling/part2/worker-brief.md`
  (branch and write rules, budget, report shape). You never run `wt`, `pm ticket`
  writes, rebase or merge. Commit on the branch and stop. Budget: 80k tokens / 40
  tool calls; near it, commit what is green and list the rest in NOT DONE.
- Code standard: `docs/component-principles.md`. Read it first.

## Read first (selectively)

- `pm ticket show fc-459fe0` (the body is the spec); `pm/docs/cut-list.md`.
- `rg -n 'unbuilt\("routing"\)' <worktree>/pm/tools` for every call site you replace.
- `pm/tools/store.py` and `pm/tools/ticket` whole (they are short).
- `pm/docs/spec/v2/SPEC.md` section 3 "Store registry" and section 4 "Cross-store edges".
- Old source, read-only, at `/Users/matthias/frontier/runtime-tools/pm/ticket/src/`.
  Line numbers move as the old pm changes; find each function with
  `rg -n 'def <name>'` and read only it. `ticket_core.py`: `owned_prefixes`,
  `store_owns`, `registry_path`, `load_registry`, `ref_prefix`, `Resolved`,
  `cwd_store_role`, `registry_entry`, `frozen_notice`, `refuse_if_frozen`,
  `_dedupe_owners`, `owners_by_prefix`, `resolve_store`, `route_ids`, `local_id`,
  `locked_store` (only its `refuse_if_frozen` call), and on `Store`: `cross_target`,
  `_resolve_cross`, `_row_state`, `cross_blockers`, `unsatisfied_cross`,
  `cross_blocks_of`. `ticket`: `ROUTED_VERBS`, `route_args` (not `route_edge`).
- The parity tests you are gated on: `class StoreRoutingTest` in
  `pm/tests/test_cli_parity.py` (find with `rg -n`).

## Deliver

1. `pm/tools/routing.py`: the registry (`$PM_STORES_FILE`, else
   `~/.config/pm/stores.json`; no file and no symlink is an empty registry, a dangling
   symlink is an error), `<prefix>/<id>` parsing, owned and legacy prefixes, the
   resolve order (`--store`, cwd store, registered owner with live over frozen, frozen
   row fallback for reads), the fail-closed frozen and unreadable-registry refusals on
   mutations only, and a cross-store row lookup for readiness and edges. Error texts
   that name the old registry location (`runtime-tools/pm/stores.json`) name the new
   default instead, unless a parity test asserts the old text; list each such text in
   DID.
2. `pm/tools/ticket`: route id-taking verbs before `run`, as `route_args` does, for
   every verb in `ROUTED_VERBS` except `dep` and `unlink` (fc-c10bcf routes edges):
   normalise `<prefix>/<id>` to the bare id and set `args.repo` to the owning repo,
   so a verb opens the right store and never has to route after opening one (overseer
   ruling on review `reports/01-review.md`). A verb whose file does not exist is
   still `unbuilt` first.
3. `pm/tools/store.py`, additive plus the call sites: `locked_store` refuses a frozen
   store by calling routing's frozen check through a function-level `import routing`
   (overseer ruling: `routing.py` may import `store` at module level; `store` imports
   `routing` only inside the function, so there is no import cycle at load time).
   Readiness counts unsatisfied cross-store blockers. Every `store.unbuilt("routing")`
   is replaced. Change no existing signature; if you must, stop and report it.
4. `pm/tools/verbs/show.py`: its `routing` call sites use `routing.py` (cross-store
   blockers, the reverse "blocks (other stores)" line). Its own after-open check for
   another store's id goes away, since the entry routed before `run`.

Not yours: `where.py`, `stores.py` (next worker); `dep`/`unlink` edge routing and
`create --discovered-from` across stores (fc-c10bcf); `close --findings` routing
(fc-d73327). Leave their `unbuilt` calls. Do not edit `pm/tests/test_cli_parity.py`,
`pm/tests/run_parity.py` or anything under `pm/docs/`; a parity test that looks wrong
goes in NOT DONE with its name and why. Never write under `~/frontier`.

## Gate (absolute paths, from the worktree root)

```sh
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket -k StoreRoutingTest --allow-pending
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'
/usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_gitcommit.py'
/usr/bin/python3 -B pm/tests/run_parity.py --cli pm/tools/ticket --allow-pending
```

Every run must exit 0 with `failed 0`. Redirect the parity runs to files under the
worktree's `.tmp/` and paste only their `parity:` and `unbuilt verbs still needed:`
lines. The full run takes about four minutes; run it once at the end. Report the
StoreRoutingTest pending count before and after your change.

## Report

Commit on `fc-459fe0` with explicit `git add` paths, message `pm routing: registry,
prefix routing, frozen stores (fc-459fe0)` plus the trailer
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Then write the report, in
the worker-brief shape, to
`/Users/matthias/projects/frontier-clean/.worktrees/fc-459fe0/docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/02a-routing-module.md`,
commit it on the same branch, and print only that path.
