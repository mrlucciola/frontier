# Spec v1 invariants

Each invariant has an id, the check, the step text `validate` prints, and who may act on
it: **agent** (the fix is mechanical, F6) or **operator**. `validate` prints steps in
(file, line, invariant id) order. The last column maps each rule of the legacy
`Store.lint()`; every one (including "unknown edge type", an I-04 schema check) is
covered here, so `Store.lint()` was deleted (cl-603745) and `validate` is the only rule set.

## Store level

| id | check | step text (after `->`) | actor | lint rule |
|---|---|---|---|---|
| I-01 | no entries under the v1 store directory other than section 2 of SPEC.md; `.tmp`/`*.tmp` tolerated | `operator: remove or relocate <path>; it is not part of the store` | operator | - |
| I-02 | `config.json` matches `config.schema.json`; `spec_version` equals the target version. v0 shape (`version` key, no `spec_version`) is reported as one step | `run: pm ticket upgrade` (v0) or `operator: config.json <key>: <schema message>` | agent (v0) / operator | - |
| I-03 | every `id` starts with `<prefix>-` and matches the id pattern | `operator: row id <id> does not carry prefix <prefix>; re-file or edit the id and every edge that names it` | operator | - |
| I-04 | every row matches `ticket.schema.json` (exactly 13 keys) | `operator: <line> <json pointer>: <schema message>` | operator | unknown status / unknown kind |
| I-05 | ids unique across `issues.jsonl` and `archive/archive-index.jsonl` rows with `source == self` | `operator: duplicate id <id> at lines <a>,<b>; keep one, re-file the other` | operator | duplicate id |
| I-06 | `title` non-empty, one line, <= 200 chars | `run: pm ticket edit <id> --title "<truncated title>"` | agent | - |
| I-07 | task: `assignee` non-null iff `status == claimed` | claimed+null: `run: pm ticket release <id>`; open+assignee: `run: pm ticket release <id>` | agent | claimed but unassigned |
| I-08 | epic: `status != claimed` and `assignee == null` | `run: pm ticket release <id>` | agent | epic is claimed |
| I-09 | `parent` null or an existing row with `kind == epic`; no parent cycle | missing: `operator: parent <p> of <id> does not exist; pm ticket reparent <id> --none or restore <p>`; not epic: `operator: parent <p> is a task`; cycle: `operator: parent cycle <id> -> ... -> <id>` | operator | parent -> missing / not an epic / parent cycle |
| I-10 | `labels` sorted, unique, each matches the label pattern | `run: pm ticket fix-labels <id>` (sort/dedupe) or `operator: label <l> on <id> is not a valid label; pm ticket fix-labels <id> lowercases it, or drops it if still invalid` (fr-3fc528: `create` refuses such a label; `fix-labels` prints every label it drops) | agent / operator | - |
| I-11 | every edge `to` resolves to a live row, or (blocks/related/discovered-from alike) to an archive index row with `source == self` | `operator: <type> edge <id> -> <to> names no ticket; pm ticket unlink <id> <to> or restore <to>` | operator | edge -> missing |
| I-12 | no edge where `to == id` | `run: pm ticket unlink <id> <id>` | agent | self-referencing edge |
| I-13 | `blocks` graph acyclic | `operator: blocks cycle <a> -> <b> -> ... -> <a>; pm ticket unlink one edge` | operator | - |
| I-14 | `notes[].ts` non-decreasing | `operator: note timestamps out of order on <id> at index <k>` | operator | - |
| I-15 | `updated >= created`; both valid timestamps | `operator: <id> updated <u> precedes created <c>` | operator | - |

## Archive level (only when `archive/` is present)

| id | check | step text | actor |
|---|---|---|---|
| I-16 | `archive-index.jsonl` rows parse and carry exactly `id title source closed path archived meta` | `operator: archive-index.jsonl:<line>: <message>` | operator |
| I-17 | `archive/issues-<yyyy>.jsonl` rows match `ticket.schema.json` and have `status == closed` | `operator: archive/issues-<yyyy>.jsonl:<line>: <message>` | operator |
| I-18 | no entry under `archive/` other than the index, `issues-<yyyy>.jsonl`, and `<source>-<yyyymmdd>/` directories | `operator: <path> is not an archive entry` | operator |

An index row whose `path` does not resolve is **not** a problem (R2 amendment, importer
rule R-42).

## Workspace level (`--workspace`)

| id | check | step text | actor |
|---|---|---|---|
| W-01 | `prefix` unique across discovered stores | `operator: prefix <p> used by <repo a> and <repo b>; pm ticket init cannot fix this, pick a new prefix in one config.json and re-id its rows` | operator |
| W-02 | no id present in two stores | `operator: id <id> in <repo a> and <repo b>` | operator |

## Verbs referenced by step text that do not exist yet

`pm ticket edit --title`, `pm ticket fix-labels`, `pm ticket unlink`. P4 builds them; each is a single-row
mutation under the store lock with no other side effect, so an agent may run it from
step text without reasoning.
