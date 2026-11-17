# Adaptive quiz

The adaptive-quiz skill presents a fixed multiple-choice bank and records answer
history. The bank contains 24 questions across 12 concepts. The current store is
`~/.kiro/knowledge/quiz.sqlite3`, configurable through `KNOWLEDGE_HOME`.

Concept keys match Feynman card slugs, allowing the skill to offer a related open
gap after a missed answer. Each component owns its storage and works independently.

| Work | Start here |
| --- | --- |
| Maintain the CLI, question bank, or component | [Development instructions](/quiz/AGENTS.md) |
| Conduct a quiz | [Adaptive quiz skill](/quiz/skills/adaptive-quiz/SKILL.md) |
| Set up, verify, disable, or remove the Kiro CLI v3 integration | [Setup guide](/quiz/INSTALL.md) |
