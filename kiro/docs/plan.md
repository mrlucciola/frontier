# Kiro adapter plan

Durable memory for the unattended kiro thread. This file is the plan of
record; keep it under 120 lines and update it as batches close.

## Goal

Run the frontier-clean core components — the ticket store, the worktree tool,
CWF, and ICM — under kiro-cli 2.17 on a locked-down work machine, and keep
them deployable there without ever running kiro on the dev machine.

## Constraints

- The dev machine never runs kiro. Correctness of kiro behavior is established
  only by probe reports brought back from the work machine.
- The work machine runs kiro-cli 2.17 only. Version-locked 2.17; kiro v3 is
  forbidden. V3-only surfaces must never appear: markdown agent format,
  `permissions.yaml`, standalone `.kiro/hooks/*.json`, PascalCase triggers
  (`SessionStart` and friends), tool category tags, `skill://` resource URIs.
- v2 facts the adapter relies on: agents are JSON-only configs in
  `~/.kiro/agents/` (global) or `<repo>/.kiro/agents/` (project scope) with
  fields `name`, `description`, `prompt: "file://..."`, `tools`,
  `toolsSettings` (regex `allowedCommands`/`deniedCommands`, glob
  `allowedPaths`/`deniedPaths`, `autoAllowReadonly`, `denyByDefault`),
  `resources: ["file://AGENTS.md"]`, and embedded hooks with triggers
  `agentSpawn`, `userPromptSubmit`, `preToolUse` (matcher = tool name),
  `postToolUse`, `stop`. Hooks read JSON on STDIN; exit 0 is ok (STDOUT is
  captured), exit 2 blocks (`preToolUse`). Permissions come from
  `--trust-all-tools`/`--trust-tools` and the `/tools` slash commands. v2
  inherits steering files, skills, and `AGENTS.md` into agents.
- The work machine is firewalled and cannot clone. Files arrive only by
  hand-paste of raw file views from a public GitHub branch.
- All work happens on branch `kiro-main`; never on `main`.

## Transfer design

Push an orphan branch `kiro-sync` (plumbing only, no checkout) to the public
repo from the dev machine. Bulk transport is the chunk bundle:
`kiro/tools/mk_sync.py` writes `MANIFEST.txt` (`<sha256> <bytes> <relpath>`)
and `SYNC-NNN.txt` chunks holding `BEGIN`/base64/`END` records, and prints
each chunk's sha256 so the hand-paster can eyeball whole chunks. At work,
`sh APPLY.sh <chunks-dir> <target-root>` verifies bytes and sha before any
write, refuses absolute or `..` paths, and reports one PASS/FAIL per file.

## Batches

- **B0 (this batch, done at scaffold):** component skeleton, `deploy.sh`
  version gate, sync transport (`mk_sync.py`, `APPLY.sh`,
  `mk_sync_branch.py`), `cli/kiro-probe`, tests, docs. Pinned 2.x reference
  is vendored under `kiro/docs/reference/` by its owning branch.
- **B1 — recon at work.** Run `kiro-probe` (default mode: version, git and
  python3 presence, `~/.kiro` layout, steering and skills paths, symlink
  following, settings-file candidates). Then, manually, `kiro-probe --smoke`
  (headless `kiro-cli chat --v2 --no-interactive` token echo). Paste the
  report back and record it. Close B1 by vendoring the reference, confirming
  the global steering path, and adding steering/skills routes.
- **B2 — per-component kiro sections.** Add kiro sections to pm, wt, cwf and
  icm: `deploy.sh` additions for kiro, `instructions/kiro.*.md` snippets, and
  a project-scope `.kiro/agents/frontier.json` (JSON-only, v2 fields above).
- **B3 — deploy and probe iterate at work.** Deploy via the paste transport,
  run the probe, fix from reports, repeat until the components run.

## Probe reports

Reports (max 40 lines, ending `PROBE-END`) are pasted back to the dev
machine and logged under `kiro/docs/probe-log/` as
`<date>-kiro<version>.txt`; see that directory's README for the format.

## Open questions (answer in B1)

- Exact global steering path and whether a fresh chat session loads it
  (currently assumed `~/.kiro/steering/`, marked CONFIRM-IN-B1 in
  /kiro/INSTALL.md).
- Whether `~/.kiro` symlinked directories are followed (probe records
  filesystem support only).
- Exit code of `kiro-cli chat --v2 --no-interactive` on a trusted machine,
  and the real settings-file inventory under `~/.kiro`.
