# pm

Ticket store for agent work: plain files that live in each repository under `.pm/`.

pm is being rebuilt as the event-log pm described in [the design](/pm/docs/design.md).
The installed `pm` stays the frontier one in `~/frontier/runtime-tools/pm` until the
operator's cutover; the new pm is not on `PATH` until then.

`pm/v2/` holds the ported pm, kept for reference until this epic's last ticket deletes
it. It is not run, and nothing new is built on it.

## Routes

| Document | Read when |
| --- | --- |
| [Design of the new pm](/pm/docs/design.md) | Building or judging any verb, event or output |
| `pm/tests/t/` and `pm/tests/run_transcripts.py` | Checking a build against the transcripts that gate it |
| [Maintenance](/pm/AGENTS.md) | Changing code or tests here |
| [Setup](/pm/INSTALL.md) | Installing, verifying, disabling or removing |
| [Cut list of the port](/pm/v2/docs/cut-list.md) | Deciding whether a verb, flag or config key of the old store belongs |
| [Store format, spec v2](/pm/v2/docs/spec/v2/SPEC.md) | Reading the old `.pm/` format, as import does |

Supported providers are recorded here once the instruction-delivery work lands.
