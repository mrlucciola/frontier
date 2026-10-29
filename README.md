# frontier-clean: a thin global layer for Claude Code

Two additions to the global agent config, installed into `~/.claude` by one script:

- **ICM** (Interpretable Context Methodology, Van Clief & McDermott, arXiv:2603.16021):
  one always-loaded instruction, two skills loaded on demand, one SessionStart hook.
- **Feynman + concept graph**: a skill that answers "how does X work" questions the
  Feynman way and persists what it learned as cards in a global concept graph; a tool
  (`cg`) that owns the store; a UserPromptSubmit hook that recalls matching cards in any
  directory. Design and rationale: `docs/feynman/design.md`.

Design rule for both: the global layer stays thin. A session that never touches a
skill pays one skill description in the skills list and a few milliseconds of shell per
prompt. Nothing else.

## Layout

```
general/                              provider-neutral
  instructions/icm.md                 section for the global CLAUDE.md / AGENTS.md
  instructions/feynman.md             section for the global CLAUDE.md / AGENTS.md (3 lines)
  skills/icm-architect/               upstream skill, vendored at a pin (VENDOR.md)
  skills/icm-run/                     executor skill for existing ICM workspaces
  skills/feynman/                     SKILL.md, references/{protocol,card}.md, routing-corpus.jsonl, NOTICE
  tools/concept-graph/cg.py           the concept graph engine (stdlib, python 3.9+) + tests/
vendor/
  claude/install.py                   installer: copy or link, merge settings, append instructions
  claude/settings.fragment.json       hook registrations + Bash allow rules, Claude Code schema
  claude/hooks/icm-detect.sh          SessionStart: ICM workspace detection
  claude/hooks/concept-graph/recall.sh  UserPromptSubmit: concept recall, shell fast path
  codex/README.md                     what applies to Codex and what is unverified
  omlx/README.md                      unknown config model; what to verify
tests/                                test_hook.py, test_recall_hook.py, test_install.py
docs/feynman/design.md                assessment, abstraction, 8/9/10 design
```

## Install (on the target machine)

```
git clone <this repo> ~/frontier-clean
python3 ~/frontier-clean/vendor/claude/install.py --dry-run   # read what it will do
python3 ~/frontier-clean/vendor/claude/install.py             # copy into ~/.claude
```

What that does: skills to `~/.claude/skills/`, the tool to `~/.claude/tools/concept-graph/`,
hooks to `~/.claude/hooks/`, the hook registrations and allow rules merged into
`~/.claude/settings.json` (backup first), the two instruction sections appended to
`~/.claude/CLAUDE.md` once (backup first), and `~/.claude/concepts/` created.
`--link` symlinks instead of copying so `git pull` updates the live files;
`--uninstall` removes everything it installed and keeps your cards.

Verify:

```
python3 ~/frontier-clean/tests/test_install.py
python3 ~/frontier-clean/tests/test_recall_hook.py
python3 ~/frontier-clean/general/tools/concept-graph/tests/test_cg.py
python3 ~/.claude/tools/concept-graph/cg.py status
```

Then, in Claude Code: `/feynman <any concept>`. Open a new session in another
directory and ask about that concept; a `memory:` block with the card should precede
your prompt, and the skill should refine the card instead of starting over.

Settings hot-reload; no restart is needed for hooks or permissions. Skills are read at
session start, so a brand-new skill needs a new session.

## How the pieces fit

| Moment | What runs | Cost when idle |
|---|---|---|
| session start | `icm-detect.sh`: silent unless cwd is an ICM workspace | ~2 ms |
| every prompt | `recall.sh`: grep the prompt against `~/.claude/concepts/lexicon.txt`; on a hit, `cg.py hook-recall` verifies phrases, filters by scope, dedups per session, prints at most 2 cards in 1,200 chars | ~5 ms, 0 tokens |
| explanatory question or `/feynman` | the `feynman` skill: recall, explain, audit gaps, close with evidence, refine, persist through `cg` | skill text only when it fires |
| any time | `cg` subcommands: `recall show add write set gap gaps link anchor check neighbors export grade status index` | none |

Store: `~/.claude/concepts/cards/<slug>.md` is the source of truth; `index.json` and
`lexicon.txt` are derived; `log.jsonl` records writes. Schema: `general/skills/feynman/references/card.md`.

## Codex and other harnesses

The instructions, skills, tool and store are provider-neutral. `vendor/codex/README.md`
lists the manual steps and the (unverified) hook registration. omlx: instruction only,
until `vendor/omlx/README.md`'s questions are answered.

## Sources

- ICM paper: https://arxiv.org/abs/2603.16021; protocol repo: https://github.com/RinDig/Interpretable-Context-Methodology; builder skill: https://github.com/RinDig/icm-architect
- Feynman skill the protocol is adapted from: https://github.com/neurofoo/agent-skills (MIT; see `general/skills/feynman/NOTICE`)
