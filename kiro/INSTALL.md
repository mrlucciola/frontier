# Kiro setup

Kiro CLI 2.x only. `kiro/deploy.sh` refuses to write anything unless
`kiro-cli --version` reports major 2. It links the probe onto PATH and
maintains one marked block; it copies nothing else and records nothing. See
"Deploy script" in [contributing](/docs/contributing.md).

## Source to destination

| Source in `kiro/` | Destination |
| --- | --- |
| `cli/kiro-probe` | `~/.local/bin/kiro-probe`, symlink |
| `instructions/kiro.steering.md` | the block between `<!-- KIRO:BEGIN -->` and `<!-- KIRO:END -->` in `~/.kiro/steering/frontier.md`; every other byte of that file is kept — CONFIRM-IN-B1 (global steering path pending recon) |

The project scope is `<repo-root>/.kiro/`; the global scope is `~/.kiro/`.
Which global directories kiro actually reads (steering, skills) is confirmed
by the B1 recon — lines above touching global paths are CONFIRM-IN-B1.

## Run

```sh
zsh kiro/deploy.sh
```

Refusals: no `kiro-cli` on PATH, or a version whose major is not 2 — both
exit 1 before any write. Run again after any edit to
`kiro/instructions/kiro.steering.md`; the checkout wins.

## Verify (fresh kiro session)

```sh
ls -l ~/.local/bin/kiro-probe
kiro-probe > report.txt   # expect PASS kiro-version 2.17.x and INFO cfg lines
sed -n '/KIRO:BEGIN/,/KIRO:END/p' ~/.kiro/steering/frontier.md
```

Then start a fresh `kiro-cli chat` session and ask which steering files it
loaded: the frontier block above must appear (CONFIRM-IN-B1: the global
steering path is pending recon).

## Remove

```sh
rm ~/.local/bin/kiro-probe
```

Then delete the lines from `<!-- KIRO:BEGIN -->` through `<!-- KIRO:END -->`
in `~/.kiro/steering/frontier.md` (or the whole file if it holds nothing
else). Removal deletes only the probe link and that block; no other kiro or
user data is touched.

## Work machine (paste-only)

Full operator procedure, in order, with commands: [Operator
runbook](/kiro/docs/ops-work-machine.md). Summary: publish with
`python3 -B kiro/tools/mk_sync_branch.py` on `kiro-main` (the branch carries
source files plus `MANIFEST.txt` and `SYNC-*.txt` chunks), push the printed
`git push --force origin kiro-sync`, then at work paste `kiro/tools/APPLY.sh`
first, then `MANIFEST.txt` and every chunk, eyeball chunk sha256s, and run
`sh APPLY.sh <chunks-dir> <target-root>` — it verifies bytes and sha before
any write and prints one PASS/FAIL per file. Recon after apply:
`python3 kiro/cli/kiro-probe`, report pasted back to
`kiro/docs/probe-log/`.
