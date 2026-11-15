# ICM maintenance

This directory owns the two workspace skills, the run contract and its state
scripts, the OpenCode setup, and the earlier Claude Code detection hook and
instruction. Read the route for the behavior being changed.

| Change | Read |
| --- | --- |
| Stage execution, review gates, status, or setup | [ICM run skill](/icm/skills/icm-run/SKILL.md), then its relevant command reference |
| Stage state or review evidence | [Shared workspace rules](/icm/skills/icm-run/scripts/workspace.py), [state](/icm/skills/icm-run/scripts/state.py), [record](/icm/skills/icm-run/scripts/record.py) and [their tests](/icm/tests/test_state.py) |
| Workspace construction or upstream templates | [Vendoring contract](/icm/skills/icm-architect/VENDOR.md) |
| OpenCode activation | [Setup guide](/icm/INSTALL.md) and [its test](/icm/tests/test_opencode_setup.py) |
| Claude Code activation or detection | [Setup guide](/icm/INSTALL.md), [detection hook](/icm/hooks/icm-detect.sh), [hook tests](/icm/tests/test_hook.py), [settings fragment](/icm/config/settings.icm.fragment.json), and [runtime instruction](/icm/instructions/icm.md) |

Keep workspace execution and review rules in the `icm-run` skill. Follow the
vendoring contract for changes under `skills/icm-architect/`. `state.py` and
`record.py` share `scripts/workspace.py` because one writes the review binding the
other checks, and separate copies would drift.

The Claude Code hook and instruction still name `CLAUDE.md` as the entry file, which
contradicts the run skill's `AGENTS.md` entry. They are kept as they are until the
decision on retiring the Claude Code delivery.

Run the component checks from the repository root.

```sh
python3 -B icm/tests/test_state.py
python3 -B icm/tests/test_opencode_setup.py
python3 -B icm/tests/test_hook.py
```
