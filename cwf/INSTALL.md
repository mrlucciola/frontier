# CWF setup for opencode

Python 3.11+ is required. CWF uses only the Python standard library. `cwf/deploy.sh`
links the checkout into opencode's locations and maintains one marked block; it
copies nothing and records nothing. See "Deploy script" in
[contributing](/docs/contributing.md).

## Source to destination

| Source in `cwf/` | Destination |
| --- | --- |
| `skills/cwf-<domain>` (six directories) | `~/.config/opencode/skills/cwf-<domain>`, symlinks |
| `cwf.py` | `~/.local/bin/cwf`, symlink |
| `instructions/opencode.AGENTS.md` | the block between `<!-- CWF:BEGIN -->` and `<!-- CWF:END -->` in `~/.config/opencode/AGENTS.md`; every other byte of that file is kept |

`~/.config/opencode/opencode.json` is never read or written. Observations, task
checkpoints and the discovery cache live under `~/.local/state/cwf`; they are
optional, and deleting them loses only that recorded state.

## Run

```sh
zsh /Users/matthias/projects/frontier-clean/cwf/deploy.sh
```

Run it again after any source edit that adds a skill or changes the block text.
Edits to existing skill files need no run: the links point at the checkout.

## Verify

```sh
ls -l ~/.config/opencode/skills ~/.local/bin/cwf
~/.local/bin/cwf version
```

Start a fresh session and send:

```text
Use @cwf-maintain to list the CWF skills and the CWF block you see in your instructions. Do not change configuration or write task or memory state.
```

Expected: six `cwf-*` skills and the CWF instruction text. opencode's documentation
does not say whether symlinked skill directories are followed; the fresh session
is the only check.

## Remove

```sh
rm ~/.config/opencode/skills/cwf-build ~/.config/opencode/skills/cwf-design ~/.config/opencode/skills/cwf-docs ~/.config/opencode/skills/cwf-maintain ~/.config/opencode/skills/cwf-plan ~/.config/opencode/skills/cwf-product
rm ~/.local/bin/cwf
```

Then open `~/.config/opencode/AGENTS.md` and delete the lines from
`<!-- CWF:BEGIN -->` through `<!-- CWF:END -->`. Removal leaves
`~/.local/state/cwf` in place; delete it only to discard recorded observations and
checkpoints.

## Copied-release leftovers

`~/.agents/skills/cwf-*` links and `~/.local/share/cwf` belong to a copied-release
install that `deploy.sh` does not use or remove. Where they exist, the operator
removes them once:

```sh
rm ~/.agents/skills/cwf-build ~/.agents/skills/cwf-design ~/.agents/skills/cwf-docs ~/.agents/skills/cwf-maintain ~/.agents/skills/cwf-plan ~/.agents/skills/cwf-product
rm -r ~/.local/share/cwf
```
