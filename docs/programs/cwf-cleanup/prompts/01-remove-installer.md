# cwfcl-01 remove the cwf installer, conform cwf to the deploy standard fc-6441eb

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/cwf-cleanup/prompts/01-remove-installer.md)"
```

The launch line submits this file as the first message of a fresh session rooted at `~/projects/frontier-clean`; nothing to paste.

---

# cwfcl-01 remove the cwf installer, conform cwf to the deploy standard fc-6441eb

`docs/programs/cwf-cleanup/prompts/01-remove-installer.md`

## Outcome

cwf deploys by `cwf/deploy.sh` alone: symlinks into the checkout plus one marked block. The installer and everything written for it (about 1,000 lines) is gone, cwf passes `docs/check_structure.py` with no exemption, and the cwf tests pass. Ticket: `pm ticket show fc-6441eb`.

## Rulings already made (do not reopen)

- No copied release, version pointer, manifest, checksum, receipt or install journal. See "One maintained source" in `README.md` and "Deploy script" in `docs/contributing.md`; read both first.
- Out of scope, left exactly as they are: observations, task checkpoints, the worktree helpers, the discovery cache, the checkpoint version pin (`cwf/cwf/state.py`, `discovery.py`, `operations.py`, `contracts.py`, `schemas/`, `fixtures/`).
- `cwf version` stays. `scripts/author_content.py` stays as the generator of skills and patterns: change skill or pattern text there, then run it.

## Precondition

```sh
git --no-pager -C /Users/matthias/projects/frontier-clean ls-files cwf/deploy.sh cwf/instructions/opencode.AGENTS.md
# expect: both paths printed
```

If either is missing, stop and report "operator has not committed cwf/deploy.sh"; do not create or commit them yourself.

## Work

Run `wt start fc-6441eb --as claude` from the main checkout, then edit and commit only under `/Users/matthias/projects/frontier-clean/.worktrees/fc-6441eb` (WT below).

1. Remove with `git -C WT rm`: `cwf/cwf/installer.py`, `cwf/scripts/package.py`, `cwf/tests/test_pilot.py`, `cwf/prompts/INSTALL-AND-QUALIFY.md`. Before each, `rg -n '<name>' WT` and fix every inbound reference.
2. `cwf/cwf/cli.py`: remove the `install`, `upgrade`, `rollback`, `uninstall`, `enable`, `disable` and `doctor` commands: the `doctor()` function, their dispatch branches, their names in `MANAGEMENT` and in the argparse choices, the `installer` import, and `--config-root` if nothing else reads it.
3. `cwf/tests/test_cwf.py`: delete the `InstallTests` class and any other test that calls the installer. Every remaining test stays green and unchanged.
4. `cwf/deploy.sh`: bring it to the template in "Deploy script": `here="${0:A:h}"` in place of the hard-coded path, the missing-snippet guard before the first write, the byte-exact read and write pair (sentinel `x`, `print -rn`), no `chmod`, no `cwf version` call. Marker name stays `CWF`. Under 60 lines.
5. Add `cwf/tests/test_deploy.py`, black-box: copy nothing, run `zsh WT/cwf/deploy.sh` twice with `HOME` set to a temporary directory whose `.config/opencode/AGENTS.md` already holds other text, and assert the six skill links and `.local/bin/cwf` point into the checkout, the block appears once, the bytes outside the markers are unchanged, and the second run changes nothing. Never run `deploy.sh` with the real `HOME`.
6. Docs. `cwf/INSTALL.md` becomes the short form "Documentation and validation" describes: source-to-destination table, the run command, verification in a fresh opencode session, the exact removal commands, and one short section for leaving the old install (remove the six `~/.agents/skills/cwf-*` links, delete `~/.local/share/cwf` and `~/.local/state/cwf`; operator runs these, you do not). Remove or rewrite to match: `docs/OPERATIONS.md` sections 2 and 8; `docs/SPECIFICATION.md` status line, section 4 table and section 12; `cwf/README.md` (install plan, doctor, ZIP sharing); `cwf/AGENTS.md` (the "owns" sentence, the "every regular file here is copied into the installed release" paragraph, the fc-2e70b4 paragraph); `docs/PLATFORM.md` lines on `~/.agents/skills` links and the local installer. In `docs/VALIDATION.md` add one sentence saying the installer results are historical; do not rewrite the record.
7. Generator text in `cwf/scripts/author_content.py`: the `maintain` steps that mention `doctor` and the installer, and the `TOOLS` paragraphs that mention the launcher, a staging bundle and `doctor`. Then `python3 -B WT/cwf/scripts/author_content.py` and confirm with `git -C WT status --short` that only the intended skill and pattern files changed.
8. Conformance: add `cwf/CLAUDE.md` containing exactly `@AGENTS.md`; make the run paragraph in `cwf/AGENTS.md` read "Run the cwf checks from the repository root." above `python3 -B cwf/tests/test_cwf.py` and `python3 -B cwf/tests/test_deploy.py`; delete both `cwf` rows from the Exemptions table in `docs/contributing.md`.
9. Last commit: `git -C WT rm -r docs/programs/cwf-cleanup` (the ticket holds the record).

## Leave alone

`cwf/.local/` (untracked operator files), `cwf/config/global-entry.md` (report whether anything still references it), branch `fc-122dd5`, every path outside WT, and the real `~/.config`, `~/.local` and `~/.agents`.

## Validation (one plain command each, full output read)

```sh
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-6441eb/cwf/tests/test_cwf.py
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-6441eb/cwf/tests/test_deploy.py
python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-6441eb/docs/check_structure.py
# expect: check_structure: ok (7 components, 0 exempted)
rg -n "installer|install plan|install apply|doctor|releases/|rollback|uninstall|package\.py" /Users/matthias/projects/frontier-clean/.worktrees/fc-6441eb/cwf
# expect: hits only in docs/VALIDATION.md and docs/DEVIATIONS.md history; explain any other
```

## Finish

Commit explicit paths in focused commits, then from the main checkout `wt finish fc-6441eb --findings <ids or none> --note "<what was removed, validation lines, what was not proven>"`. Add a note to `fc-42e0f4` saying its two open items (the CLAUDE.md shim and the test working directory) are closed by fc-6441eb, and a note to `fc-122dd5` saying its branch now also conflicts with the removed installer tests. Do not close either.

## Stop and report instead of proceeding when

- the precondition fails;
- a remaining test fails for a reason that needs a decision about an out-of-scope feature;
- two validation attempts fail without a diagnosis;
- finishing would require editing anything under "Leave alone".

End with the lines removed per file group (code, tests, docs), the four validation results, every finding and where it was written, and `Ticket: fc-6441eb <status>`.
