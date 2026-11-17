# CWF setup for Kiro CLI v3

Python 3.11+ is required. CWF uses only the Python standard library. `cwf/deploy.sh`
links the checkout into the Kiro v3 surfaces and maintains one marked block; it
copies nothing and records nothing. See "Deploy script" in
[contributing](/docs/contributing.md) and the [surface map](/docs/kiro-branch.md).

## Source to destination

| Source in `cwf/` | Destination |
| --- | --- |
| `skills/cwf-<domain>` (six directories) | `~/.kiro/skills/cwf-<domain>`, symlinks (CONFIRM) |
| `cwf.py` | `~/.local/bin/cwf`, symlink |
| `instructions/kiro.steering.md` | the block between `<!-- CWF:BEGIN -->` and `<!-- CWF:END -->` in `~/.kiro/steering/frontier.md`; every other byte of that file is kept (CONFIRM) |

No other file under `~/.kiro/` is read or written; `permissions.yaml` is never
written by deploy. Observations, task checkpoints and the discovery cache live
under `~/.local/state/cwf`; they are optional, and deleting them loses only
that recorded state.

## Run

```sh
zsh cwf/deploy.sh
```

Run it again after any source edit that adds a skill or changes the block text.
Edits to existing skill files need no run: the links point at the checkout.

## Verify

```sh
ls -l ~/.kiro/skills ~/.local/bin/cwf
~/.local/bin/cwf version
```

Start a fresh `kiro-cli --v3` session and ask it to load the `cwf-maintain`
skill (CONFIRM: the v3 skill-invocation syntax) and to list the CWF skills and
the CWF block it sees in its instructions, changing nothing.

Expected: six `cwf-*` skills and the CWF instruction text. Whether kiro v3
follows symlinked skill directories is unverified; the fresh session is the
only check.

## Remove

```sh
rm ~/.kiro/skills/cwf-build ~/.kiro/skills/cwf-design ~/.kiro/skills/cwf-docs ~/.kiro/skills/cwf-maintain ~/.kiro/skills/cwf-plan ~/.kiro/skills/cwf-product
rm ~/.local/bin/cwf
```

Then open `~/.kiro/steering/frontier.md` and delete the lines from
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
