# Kiro branch policy

`kiro-main` is the kiro-only line of this repository: these components run
under the Kiro v3 runtime on the work machine. There is no kiro adapter
component — the branch itself is the kiro variant, and its components keep
their own directories.

## Branch rules

- Development lands on `kiro-main`: commit here, merge here. This branch's
  work never merges into `main`.
- Rebasing or merging `main` in as changes arrive is allowed and welcome, but
  never required; `kiro-main` may trail `main` for as long as it needs.

## Runtime rules

- Agents run only through `kiro-cli --v3` (the Kiro v3 runtime).
- No version gate: nothing pins `kiro-cli --version` output, and no deploy or
  run refuses based on it. `kiro-cli --version` is recorded as information
  in recon only.

## Work-machine transfer

The work machine is firewalled and cannot clone. Files arrive only as
hand-pasted raw file views:

1. Dev machine: push the branch to the public repository
   (`git push origin kiro-main`).
2. Work machine: for each needed file, open
   `https://raw.githubusercontent.com/OWNER/REPO/kiro-main/<path>`,
   copy, and write it to the same relative path in the work checkout —
   in a terminal with `cat > <path>`, never a text editor.
3. `chmod +x` the scripts and executables; paste drops the bit.

There is no manifest, checksum, chunk, or apply step. Correctness at work is
established by reading the files back and by the components' own checks, not
by byte validation.

## Kiro surface map

Every component targets these Kiro v3 surfaces. Paths marked CONFIRM are the
layout the v3-era docs name but this branch has not yet verified on the work
machine; keep the marker until recon settles it.

| Concern | Kiro v3 destination |
| --- | --- |
| Global instructions | `~/.kiro/steering/frontier.md`, one marked block per component (CONFIRM) |
| Project instructions | `<repo>/.kiro/steering/` (CONFIRM) |
| Skills | `~/.kiro/skills/<name>` symlinks; project scope `<repo>/.kiro/skills/` (CONFIRM) |
| Hooks | `~/.kiro/hooks/<component>.json`, PascalCase triggers (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`), command handlers (CONFIRM) |
| Agents | markdown agent definitions, `~/.kiro/agents/` or `<repo>/.kiro/agents/` (CONFIRM) |
| Permissions | `permissions.yaml`, reviewed by hand; never written by a deploy script (CONFIRM) |
| Entry instructions | `AGENTS.md` read natively; no shim files of any other name |

Session identity is `--session <id>` or `PM_SESSION_ID` only; a Kiro-exported
session variable is a CONFIRM recon item. Component-owned user data lives
under `~/.kiro/` beside the surfaces above.

## Deferred until recon

Kiro analogs that need observed v3 behavior before they can be written: the
session-telemetry runners, hook trust/registration mechanics, the
`permissions.yaml` schema, and the headless `kiro-cli --v3 chat` contract.
Components carry their old wiring's kiro-shaped files and mark the unknowns;
they do not invent v3 behavior.
