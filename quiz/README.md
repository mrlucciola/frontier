# Adaptive quiz

The adaptive-quiz skill presents a fixed multiple-choice bank and records answer
history. The bank contains 24 questions across 12 concepts. The current store is
`~/.claude/knowledge/quiz.sqlite3`, configurable through `KNOWLEDGE_HOME`.

Concept keys match Feynman card slugs, allowing the skill to offer a related open
gap after a missed answer. Each component owns its storage and works independently.

| Work | Start here |
| --- | --- |
| Maintain the CLI, question bank, or component | [Development instructions](AGENTS.md) |
| Conduct a quiz | [Adaptive quiz skill](skills/adaptive-quiz/SKILL.md) |
| Review the former Claude installer workflow | [Historical setup guide](INSTALL.md) |
