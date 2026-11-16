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

1. Dev machine, in the checkout:
   `python3 kiro/tools/mk_sync.py --out .tmp/kiro-sync-bundle` prints the
   chunk list with each chunk's sha256.
2. Dev machine: `python3 kiro/tools/mk_sync_branch.py`, then run the push
   command it prints (`git push --force origin kiro-sync`; point `origin` at
   the public repo). The `kiro-sync` branch raw views bootstrap the small
   files, `kiro/tools/APPLY.sh` first.
3. At work: paste `MANIFEST.txt` and the `SYNC-*.txt` contents into one
   directory (verify each chunk's sha256 while pasting), then
   `sh APPLY.sh <chunks-dir> <target-root>` — it verifies bytes and sha
   before writing and prints one PASS/FAIL per file.
4. Restore bits lost in paste:
   `chmod +x kiro/cli/kiro-probe kiro/tools/APPLY.sh kiro/deploy.sh`,
   then recon: `kiro-probe > report.txt` and paste the report back to the
   dev machine for the log in `kiro/docs/probe-log/`.
