# pm/ticket spec changelog

## v2.6 additions (2026-11-12, fr-d964dd)

Additive, no `spec_version` bump. Optional note key `kind`, one of `worker-return`, `park`, `finding`, `decision`, `edit-trail`, `provenance`, `measurement` (design C6.1); rows without it stay valid and no existing note is migrated. `note <id> <text> --kind <kind>` writes it (refused on a v1 store). On v2 stores `close` writes `worker-return` (`park` with `--unmerged`; the deploy-check-skipped note is `finding`), `edit` and detach-on-close write `edit-trail`, a `create --dup-of` sighting writes `finding`. Text `show` hides `edit-trail` notes (one line says how many) unless `--all-notes`; `show --json` is unchanged apart from the key.

## v2.5 additions (2026-11-12, fr-44a827)

Additive, no `spec_version` bump. Optional `config.json` key `history_interval_seconds` (integer >= 0), meaningful with `history_ref`. Absent or `0`: one snapshot per op, unchanged. `N > 0`: an op that changes a row's `status` or `assignee` (claim, release, close, reopen, `create --claim-as`) snapshots at once and clears `.pm/history-pending`; other ops defer, creating the marker (`deferred <timestamp>`, never rewritten) and making no git call, until the marker is `N` seconds old on a later op. `summary` and `history sync` flush it at any age. `pm ticket history status` prints `deferred` for that state (the file differs from the tip and the marker starts with `deferred`); `behind` stays for every other difference.

Optional `config.json` key `compact_closed_after_days` (integer >= 0); absent: never compact. Optional epic-only row key `subtasks` (array of `{id, title, closed, reason}` plus optional `note`, `findings`, `closed_by`, sorted by (`closed`, `id`)): after each mutating op a closed child task older than `N` days (and not touched by that op, no `keep` label, not `done-unmerged`) is folded into its parent epic's `subtasks` and its row deleted; its id keeps resolving as a closed ticket. Readers: `show <id>` and `show <id> --json` of a compacted id print a synthesized closed row (`compacted: true`); `where <id> --mutate` refuses it as already closed; `close --findings` accepts it; every verb that would change it (`reopen`, `note`, `edit`, `claim`, `hold`, `release`, `reparent`, `dep`, `unlink`, `close`, `archive`) exits 1 with `<id> was compacted into <parent> when it closed (<closed>); it cannot be changed. File a new ticket.`; `blocked_by_ticket`, `would_cycle` and `tree` skip ids that exist only as tombstones; text `show` of the epic lists its subtasks.

Optional `config.json` key `archive_closed_after_days` (integer >= 0); absent: never. In the same sweep, after compaction, every remaining closed row not touched by the op (when `compact_closed_after_days` is also set, never a closed `task` with a live epic parent and no `keep` label: that row waits for compaction) with `updated` on or before today (UTC) minus `N` days is archived, silently skipping a row that a staying live row names as `parent` (to a fixed point, as `archive --closed-before` does). Year files are now appended to, not rewritten. Archiving an epic that carries `subtasks` also writes one index row per subtask (`meta.compacted_into: <epic id>`, same `path`); validate I-17 checks the epic's year-file row lists that subtask. After an op that archived (the sweep or `pm ticket archive`), `archive/archive-index.jsonl` alone is committed as `pm: archive <n> closed`: never fatal, skipped on a non-default branch with one stderr line, skipped silently when git ignores the file or the store is not in a git checkout. `pm ticket archive` now passes a commit message, so a history store is no longer left `behind`. `show <id>` and `show <id> --json` of an id archived with `source: "self"` read the year file and print the stored row plus `archived: true` (text: `archived: <path>`; a compacted subtask of an archived epic gets the synthesized row); a missing year file or row exits 1 with `<id> is archived in <path> but that file is not on this machine`. `tree <archived id>` exits 1 with one line; `where <archived id> --mutate` refuses as already closed.

## v2.4 additions (2026-11-03, fr-253a2d)

Additive, no `spec_version` bump. Optional row keys `closed_by` (written by `pm ticket close` and `close --unmerged`) and `released_by` (written by `pm ticket release`): the claim-shaped identity (`ticket_core.session_assignee`, e.g. `agent:claude/claude#<8-hex>`) of the acting session, so a ticket claimed and closed inside one turn still links to its session. Written on v2 stores only, and only when a session token is known (`--session`, `PM_SESSION_ID`, `CLAUDE_CODE_SESSION_ID`); bulk close/release set it on every row. `reopen` clears both; `close` clears `released_by`, `release` clears `closed_by`, a re-`claim` clears `released_by`. `close` and `release` gain `--session`. `pm ticket show` prints the keys when present.

