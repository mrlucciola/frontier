# Contextual Work Framework 0.1.0

**Installation candidate.** Global Codex skills and local, model-free tools for contextual discovery, task continuity, and coordinated work. No ticketing system, repository initialization, background service, hooks, remote memory, or API key is required.

For this repository's Codex pilot, start with [setup and removal](INSTALL.md).
The component includes the fc-14662f macOS fixture repair; current C2 evidence
lives on fc-2e70b4. The historical records below describe the imported candidate,
not an activated or behaviorally qualified live pilot. C2's global entry is a
separate reviewed configuration product; always use `guidance:false` for that
pilot. Read [maintenance instructions](AGENTS.md) before changing this component.

Targets macOS with Python 3.11+, Git for worktree operations, and Codex CLI/IDE extension. Mechanics are tested in the authoring environment; macOS and live Codex qualification remain pending. See `docs/VALIDATION.md` and `validation-ledger.json` for executed versus pending checks.

## Start here

1. Read `docs/OPERATIONS.md` for prerequisites, installation planning/apply, toggles, upgrade, rollback, and uninstall.
2. Run the tests in a temporary environment before live installation. Tests use disposable homes/repositories, never your real Codex configuration.
3. Give a fresh local Codex agent `prompts/INSTALL-AND-QUALIFY.md` and this extracted directory. That prompt authorizes local installation only when you actually submit it to that agent.

The original design contract is `docs/SPECIFICATION.md`. Implemented scope and deliberate differences are in `docs/DEVIATIONS.md`. Native platform assumptions and source links are in `docs/PLATFORM.md`.

## Files

| Path | Purpose |
| --- | --- |
| `cwf.py`, `cwf/` | Standard-library runtime and command entrypoint |
| `skills/` | Six native skill entrypoints and UI metadata |
| `patterns/` | Shared, on-demand questions and tool usage |
| `schemas/` | Published JSON Schema contracts |
| `fixtures/`, `tests/` | Synthetic inputs and mechanical regression tests |
| `docs/`, `prompts/` | Operations, limits, qualification, and fresh-agent handoff |
| `MANIFEST.json`, `CHECKSUMS.sha256` | Integrity and owned-release inventory; not signatures or authenticity proof |

The ZIP itself does not install or change anything. CWF never replaces your model/provider/approval settings. It may add an owned activation block and namespaced skills when you apply a reviewed installation plan. It does not guarantee that a model will select or follow a skill; that requires behavioral qualification.

## Quick checks from the extracted directory

```sh
python3 -B cwf.py version
python3 -B -m unittest discover -s tests -v
python3 -B cwf.py doctor
```

`doctor` reports local mechanics and limitations; it does not certify live skill activation. Runtime has no third-party Python dependencies. An optional development test uses `jsonschema` if already available; absence is reported as a skipped check rather than installed automatically.

## Sharing

Share this unchanged candidate ZIP with testers. Each tester installs into their own home and qualifies their own configuration. Do not share generated installation plans, receipts, local databases, raw source context, or personal observations. Those may contain private paths/content. Default state export is counts-only.
