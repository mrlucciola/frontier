# frontier-clean: self-contained components for Claude Code

Each top-level directory is one component: everything it needs (skills, hooks, tools,
settings fragment, instruction section, tests) plus its own `install.py`. Components
know nothing about each other. Install one, both, or neither.

- **`icm/`** -- Interpretable Context Methodology (Van Clief & McDermott,
  arXiv:2603.16021): one always-loaded instruction, two skills loaded on demand, one
  SessionStart hook. Guide: [`icm/INSTALL.md`](/icm/INSTALL.md).
- **`feynman/`** -- a skill that answers "how or why does X work" questions the Feynman
  way and persists what it learned as cards in a global concept graph at
  `~/.claude/concepts/`; a `cg` tool that owns the store; a UserPromptSubmit hook that
  recalls matching cards in any directory. Guide:
  [`feynman/INSTALL.md`](/feynman/INSTALL.md). Design: `feynman/docs/design.md`.

Design rule: the global layer stays thin. A session that never touches a component
pays one skill description in the skills list and a few milliseconds of shell per
prompt. Nothing else.

## Install

```
git clone <this repo> ~/frontier-clean
python3 ~/frontier-clean/icm/install.py --dry-run && python3 ~/frontier-clean/icm/install.py
python3 ~/frontier-clean/feynman/install.py --dry-run && python3 ~/frontier-clean/feynman/install.py
```

Each installer copies (or with `--link`, symlinks) its files into `~/.claude`, merges
its hook registration and allow rules into `~/.claude/settings.json`, appends its
instruction section to `~/.claude/CLAUDE.md` once, and backs both files up first.
`--uninstall` reverses that (Feynman keeps your cards). Settings hot-reload; a new
skill needs a new session. Follow each component's INSTALL.md for file checks and a
first live test.

## Component layout convention

```
<component>/
  install.py          installs ONLY this component; stdlib, idempotent, --dry-run/--link/--uninstall
  INSTALL.md          clone-to-first-test guide
  instructions/*.md   section(s) appended to the global CLAUDE.md
  skills/<name>/      skill directories, copied under ~/.claude/skills/
  hooks/ or tools/    executables, copied under ~/.claude/hooks/ or ~/.claude/tools/
  config/*.fragment.json  hook registrations + allow rules, merged into ~/.claude/settings.json
  tests/              component-level tests (plain python3, no dependencies)
```

Deployment targets Claude Code only. Other harnesses (Codex, local models) have their
own config surfaces and deployment needs; port a component's files to them separately
rather than growing a shared installer.

## Verify everything

```
python3 ~/frontier-clean/icm/tests/test_hook.py
python3 ~/frontier-clean/icm/tests/test_install.py
python3 ~/frontier-clean/feynman/tools/concept-graph/tests/test_cg.py
python3 ~/frontier-clean/feynman/tests/test_recall_hook.py
python3 ~/frontier-clean/feynman/tests/test_install.py
# expect: OK five times
```

## Sources

- ICM paper: https://arxiv.org/abs/2603.16021; protocol repo:
  https://github.com/RinDig/Interpretable-Context-Methodology; builder skill:
  https://github.com/RinDig/icm-architect (vendored at a pin, see
  `icm/skills/icm-architect/VENDOR.md`)
- Feynman protocol adapted from: https://github.com/neurofoo/agent-skills (MIT; see
  `feynman/skills/feynman/NOTICE`)
