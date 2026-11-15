# ICM

Interpretable Context Methodology provides skills for building workspaces and
executing their stages. A workspace is a directory with a root `CONTEXT.md`, an
`AGENTS.md` entry file and numbered `stages/` folders. Execution and review rules live
in the `icm-run` skill and the workspace's own contracts. Its scripts derive each
stage's state from the files and record review verdicts bound to them.

Providers: OpenCode (skills only) and an earlier Claude Code setup (skills, hook and
instruction section).

| Work | Start here |
| --- | --- |
| Maintain the component or run its checks | [Development instructions](/icm/AGENTS.md) |
| Build or restructure a workspace | [ICM architect skill](/icm/skills/icm-architect/SKILL.md) |
| Execute a stage, review it, inspect status, or run setup | [ICM run skill](/icm/skills/icm-run/SKILL.md) |
| Set up, verify, disable, or remove the OpenCode or Claude Code integration | [Setup guide](/icm/INSTALL.md) |

## Sources

- ICM paper, arXiv:2603.16021, and [methodology repository](https://github.com/RinDig/Interpretable-Context-Methodology).
- [ICM architect upstream](https://github.com/RinDig/icm-architect), with local pin and maintenance rules in [VENDOR.md](/icm/skills/icm-architect/VENDOR.md).
