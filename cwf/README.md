# Contextual Work Framework 0.1.0

**Deployable candidate.** Global agent skills for Kiro CLI v3 and local, model-free tools for contextual discovery, task continuity, and coordinated work. No ticketing system, repository initialization, background service, hooks, remote memory, or API key is required.

Supported provider: Kiro CLI v3. For this repository's pilot, start with [setup and removal](/cwf/INSTALL.md). What CWF is for and what it is not: [product requirements](/cwf/docs/PRD.md).
The historical records below describe the imported candidate,
not an activated or behaviorally qualified live pilot. Read [maintenance instructions](/cwf/AGENTS.md) before changing this component.

Targets macOS with Python 3.11+, Git for worktree operations, and Kiro CLI v3 sessions. Mechanics are tested in the authoring environment; macOS and live Kiro v3 qualification remain pending. See `docs/VALIDATION.md` for executed versus pending checks.

## Start here

1. Read `docs/OPERATIONS.md` for prerequisites, deployment, and the command reference.
2. Run the tests before deploying. Tests use disposable homes/repositories, never your real `~/.kiro` configuration.
3. Run `zsh deploy.sh` from this directory, then verify in a fresh `kiro-cli --v3` session as [setup](/cwf/INSTALL.md) describes.

The design contract is `docs/SPECIFICATION.md`; the product requirements in `docs/PRD.md` win where they disagree. Implemented scope and deliberate differences are in `docs/DEVIATIONS.md`. Native platform assumptions and source links are in `docs/PLATFORM.md`.

## Files

| Path | Purpose |
| --- | --- |
| `cwf.py`, `cwf/` | Standard-library runtime and command entrypoint |
| `skills/` | Six native skill entrypoints |
| `patterns/` | Shared, on-demand questions and tool usage |
| `schemas/` | Published JSON Schema contracts |
| `fixtures/`, `tests/` | Synthetic inputs and mechanical regression tests |
| `docs/` | Operations, limits, and qualification |
| `deploy.sh`, `instructions/` | Deployment script and the block it maintains |

CWF never replaces your model/provider/approval settings. `deploy.sh` adds namespaced skill links under `~/.kiro/skills`, a launcher link, and one marked block in `~/.kiro/steering/frontier.md`. It does not guarantee that a model will select or follow a skill; that requires behavioral qualification.

## Quick checks

```sh
python3 -B cwf.py version
python3 -B tests/test_cwf.py
python3 -B tests/test_deploy.py
```

Runtime has no third-party Python dependencies. An optional development test uses `jsonschema` if already available; absence is reported as a skipped check rather than installed automatically. Do not share local databases, raw source context, or personal observations: they may contain private paths/content. Default state export is counts-only.
