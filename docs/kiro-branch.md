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

## Open v3 questions (close them at the work machine)

- Which global paths the v3 runtime reads (steering, skills, `~/.kiro/`
  layout) and whether it auto-loads `AGENTS.md`.
- Agent definition format and location the runtime actually honors
  (markdown agents, project vs global scope).
- Exit behavior of headless `kiro-cli --v3 chat` runs, as far as the pm and
  wt hooks care.
