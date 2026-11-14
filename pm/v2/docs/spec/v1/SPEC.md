# PM store spec v1

Status: DRAFT (cl-4e84d3, epic cl-2121e0). Frozen when tagged `pm-spec/v1`.
Normative for: the v1 store directory layout, `config.json`, every row of
`issues.jsonl`, the archive, and the observable contracts of `pm ticket validate`,
`pm ticket upgrade`, `pm ticket init`, `pm ticket adopt`, `pm ticket archive`. Protocol
semantics (claim, file, close, readiness) stay in the pm skill's protocol (`skills/pm`,
cl-00b6e9); this document only fixes what a validator can check without reasoning.

Words: MUST / MUST NOT are checked by `validate` (each maps to an invariant in
`invariants.md`). SHOULD is guidance the write path follows but `validate` does not
enforce.

## 1. Versions

- A store declares its version in `config.json` as `spec_version` (integer >= 1).
- **v0** is the name for the pilot store shape that predates this spec:
  `{"prefix": "<p>", "version": 1}` with rows as written by `ticket_core` before
  2026-09-15. `validate` recognises v0 and reports exactly one step: run
  `pm ticket upgrade`. `upgrade` v0 -> v1 is `spec/v1/migrate_v0_to_v1.py`.
- The spec for version N lives at `spec/vN/` in `~/frontier/runtime-tools/pm/ticket`: `SPEC.md`,
  `config.schema.json`, `ticket.schema.json`, `invariants.md`, `importers.md`,
  `CHANGELOG.md`, `migrate_v<N-1>_to_vN.py`. The freezing commit is tagged `pm-spec/vN`.
- **Bump rule.** N+1 exists only when a store that validates under vN would fail under
  vN+1 (a field added as required, removed, renamed, an enum narrowed, a path or name
  changed). Adding an optional field, a new label convention, or a new verb does not
  bump the spec; it lands in `CHANGELOG.md` under the current version.
- `ticket_core.PROJECTION_VERSION` (the L2 read contract consumed by board, overview and the
  GUI) is independent of `spec_version`. A spec bump SHOULD keep the projection stable
  by adapting inside `ticket_core.project()`; if the projection must change, bump both and
  say so in both changelogs.

## 2. Layout

v1 stores live in `.backlog/`.

```
<repo>/.backlog/
  config.json              MUST   see section 3
  issues.jsonl             MUST   see section 4 (may be empty)
  lock                     MAY    flock target; content irrelevant; SHOULD exist
  migrate-report.md        MAY    written by adopt/migrate; not validated
  upgrade-<from>-to-<to>.md MAY   written by upgrade; not validated
  archive/                 MAY    gitignored except the index; see section 6
    archive-index.jsonl    MAY    tracked
    issues-<yyyy>.jsonl    MAY    rows moved out by `pm ticket archive`
    <source>-<yyyymmdd>/   MAY    moved artifacts, untouched
```

No other entries MUST exist under the v1 store directory. Unknown files or directories
are reported by `validate` (I-01) so that stray state cannot hide there; `.tmp` and
`*.tmp` are tolerated as in-flight write artifacts.

