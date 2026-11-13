# Quiz maintenance

`skills/adaptive-quiz/scripts/quiz.py` owns question selection, grading, answer
history, and profile output. The skill owns presentation and learner interaction.

| Change | Read |
| --- | --- |
| Selection, grading, persistence, or profile | [Quiz CLI](/quiz/skills/adaptive-quiz/scripts/quiz.py) and [tests](/quiz/tests/test_quiz.py) |
| Question-bank format or concept identity | [Catalog](/quiz/skills/adaptive-quiz/catalog.json) and its checks in [test_quiz.py](/quiz/tests/test_quiz.py) |
| Question presentation, hints, or learner interaction | [Adaptive quiz skill](/quiz/skills/adaptive-quiz/SKILL.md) and [workflow](/quiz/skills/adaptive-quiz/references/workflow.md) |
| Provider activation | [Setup guide](/quiz/INSTALL.md) and [settings fragment](/quiz/config/settings.quiz.fragment.json) |

Preserve CLI grading and the separation of assisted answers in profile results.
Use temporary `KNOWLEDGE_HOME` directories for validation.

Run the quiz checks from the repository root.

```sh
python3 -B quiz/tests/test_quiz.py
```
