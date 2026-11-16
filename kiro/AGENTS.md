# Kiro maintenance

`kiro/` owns the provider adapter for Kiro CLI 2.x: the version-gated
`deploy.sh`, the copy-paste sync transport in `tools/`, the recon probe
`cli/kiro-probe`, and the routes to the pinned 2.x reference vendored under
`kiro/docs/reference/`. It never runs kiro on the dev machine.

| Change | Read |
| --- | --- |
| Goal, constraints, batches, work-machine procedure, probe report log | [Plan](/kiro/docs/plan.md); reports live in `kiro/docs/probe-log/` |
| Kiro 2.x surfaces (agent JSON fields, hooks, `toolsSettings`, scopes) | the pinned reference under `kiro/docs/reference/` (owned by another branch, vendored at B1); the v3 ban list is in the [plan](/kiro/docs/plan.md) |
| Sync transport: manifest, base64 chunks, apply verification | `tools/mk_sync.py` owns the default file list; `tools/APPLY.sh` stages to a temporary directory and verifies bytes and sha before any write; `tools/mk_sync_branch.py` imports `mk_sync.collect` so the orphan branch and the bundle never drift |
| Deploy, refusal order, the steering block | `deploy.sh` and [setup](/kiro/INSTALL.md) |
| Probe line grammar and exit codes | `cli/kiro-probe`, pinned by `tests/test_probe.py` |

Run the kiro checks from the repository root.

```sh
python3 -B kiro/tests/test_sync.py
python3 -B kiro/tests/test_deploy.py
python3 -B kiro/tests/test_probe.py
python3 -B docs/check_structure.py
```

Only Kiro CLI 2.x is supported: v3-only surfaces (markdown agents,
`permissions.yaml`, standalone `.kiro/hooks/*.json`, PascalCase triggers,
tool category tags, `skill://` resources) must not appear in this component.
`kiro/docs/reference/` is owned by another branch; add no content here. The
tests use disposable homes and PATH stubs and never spawn a live kiro
session; real kiro behavior is qualified only by probe reports at work.
