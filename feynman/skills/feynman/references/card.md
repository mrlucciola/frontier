# Card schema

One file per concept at `~/.kiro/concepts/cards/<slug>.md`. Written only by `cg`.

```markdown
---
name: wal-mode
title: SQLite WAL mode
aliases: [write-ahead log, wal]
scopes: [global, /Users/me/frontier]
status: understood            # learning | understood | stale (derived, see below)
confidence: 4                 # 1..5, self-rated after the pitch
epistemic: verified-in-code   # strongest evidence class among closed gaps (derived)
grade: 4                      # only after `cg grade`
edges:
  depends_on: [sqlite-journal]
  related: [graph-memory-store]
  contrasts_with: [rollback-journal]
anchors:
  - repo: /Users/me/frontier
    path: hooks/graph-memory/schema.sql
    sha: 5b2dbee
    line: 10
gaps:
  - q: Why do readers never block writers in WAL?
    status: closed
    opened: 2026-10-29
    due: 2026-11-05
    closed: 2026-10-29
    evidence: source-cited
    ref: https://sqlite.org/wal.html
  - q: What happens to a WAL file on an unclean shutdown?
    status: open
    opened: 2026-10-29
    due: 2026-11-05
created: 2026-10-29T10:00:00Z
updated: 2026-10-29T10:12:00Z
---

## Simple explanation
Under 120 words.

## Analogy
One analogy.

## Where it breaks
One sentence.

## Pitch
The 30-second version.

## Log
- 2026-10-29 created (session 2335381c)
- 2026-10-29 gap closed (source-cited): Why do readers never block writers in WAL?
```

## Field rules

| Field | Who sets it | Rule |
|---|---|---|
| `scopes` | `cg add --scope`, `cg anchor` | `global` means recalled everywhere. A path means recalled when the session's cwd is inside it. `--local-only` drops `global`. Anchoring adds the repo to scopes. |
| `status` | derived | `learning` while a gap is open or confidence is under 3; `understood` otherwise; `stale` only from `cg check` (anchor drift, or a gap more than 30 days past due). Stale clears when the card is re-anchored or confidence is set again. |
| `confidence` | you, after the pitch | 1 = I used words I cannot define; 3 = right but a vague spot; 5 = a child would get it and I can point at evidence. |
| `epistemic` | derived | strongest class among closed gaps; `reasoned` when nothing is closed. |
| `gaps[].due` | `cg gap add --due`, default +7 days | a due gap is printed first by recall and by `cg gaps --due`. |
| `anchors[].sha` | `cg anchor` | the repo HEAD at anchoring; `cg check` marks drift when the file changed since. |
| `edges` | `cg link` | `depends_on` (prerequisite), `related`, `contrasts_with`, `instance_of`. Reverse edges are derived into the index. |

## Evidence classes

`verified-in-code` > `ran` > `source-cited` > `reasoned` > `user-declared`. The first
three require `--ref`. A repo question may close a gap only with the first three.

## Derived files

`index.json` (card summaries, reverse edges) and `lexicon.txt` (match tokens for the
prompt hook) are rebuilt on every write and by `cg index`. `log.jsonl` records every
write with the session id. `.state/` holds per-session recall dedup and is garbage
collected after seven days.
