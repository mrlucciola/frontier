# Quiz maintenance

`skills/adaptive-quiz/scripts/quiz.py` owns question selection, grading, answer
history, and profile output. The skill owns presentation and learner interaction.

| Change | Read |
| --- | --- |
| Selection, grading, persistence, or profile | [Quiz CLI](skills/adaptive-quiz/scripts/quiz.py) and [tests](tests/test_quiz.py) |
| Question-bank format or concept identity | [Catalog](skills/adaptive-quiz/catalog.json) and its checks in [test_quiz.py](tests/test_quiz.py) |
| Question presentation, hints, or learner interaction | [Adaptive quiz skill](skills/adaptive-quiz/SKILL.md) and [workflow](skills/adaptive-quiz/references/workflow.md) |
| Provider activation | [Settings fragment](config/settings.quiz.fragment.json) |

Preserve CLI grading and the separation of assisted answers in profile results.
Use temporary `KNOWLEDGE_HOME` directories for validation.

Run the quiz checks from the repository root.

```sh
python3 -B quiz/tests/test_quiz.py
```

The [installer test](tests/test_install.py) refers to a removed `install.py`.
[INSTALL.md](INSTALL.md) records that former workflow. Validate replacement setup
against its actual documented commands when working on activation.