## v2.3 additions (2026-11-03, fr-e6e12c)

No schema change. `pm ticket edit <id> --append-body <text>` appends `<text>` as a new line to the existing body (an empty body becomes the text; no leading blank line, no doubled newline) and writes the same `edit history: body was ...` note as `--body`. It refuses, exit 1 and write nothing, when combined with `--body` or when the text is empty. It combines with `--title` and `--priority`.

## v2.2 additions (2026-11-03, fr-b072a7)

No schema change. `pm ticket create` and `pm ticket edit --title` now refuse, exit 1 and write nothing, a title that `validate` I-06 would reject (empty, multi-line, or over 200 chars); the message names the length and the limit. `edit --title` no longer silently truncates to 200.

## v2.2 additions (2026-10-15, fr-66d647)

Schema change to `runtime-tools/pm/stores.json` only (additive): a registry entry may carry an
optional string `successor` (the repo dir that took over a frozen store's work). No change to
`config.json` or `tickets.jsonl` rows.
`archive` redesigned: `pm ticket archive <id> [<id> ...]` moves those closed rows (same
`archive/` layout as before; non-closed or unknown ids refuse the whole call, the
non-closed line names `pm ticket close`). `--closed-before` is no longer required: it is an
optional filter (with ids: each row must predate it; alone: the former bulk form); no ids and
no date is a refusal. The summary size hint now suggests `pm ticket archive <id> [<id> ...]`.
Frozen stores: a refused mutation ends `; use <successor>/.pm` when the entry has a
`successor`; text `summary` and `ready` print one "store <repo> is frozen; work is in
<successor>/.pm" line instead of listing work (`--json` unchanged). `stores --check` validates
`successor`. Refusal semantics of the frozen role are unchanged.

## v2.1 additions (2026-10-14, fr-a1ee37)

No schema change. The frozen-store check now fails closed on a mutation: a registry file that
exists but cannot be read or parsed, has the wrong shape, or carries a `role` other than exactly
`live`/`frozen` on any entry (`Frozen`, `archived`) refuses every mutation, naming the registry
path and the fault, instead of warning and treating the store as live. No file and no symlink
at the registry path still means no frozen stores (a dangling symlink is unreadable and
refuses), and an absent `role` is still `live`. Reads never look up the frozen role; a read
of a current-store id tolerates a broken registry. A non-UTF-8 registry is an error, not a
traceback. `stores --check` reports a bad role as a problem (exit 2) naming the value.

## v2.1 additions (2026-10-14, fr-aaebbc)

No schema change. A store the registry marks `frozen` now refuses every mutation: ones run
with cwd inside it, ones with an explicit `--store` naming it, and the store-scoped verbs
(`create`, `archive`, `upgrade`, `fix-labels`, `adopt --apply`,
`history enable|disable|sync|restore`), not only id-taking mutations routed to it.
`archive --dry-run` and `adopt` without `--apply` still run; `upgrade --dry-run` and an
already-current `upgrade` are refused (the dry run writes `<repo>/.pm.upgrade-<pid>`);
`upgrade --workspace` skips a frozen repo with a refusal line and exits non-zero. Exit 1,
nothing written or committed; the
refusal names the store and the live owner of its prefix when one is registered. The role is
read from `stores.json` alone, and only on a mutation; reads of a frozen store are unchanged.

## v2.1 additions (2026-10-14, fr-1590f5)

No schema change. `close --findings` now stores each id bare: `<prefix>/<id>` is resolved,
then written as `<id>`, so `validate` accepts the row (the schema allows only bare ids in
`findings`). Supersedes the stored-as-given behaviour of fr-a58e7e.

## v2.1 additions (2026-10-14, fr-7e1d26)

Additive, no `spec_version` bump. `config.json` accepts optional boolean
`findings_required`; the close row accepts optional `findings_absent` (only ever `true`).
Phase 1 (flag off): `pm ticket close` and `wt finish`/`wt park` without `--findings` warn and
the close records `findings_absent`. Phase 2 (`findings_required: true`): they refuse, `wt`
before any merge or teardown, and `--findings none` needs a non-empty `--note`/`--reason` or an
existing note. pm must be deployed before any config or row carries either key (I-02).

## v2.1 additions (2026-10-14, fr-a58e7e)

No schema change. `close --findings` accepts ids of other registered stores (bare or
`<prefix>/<id>`), resolved read-only through `resolve_store`; an unowned prefix is refused
with the resolve_store text. Supersedes the fr-05e45a "other-store ids are refused" entry.

## v2.1 additions (2026-10-14, fr-1bdf6d)

Additive, no `spec_version` bump. Optional boolean row key `dedupe_overridden` (only ever
`true`), written by `pm ticket create --new` (ticket.schema.json, SPEC.md section 4). pm
must be deployed before any store holds it: an older `validate` rejects the unknown key
(I-02). CLI only: `create` now refuses (exit 2, nothing written) when an open row, or one
closed within 30 days, shares enough rare title/body tokens (words of 4+ chars, file paths,
ticket ids, quoted strings) with the new ticket and reaches an idf-weighted Jaccard of 0.25;
it prints up to 3 `possible duplicate: <id> <status> <title>` lines (`--json`:
`{"possible_duplicates": [...]}`). `--dup-of <id>` appends a `sighting <date> (found in
<discovered-from>): <title>` note to that row instead of creating one; `--new` bypasses the
guard. Thresholds: `DUP_*` in `ticket_core.py`.

## v2.1 additions (2026-10-13, fr-d65047)

Additive, no `spec_version` bump. `config.json` accepts optional `gate` (non-empty
array of strings, the argv `wt finish` reads, fr-240ed1) and `known_red` (array of
`{match, ticket, since}`, fr-6c228b; section 3). pm must be deployed before any config
carries either key: an older `validate` rejects the unknown key (I-02).

## v2.1 additions (2026-10-13, fr-05e45a)

Additive, no `spec_version` bump. Optional `findings` row key (string[]; `["none"]` or
same-store ticket ids), written by `pm ticket close --findings`, cleared by `reopen`.
Other-store ids are refused until fr-a58e7e routes them through `resolve_store`.

## v2.1 additions (2026-10-12, fr-401bf1)

Additive, no `spec_version` bump. `config.json` accepts optional `legacy_prefixes`
(unique strings matching the prefix pattern, none equal to `prefix`; section 3).
`validate` I-03 accepts a row id under `prefix` or any legacy prefix; the disjointness
rule is an I-02 check. `create` still mints only `prefix`. `dep`/`unlink` treat a
legacy-prefixed target as local when the store holds the row, else as a cross-store
edge to the registry's owner. pm must be deployed before any config carries
`legacy_prefixes`: an older `validate` rejects the unknown key (I-02).

## v2.1 additions (2026-10-12, fr-b1b41c)

Additive, no `spec_version` bump. New edge type `blocked-by` (ticket.schema.json and
SPEC.md section 4), valid only with a cross-store `to` and stored on the blocked row
in the blocked row's store. `is_ready` requires every `blocked-by` target to be
`closed` (or a `source: self` archive row) and fails closed on an unresolvable one.
`dep`/`unlink`/`create --discovered-from` accept `<prefix>-<id>` or `<prefix>/<id>`
(never `<prefix>:<id>`). `claim`, `summary`, `show` and `tree` text views surface the
remote blockers; every `--json` projection is unchanged. `validate` checks the
`blocked-by` shape (I-04); `pm ticket stores --check` reports dangling cross-store
edges and blocker-side cross-store `blocks` edges. pm must be deployed before any
store holds a `blocked-by` edge: an older `validate` rejects the unknown enum value.

## v2.1 additions (2026-10-12, fr-1576dd)

Additive, no `spec_version` bump. SPEC.md section 3 gains a "Store registry"
subsection (path list at `runtime-tools/pm/stores.json`, `PM_STORES_FILE` override,
prefix-based `resolve_store`, routed verbs, `--store` with `--repo` as alias,
`pm ticket where`, `pm ticket stores [--check]`) and replaces the out-of-scope bullets
in sections 0 and 10. This amends ADR Q9, which placed the registry at
`~/.config/pm/stores.json`.

## v2 (draft, 2026-10-05, cl-730ec9)

One bump covering five changes at once (ADR `pm-reorg.md` Q6: "one bump, not
several"):

- **Store/file rename.** the v1 store directory -> `.pm/`, `issues.jsonl` -> `tickets.jsonl`,
  `issues-<yyyy>.jsonl` -> `tickets-<yyyy>.jsonl`. Performed by the runtime
  (cl-37cb07), not by `migrate_v1_to_v2.py`, which still reads/writes the v1
  filenames (`config.json`, `issues.jsonl`) -- SPEC.md section 0.
- **`config.json` identity fields.** New `store_id` (12-hex token, assigned once,
  never reassigned) and `created_by` (`<provider>/<name>` or null, ADR Q7's env
  contract). Both reserved for the store registry (ADR Q9, `~/.config/pm/stores.json`)
  and cross-store edges; neither is read by any v2 verb yet. `migrate_v1_to_v2.py`
  populates both for every pre-existing store (`store_id` deterministically from
  content, `created_by: null` -- never guessed).
- **Assignee identity (ADR Q7).** Narrowed from "any non-empty string" to
  `agent:<provider>/<name>#<8-hex>` | `human:<name>` | `legacy:<anything>` (migration
  landing spot only). This is the backward-incompatible change that forces the spec
  bump: a v1 store with an assignee like `@pm-cutover-overseer#f2a24e63` would fail a
  naive v2 schema check, so the migration wraps it as `legacy:@pm-cutover-overseer#...`
  rather than reject or guess a provider.
- **Cross-store edge syntax (ADR Q6).** `edges[].to` now also accepts
  `<prefix>/<id>` alongside a bare local id. v1 downgraded a cross-repo relation to a
  prose note (see the v1 entry below); v2 makes it a first-class (shape-only;
  existence resolution is the registry's job, out of scope here) edge target.
- **Title cap enforced at `create` (folds cl-a53655).** v1 never specified `create` at
  all; v2 section 8 requires `create` to refuse an over-200-char title the same way
  `validate`'s I-06 already does, rather than writing a row `validate` would then
  reject. Refuse, never truncate (never-synthesize principle).
- **Lock gitignored (folds cl-f7d6b4).** `init`/`adopt` MUST write a `.pm/lock`
  gitignore line alongside the archive lines; a tracked `.pm/lock` is now an I-01-style
  validate problem instead of silent.
- **`closure_reason` (mined from workctl, one field, one named consumer).** New
  optional 14th row key, `null` unless a write path that knows the reason sets it
  (`pm work close`, cl-496fb8). MUST be null when not closed; MAY still be null when
  closed (a migrated row has no recoverable reason -- never guessed from note text).
  No other workctl lifecycle concept (principals, approval receipts, leases/worktree
  identity, evidence adoption, projection bundles, ULID typed ids) is adopted in this
  bump; each needs its own named consumer first.

- **`hold` (fr-d088b2, added while v2 is still draft).** Optional 15th row key, absent
  unless a claiming session declares the claim in flight (`claim --hold`, `hold`);
  cleared by `release`/`close`/`reopen`. Consumer: the Stop hook's warn-once path and
  `summary`'s stale-hold list. See SPEC.md "In-flight hold".

- **`history_ref` (fr-4cc7ec, additive; no `spec_version` bump).** Optional `config.json`
  key, enum `["pm-store"]`. Set, it moves the store's commit history off the checked-out
  branch onto `refs/heads/pm-store` (plumbing commits; working `tickets.jsonl` becomes
  untracked and ignored). Absent keeps today's behavior byte for byte. Verbs:
  `pm ticket history status|enable|disable|sync|restore`. See SPEC.md section 1.

Schema shape: row key count goes from 13 to 14 (`closure_reason` added; a 15th,
optional `hold`, is described above);
`config.json` key count goes from 2 to up to 4 (`store_id` required, `created_by`
optional). `PROJECTION_VERSION` is unaffected by this bump -- no verb here changes
what `ticket_core.project()` reads.

## v1 (draft, 2026-09-15; frozen when tagged `pm-spec/v1`)

See `runtime-tools/pm/ticket/spec/v1/CHANGELOG.md` for the full v1 history, carried here only where
v2 supersedes it:

- Rows: exactly 13 keys (v2: 14); `assignee` any non-empty string (v2: narrowed);
  `edges[].to` local ids only (v2: cross-store syntax added).
- `config.json`: exactly `spec_version`, `prefix` (v2: adds `store_id`, `created_by`).
- A cross-repo relation that v1 could not express as an edge was downgraded to a
  prose note -- the gap v2's cross-store edge syntax closes.