The store is found by walking up from cwd to the first directory containing the v1
store directory, never crossing a `.git` boundary upward once one has been passed (a
nested repo never resolves to its parent's store, R1). One boundary is crossed
SIDEWAYS, not upward: a directory whose `.git` is a *file* is a linked git worktree,
and its own v1 store directory (a checked-out copy of the ticket branch) is never the
store -- discovery resolves the worktree to its main checkout (via the `gitdir:`
pointer and `git rev-parse --git-common-dir`) and uses the main checkout's v1 store
directory. A directory whose `.git` is a *dir* with no v1 store directory still yields
no store (R1 unchanged).

## 3. `config.json`

Schema: `config.schema.json`. Exactly these keys, no others:

| key | type | rule |
|---|---|---|
| `spec_version` | integer | equals the version being validated (I-02) |
| `prefix` | string | `^[a-z][a-z0-9]{1,7}$`; every row id starts with `<prefix>-` (I-03) |

`prefix` uniqueness across repos is a workspace check (section 8), not a store check.

## 4. Rows in `issues.jsonl`

One JSON object per line, UTF-8, `\n` terminated, keys sorted, `ensure_ascii=false`.
Blank lines are tolerated on read and removed on the next write. Schema:
`ticket.schema.json`. A row has exactly these 13 keys (I-04):

| key | type | rule |
|---|---|---|
| `id` | string | `^<prefix>-[0-9a-f]{6,11}$`, unique in the file and in the archive index (I-03, I-05) |
| `title` | string | non-empty, single line, <= 200 chars (I-06) |
| `body` | string | any, may be empty |
| `kind` | enum | `task` or `epic` |
| `status` | enum | `open`, `claimed`, `done-unmerged`, `closed` |
| `priority` | integer | 0..4 |
| `assignee` | string or null | non-null iff `status == claimed` for tasks (I-07); null on epics (I-08) |
| `parent` | string or null | an existing row of `kind == epic`, no parent cycle (I-09) |
| `labels` | string[] | sorted, unique, each `^[a-z0-9][a-z0-9:_./-]*$` (I-10) |
| `edges` | object[] | each `{"type": <blocks,related,discovered-from>, "to": <existing id>}`; no self edge; no `blocks` cycle (I-11..I-13) |
| `notes` | object[] | each `{"ts": <timestamp>, "text": <string>}`, non-decreasing `ts` (I-14) |
| `created` | timestamp | `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` |
| `updated` | timestamp | same form, `>= created` (I-15) |

Reserved labels (validated only for shape, not meaning): `semaphore`, `xrepo`,
`imported:<yyyymmdd>`, `mao`, `mao:<run>:<T-nnn>`, `mao-run:<id>`, `mao-phase:<id>`,
`archive-pointer`, and the R4 types `backlog`, `failure-report`, `wishlist`, `question`.

## 5. `validate` contract

```
pm ticket validate [--repo <path>] [--workspace <file>] [--json]
```

- Exit 0: prints `OK spec_version=<N> rows=<n> archive=<present|absent>` on one line.
- Exit 1: prints `FAIL spec_version=<N or v0 or unknown> problems=<k>` then `k` numbered
  steps, one per problem, each on one line in the form
  `<n>. <file>[:<line>][ (<id>)]: <what is wrong> -> <exact fix>`.
  Steps are ordered by file, then line, then invariant id, so two runs on the same
  store print identical output. A `-> run: pm ticket <verb> ...` fix is an action an
  agent MAY take without further reasoning (F6); a `-> operator:` fix MUST be
  surfaced, not taken.
- Exit 2: no store found, or a file that MUST exist is unreadable or not valid JSON.
  One line naming the path and the parse error; no steps.
- `--json` emits `{"ok": bool, "spec_version": N|"v0"|null, "problems": [{"file", "line",
  "id", "invariant", "message", "fix", "agent_may_fix": bool}]}` and the same exit codes.
- `validate` never writes. It never invokes `lint` semantics beyond the invariants list;
  `pm ticket lint` remains the legacy alias and prints the same steps.
- Archive: a missing `archive/` or an index row whose `path` does not resolve is not a
  problem (R2 amendment). A present archive is checked for shape (I-16..I-18).

## 6. Archive

- `archive-index.jsonl`: one row per archived item, keys sorted:
  `{"id": <string>, "title": <string>, "source": <string>, "closed": <timestamp or null>,
  "path": <relative to the v1 store directory's archive/>, "archived": <timestamp>,
  "meta": <object>}`. `id` is the source system's id (`T-401`, `PARK-...`, a ticket id)
  qualified as `<source>:<id>` when the source is not this store. `meta` is free-form
  provenance (`run_id`, `plan_commit_ref`, `superseded_by`, `resolution`).
- `issues-<yyyy>.jsonl`: rows moved out by `pm ticket archive --closed-before`,
  unchanged, grouped by the year of `updated`. Not read by any verb unless `--all`.
- `<source>-<yyyymmdd>/`: artifacts moved by `pm ticket migrate`, byte-identical, modes
  preserved where the filesystem allows.
- Gitignore lines written by `init`/`adopt` (R2 amendment): the v1 store directory's
  `archive/*` and `!archive/archive-index.jsonl`.

## 7. `upgrade` contract

```
pm ticket upgrade [--repo <path>] [--workspace <file>] [--to <N>] [--dry-run]
```

1. `validate` at the store's declared version (v0 accepted). Any problem other than
   "store is v0" aborts with the same numbered steps, exit 1.
2. Copy the v1 store directory to `<store-dir>.upgrade-<pid>/` inside the repo; apply
   `migrate_v<k>_to_v<k+1>.py` in sequence on the copy, each one a pure function of the
   copy's files; after each step run `validate` at `k+1` on the copy.
3. On success swap the copy over the original under the store lock, leaving
   `upgrade-<from>-to-<to>.md` in the store directory (what changed, row counts before
   and after). On any failure remove the copy, print the failing step, exit 1,
   original untouched.
4. `--dry-run` performs 1 and 2 and prints the report without swapping.

`upgrade` never rewrites rows beyond what the migration script states, never reorders
rows, never changes `created`.

## 8. Workspace fan-out (R1)

`--workspace <file>` reads a `.vscode/*.code-workspace` JSON (comments and trailing
commas tolerated), resolves each `folders[].path` relative to the file, keeps those that
contain both `.git` and the v1 store directory, and runs the verb per repo, printing one block per
repo prefixed with the repo path. Cross-repo checks added by `validate --workspace`:
prefixes unique across the set (W-01); no two stores share an `id` (W-02). Exit is the
max over repos. Nothing is written across repos; there is no workspace-level store.

## 9. `init` and `adopt`

- `pm ticket init --prefix <p> [--repo <path>]`: refuses if the v1 store directory
  exists; writes `config.json` (`spec_version` = current), empty `issues.jsonl`,
  `lock`, the two gitignore lines (appended to the repo `.gitignore`, created if
  absent), and prints the one-line CLAUDE.md footprint for the operator to paste.
  Idempotent only in the sense that a second run is a clean refusal, exit 1.
- `pm ticket adopt [--repo <path>] [--from mao|docs-inbox|md-list ...] [--apply]`: `init` if
  needed, then every named importer (default: all that detect a source) in one pass,
  docs-inbox first (importer rule R-28). Dry-run by default: prints the would-be rows,
  edges, archive moves and the report; `--apply` writes into a temp copy of the store,
  runs `validate`, swaps on success. Re-running `adopt --apply` on a repo where every
  source is already archived is a no-op, exit 0.

## 10. `archive` (R7)

`pm ticket archive --closed-before <YYYY-MM-DD> [--dry-run]`: moves rows with
`status == closed` and `updated < date` to `archive/issues-<yyyy>.jsonl`, appends one
index row each (`source` = `self`), and rewrites `issues.jsonl` without them. Edges from
live rows to archived ids are kept as-is; `validate` treats an edge target that resolves
in the archive index as satisfied (I-11). Never automatic; `summary` prints a hint when
`issues.jsonl` exceeds 1 MB or holds closed rows older than 90 days.

## 11. Out of scope for v1

Time tracking, estimates, external sync, workspace-level stores, projection changes
(`PROJECTION_VERSION` stays 1), GUI.
