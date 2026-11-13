# Feynman

The Feynman skill explains concepts and records evidence, explanations, and open
gaps as concept cards. The `cg` tool owns the store and a prompt hook recalls
relevant cards. The current default store is `~/.claude/concepts/`, configurable
through `CONCEPT_GRAPH_ROOT`.

| Work | Start here |
| --- | --- |
| Maintain the tool, hook, or component | [Development instructions](AGENTS.md) |
| Explain a concept or update a card | [Feynman skill](skills/feynman/SKILL.md) |
| Review design decisions and history | [Design record](docs/design.md) |
| Review the former Claude installer workflow | [Historical setup guide](INSTALL.md) |

## Sources

Adapted from [neurofoo/agent-skills](https://github.com/neurofoo/agent-skills) under
MIT. Attribution is preserved in [NOTICE](skills/feynman/NOTICE).
