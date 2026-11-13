# Feynman maintenance

`tools/concept-graph/cg.py` owns card storage, indexes, the lexicon, and recall state.
The adjacent `recall.sh` owns the prompt hook's shell fast path.

| Change | Read |
| --- | --- |
| CLI behavior, storage, or recall | [Concept graph tool](/feynman/tools/concept-graph/cg.py) and its [tests](/feynman/tools/concept-graph/tests/test_cg.py) |
| Hook matching or provider registration | [Recall hook](/feynman/tools/concept-graph/recall.sh), [settings fragment](/feynman/config/settings.feynman.fragment.json), and [hook tests](/feynman/tests/test_recall_hook.py) |
| Provider activation | [Setup guide](/feynman/INSTALL.md), [settings fragment](/feynman/config/settings.feynman.fragment.json), and [runtime instruction](/feynman/instructions/feynman.md) |
| Explanation or card workflow | [Feynman skill](/feynman/skills/feynman/SKILL.md), then its relevant schema or protocol reference |
| Historical design rationale | [Design record](/feynman/docs/design.md) |

Use temporary stores through `CONCEPT_GRAPH_ROOT` for validation. Check the CLI and
hook together when changing store paths or recall semantics.

Run the relevant checks from the repository root.

```sh
python3 -B feynman/tools/concept-graph/tests/test_cg.py
python3 -B feynman/tests/test_recall_hook.py
```
