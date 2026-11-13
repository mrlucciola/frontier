# pm

Ticket store for agent work: one JSONL file per repository under `.pm/`, driven
by `pm ticket <verb>`.

Status: being rewritten into this component. The installed `pm` is still the
one in `~/frontier/runtime-tools/pm` until cutover. Nothing here is on `PATH`.

| Document | Read when |
| --- | --- |
| [Cut list](/pm/docs/cut-list.md) | Deciding whether a verb, flag or config key belongs in the rewrite |
| [Store format, spec v2](/pm/docs/spec/v2/SPEC.md) | Reading or writing `.pm/` files; the format is frozen |
| [Maintenance](/pm/AGENTS.md) | Changing code or tests here |
| [Setup](/pm/INSTALL.md) | Installing, verifying or removing |

Supported providers are recorded here once the instruction-delivery work lands.
