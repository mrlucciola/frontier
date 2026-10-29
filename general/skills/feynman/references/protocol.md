# Full protocol (`/feynman <topic>`)

Adapted from the four-step Feynman template in neurofoo/agent-skills (MIT). Changes
from upstream: a recall step, a "where it breaks" line on every analogy, a "how to
close" column and evidence classes for gaps, a confidence rating, and persistence.

Print the sections in this order. Keep each short; the whole document should fit on
one screen for a simple concept.

```markdown
# <Concept>

Recalled: <none | card <slug>, status, confidence, open gaps listed>

## 1. Simple explanation
<under 120 words, no undefined term, bright-12-year-old bar>

**Analogy:** <one everyday analogy>
**Where it breaks:** <one sentence>

## 2. Gaps
| Gap | What I said | What I am not sure about | How to close |
|---|---|---|---|
| ... | ... | ... | read code / run / source / ask |

| Term | Can I explain it simply? | One-line definition |
|---|---|---|
| ... | yes / partially / no | ... |

## 3. Closing the gaps
### Gap 1: <topic>
- Question: ...
- Evidence: <class> — <file:line@sha | command and output | URL | reasoning>
- Now I can say: ...
(repeat; a gap with only reasoning behind it stays OPEN with a due date)

## 4. Refined explanation
<rewrite with gaps closed, still under 120 words>

**Improved analogy:** ... **Where it breaks:** ...

**Key takeaways**
1. ...
2. ...
3. ...

**Pitch (30 seconds):** ...

**Confidence:** N/5 because <one clause>

## Card
<cg commands run, one per line, and their one-line results>
```

Evidence classes, strongest first: `verified-in-code`, `ran`, `source-cited`,
`reasoned`, `user-declared`. A codebase question closes gaps with the first three only.

Persistence checklist after section 4:

1. `cg add` (new) or `cg write` + `cg set <slug> confidence=N` (existing).
2. `cg gap <slug> add "<q>"` for every open gap; `cg gap <slug> close "<q>" --evidence <class> --ref <ref>` for every closed one.
3. `cg link <slug> <depends_on|related|contrasts_with|instance_of> <other>`; add the neighbour card first if it does not exist (`--allow-empty` is acceptable for a stub you name but do not explain).
4. `cg anchor <slug> --path <file> --line N` for each code claim, run from inside that repo.
