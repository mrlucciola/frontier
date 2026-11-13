# ICM

Interpretable Context Methodology provides skills for building workspaces and
executing their stages. The current detection hook recognizes a root `CONTEXT.md`
and a numbered `stages/` directory. Workspace execution rules live with the skills
and the workspace's own contracts.

| Work | Start here |
| --- | --- |
| Maintain the component or run its checks | [Development instructions](AGENTS.md) |
| Build or restructure a workspace | [ICM architect skill](skills/icm-architect/SKILL.md) |
| Execute a stage, inspect status, or run setup | [ICM run skill](skills/icm-run/SKILL.md) |
| Review the former Claude installer workflow | [Historical setup guide](INSTALL.md) |

## Sources

- ICM paper, arXiv:2603.16021, and [methodology repository](https://github.com/RinDig/Interpretable-Context-Methodology).
- [ICM architect upstream](https://github.com/RinDig/icm-architect), with local pin and maintenance rules in [VENDOR.md](skills/icm-architect/VENDOR.md).
