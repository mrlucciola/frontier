# Operator runbook: sync and recon at the work machine

Run top to bottom. Steps 0 runs on the dev machine; 1–9 run at work, in
order, each time you sync. Placeholders: `OWNER`/`REPO` = your public GitHub
repository; the branch is always `kiro-sync`.

Assumes a POSIX terminal with `base64`, and `shasum -a 256` or
`shasum`→`sha256sum`. `APPLY.sh` checks these itself and exits 2 with a
usage line when missing.

## 0. Dev machine — publish a sync

```sh
cd /Users/matthias/projects/frontier-clean/.worktrees/trunk-kiro
python3 -B docs/check_structure.py
python3 -B kiro/tests/test_sync.py
python3 -B kiro/tests/test_deploy.py
python3 -B kiro/tests/test_probe.py
python3 -B kiro/tools/mk_sync_branch.py
```

`mk_sync_branch.py` prints the `kiro-sync` commit, then one
`<name> <sha256> <bytes>` line per bundle file (`MANIFEST.txt`, `SYNC-001.txt`
...). **Save those lines** — step 4 compares against them. Then push:

```sh
git push --force origin kiro-sync
```

## 1. Work machine — bundle folder

```sh
mkdir -p ~/kiro-bundle && cd ~/kiro-bundle
```

## 2. Paste the verifier first

Open in the browser (raw view only, never the rich GitHub file view):

```text
https://raw.githubusercontent.com/OWNER/REPO/kiro-sync/kiro/tools/APPLY.sh
```

Select-all, copy, then in the terminal:

```sh
cat > APPLY.sh
# paste, press Return, then Ctrl-D
```

Verify the paste against its manifest record (both are pasted, so a
consistent double-corruption is not caught here; it is caught later by
`git diff` when you compare with the dev machine, and the risk window is
one file of shell):

```sh
grep ' kiro/tools/APPLY.sh$' MANIFEST.txt   # after step 3
shasum -a 256 APPLY.sh                     # hashes must match
```

## 3. Paste MANIFEST and every chunk

Paste `MANIFEST.txt` the same way, then every `SYNC-NNN.txt` listed in step
0's saved output. Hygiene, per file:

- raw view (`raw.githubusercontent.com`), Select All, copy;
- `cat > SYNC-001.txt`, paste, Return, Ctrl-D — a terminal, never a text
  editor (smart quotes and soft wraps corrupt base64);
- keep the final `END ...` line intact; a stray trailing blank line is
  harmless, a joined or truncated line is not.

## 4. Eyeball whole-chunk hashes before applying

```sh
shasum -a 256 MANIFEST.txt SYNC-*.txt
```

Compare with the lines saved in step 0. On mismatch, re-paste that one file
and re-check; only proceed when all match.

## 5. Apply

```sh
sh APPLY.sh ~/kiro-bundle ~/frontier; echo "exit=$?"
```

Expect one `PASS <path>` line per file and `exit=0`. For each `FAIL <path>`:

```sh
grep -l "BEGIN <path> " SYNC-*.txt   # the chunk holding it
```

re-paste that chunk, re-run step 4 for it, re-run APPLY (idempotent —
safe to run again any number of times).

## 6. Restore executable bits lost in paste

```sh
cd ~/frontier
chmod +x kiro/cli/kiro-probe kiro/tools/APPLY.sh kiro/deploy.sh
```

## 7. Recon (batch 1; this is the point of the first sync)

```sh
kiro-cli --version                       # must report 2.x (expect 2.17)
python3 kiro/cli/kiro-probe > ~/probe-$(date +%Y%m%d).txt; echo "exit=$?"
```

Carry the probe file and the version line back to the dev machine (paste
into chat, or email if permitted). On the dev machine save as
`kiro/docs/probe-log/<YYYY-MM-DD>-kiro<version>.txt` on `kiro-main` and
commit. Answer `--smoke` only when the report shows headless looks viable.

## 8. Optional: local git (required before pm/wt work at work)

```sh
git --version && cd ~/frontier && git init -q \
  && git add -A && git commit -qm "frontier kiro-sync snapshot"
```

If git is absent or blocked: pm and wt cannot run here; record that in the
probe log and use only cwf/icm guidance.

## 9. Deploy — only after batch 2 merges (B2 lands component kiro sections)

```sh
cd ~/frontier
zsh kiro/deploy.sh    # refuses first, naming versions, if kiro-cli is not 2.x
zsh pm/deploy.sh && zsh wt/deploy.sh && zsh cwf/deploy.sh && zsh icm/deploy.sh
```

Then reopen kiro and run `kiro-probe` again; the diff of probe reports is
the deploy verification. Removal commands: `kiro/INSTALL.md`.
