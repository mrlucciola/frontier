# pm maintenance

Standard-library Python at `/usr/bin/python3`. Build to
[the design](/pm/docs/design.md) and the
[component principles](/docs/component-principles.md).

The gate is the transcripts in `tests/t/`.

Run from the repository root.

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending
```

A verb with no file under `tools/verbs/` is reported unbuilt by the dispatcher. A built
verb that reaches a part a later ticket owns calls `store.unbuilt(<name>)`, and
`--allow-pending` must stay at `failed 0`.

| Work | Read |
| --- | --- |
| Any verb, event or output | [Design](/pm/docs/design.md), then the transcripts in `tests/t/` |
| A transcript or the design that looks wrong | Stop and report what looks wrong. Never edit the design, `tests/t/` or `tests/fixtures/` |
| The ported pm in `pm/v2/` | Read-only reference; do not edit or run it |

After a docs change, run `python3 -B docs/check_structure.py`.
