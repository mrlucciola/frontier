# PM ticket store spec v2

Status: DRAFT (cl-730ec9, epic cl-14b31a; ADR `~/frontier/docs/pm-reorg.md` Q6, Q7, Q9).
Supersedes `runtime-tools/pm/ticket/spec/v1/SPEC.md` for every store at `spec_version: 2`. Normative
for: store layout, `config.json`, every row of `tickets.jsonl`, the archive, and the
observable contracts of `create`, `validate`, `upgrade`, `init`, `adopt`. This document
is self-contained (v1 behaviour is restated, not just diffed); `CHANGELOG.md` in this
directory carries the delta narrative and rationale.

Words: MUST / MUST NOT are mechanically checkable. SHOULD is guidance the write path
follows but a checker need not enforce.

## 0. What moved here and what did not

Everything in `runtime-tools/pm/ticket/spec/v1/SPEC.md` section 1 ("Versions") still applies: N+1
exists only when a store valid at vN would fail at vN+1. v2 is one bump per the ADR
(Q6: "one bump, not several") covering five changes at once: the store/file rename,
identity fields, cross-store edge syntax, the title cap at `create`, and one mined
lifecycle field (`closure_reason`). `ticket_core.PROJECTION_VERSION` is unaffected.

**Not in this document, by design:**

- The v1 store directory -> `.pm/` directory rename and `issues.jsonl` -> `tickets.jsonl` file
  rename are performed by the **runtime** (the tool that reads/writes a live store),
  tracked by cl-37cb07. `migrate_v1_to_v2.py` in this directory is a pure function over
  a directory that still carries the v1 filenames (`config.json`, `issues.jsonl`) at
  the moment it runs, exactly like `migrate_v0_to_v1.py` -- see section 7 and the
  module's own docstring. A reader of this SPEC.md should picture `.pm/tickets.jsonl`
  as the *steady-state* v2 layout the runtime produces, not as something the migration
  module itself writes.
- The store registry is defined in section 3 ("Store registry"): a machine-level path
  list at `runtime-tools/pm/stores.json`, deployed with pm, which amends ADR Q9
  (`~/.config/pm/stores.json`). This spec defines the cross-store edge *syntax*
  (section 4) and how readers resolve its target (v2.1); single-repo `validate` stays
  shape-only, same way v1 left W-01/W-02 to the `--workspace` layer.
- `pm ticket lint` (the dispatchable-ticket body-heading checker, cl-888843) is a
  separate verb built under a separate ticket. Section 5 reserves the slot this spec
  owns: the four headings are a body convention, not schema fields.

## 1. Layout

```
<repo>/.pm/
  config.json              MUST   see section 3
  tickets.jsonl             MUST   see section 4 (may be empty)
  lock                     MAY    flock target; content irrelevant; SHOULD exist;
                                  MUST be gitignored (folds cl-f7d6b4, see below)
  migrate-report.md        MAY    written by adopt/migrate; not validated
  upgrade-<from>-to-<to>.md MAY   written by upgrade; not validated
  archive/                 MAY    gitignored except the index; see section 6
    archive-index.jsonl    MAY    tracked
    tickets-<yyyy>.jsonl    MAY   rows moved out by `archive`
    <source>-<yyyymmdd>/   MAY    moved artifacts, untouched
```

**History ref (fr-4cc7ec, additive).** When `config.json` sets `history_ref`,
`.pm/tickets.jsonl` is untracked and gitignored in the store's repo, and every mutation
is recorded as one plumbing commit on `refs/heads/pm-store` (tree: one entry,
`tickets.jsonl`) instead of a commit on the checked-out branch. The working file stays
the only file pm reads and writes; with the key set and the working file missing,
every verb refuses and names `pm ticket history restore`, never loading it as empty.
`pm ticket history {status,enable,disable,sync,restore}` move a store in and out. A
store without the key commits exactly as before. With the optional `history_interval_seconds`
(section 3) the snapshot of an op that changes no row's `status` or `assignee` may be
deferred: pm creates `.pm/history-pending` (content `deferred <timestamp>`) and commits
nothing until the marker is that many seconds old on a later op, or `summary` or
`history sync` runs. The working file is written on every op regardless.

No other entries MUST exist under `.pm/`; unknown entries are a problem, `.tmp`/`*.tmp`
tolerated, exactly as v1 section 2's I-01.

Store discovery (walk up from cwd to the nearest `.pm/`, never crossing a `.git`
boundary upward, worktree-sideways-resolution via `gitdir:`) is unchanged from v1
section 2 and is not restated here; a store is found by the presence of `.pm/`,
not the v1 store directory, once a repo is at v2 (the runtime decides when a repo "is at v2":
out of scope here, cl-37cb07/cl-55e2e5).

**Lock gitignore (folds cl-f7d6b4).** v1's `init`/`adopt` wrote only the archive
gitignore lines (the v1 store directory's `archive/*`, `!archive/archive-index.jsonl`) and
left `lock` untracked-but-not-ignored, so a blanket `git add` of the v1 store directory
staged a runtime file that every subsequent `pm ticket` invocation then dirtied. v2 requires `init`
and `adopt` to also write a `.pm/lock` gitignore line in the same pass that writes the
archive lines, before the store is first used. `validate` at v2 treats a *tracked*
`.pm/lock` as an I-01 problem (`operator: untrack .pm/lock and add it to .gitignore`)
rather than silently tolerating it.

## 2. Versions

A store declares `spec_version: 2` in `config.json`. v1 -> v2 is
`migrate_v1_to_v2.py` in this directory, chained after
`runtime-tools/pm/ticket/spec/v1/migrate_v0_to_v1.py` so a v0 store (`lai`) upgrades to v2 in one
`pm ticket upgrade` call. Sharding to one file
per ticket is explicitly out of scope for v2 (ADR Q6), same as v1 section 11.

## 3. `config.json`

Schema: `config.schema.json`. Exactly these keys, no others (optional ones may be absent):

| key | type | rule |
|---|---|---|
| `spec_version` | integer | equals 2 (I-02, unchanged shape from v1) |
| `prefix` | string | `^[a-z][a-z0-9]{1,7}$`; every row id starts with `<prefix>-` or `<legacy prefix>-` (I-03, widened in v2.1) |
| `store_id` | string | `^[0-9a-f]{12}$`; new in v2, see below |
| `created_by` | string or null | new in v2, see below |
| `history_ref` | string, optional | enum `["pm-store"]`; absent means commits on the checked-out branch (section 1, "History ref") |
| `archive_closed_after_days` | integer >= 0, optional | v2.5. Absent: never. Set: after each mutating op, after compaction, every `closed` row with `updated` on or before today (UTC) minus `N` days, not touched by that op, is archived as `pm ticket archive` would (section 6); a row a staying live row names as `parent` is skipped without a message, to a fixed point. When `compact_closed_after_days` is also set, a row compaction owns whatever its age (`task`, live epic parent, no `keep` label) is never selected: it waits for compaction. Without that key every such row is eligible |
| `compact_closed_after_days` | integer >= 0, optional | v2.5. Absent: never compact. Set: after each mutating op, a closed `task` row with a live epic parent, no `keep` label, and `updated` on or before today (UTC) minus `N` days, not touched by that op and not the target of any edge of a row that op touched, is replaced by an entry in its parent's `subtasks` (section 4) and its `blocks` edges are dropped; `done-unmerged` rows are never compacted |
| `history_interval_seconds` | integer >= 0, optional | v2.5. Only meaningful with `history_ref`. Absent or `0`: one history snapshot per mutating op. `N > 0`: an op that changes some row's `status` or `assignee` (a new row counts as `open`, unassigned) snapshots at once; any other op defers its snapshot until the `history-pending` marker is `N` seconds old (section 1, "History ref") |
| `legacy_prefixes` | array of string, optional | v2.1 (fr-401bf1). Each `^[a-z][a-z0-9]{1,7}$`, unique, and none equal to `prefix` (the last is checked by `validate`, I-02, since JSON Schema cannot express it). Absent reads as `[]`. A row id may carry `prefix` or any legacy prefix (I-03); `create` mints only `prefix` |
| `gate` | array of string, optional | v2.1 (fr-d65047). Non-empty argv `wt finish`/`wt land` run in the worktree before merging (fr-240ed1); absent means no gate. `pm` only validates the shape; `wt` owns the semantics |
| `findings_required` | boolean, optional | v2.1 (fr-7e1d26). `true`: `pm ticket close` (also `--unmerged`), `wt finish` and `wt park` refuse without `--findings`, and `--findings none` needs a non-empty `--note`/`--reason` or an existing note. Absent or `false`: the same calls warn and record `findings_absent` |
| `known_red` | array of object, optional | v2.1 (fr-d65047). Entries `{"match": <non-empty substring of a failing test line>, "ticket": <id>, "since": "YYYY-MM-DD"}`, all three required, no other keys. Shape only here; the gate semantics are fr-6c228b's |

**Identity fields (ADR Q6/Q9).** `prefix` is a human-chosen, repo-scoped mnemonic and
is only checked for uniqueness within one `--workspace` fan-out (v1 section 8,
unchanged) -- two unrelated repos on the same machine can legally share a prefix until
someone runs them together. That is not enough identity for the store registry (ADR
Q9; see "Store registry" below for where it lives) or for a cross-store edge (section
4) to name a store unambiguously machine-wide. v2 adds:

- `store_id`: a 12-hex-character token, assigned once (by `init`, or by
  `migrate_v1_to_v2.py` for a store that predates it) and **never reassigned**. It is
  the stable key the registry and cross-store edges use; `prefix` MAY change (via a
  future reparent/rename verb) without invalidating existing cross-store references.
  The store registry (below) resolves by prefix and owned prefixes, not by `store_id`;
  `store_id` stays reserved shape only -- no verb reads it yet.
- `created_by`: `<provider>/<name>` (ADR Q7's env contract, e.g. `claude/cl-f2a24e63`)
  or `null`. Populated from `PM_AGENT` at `init` time once the provider env contract
  (cl-ea6f1a) lands; `null` for every store that predates it, including every store
  `migrate_v1_to_v2.py` touches -- the migration MUST NOT guess who created a store it
  has no record of (never synthesize; same principle as cl-a53655's fix shape).

Both fields are optional-at-schema-level only in the sense that `migrate_v1_to_v2.py`
always populates `store_id` (deterministically, see section 7) and always sets
`created_by: null` when absent; `config.schema.json` marks `store_id` required and
`created_by` optional-with-null-default so a hand-written `config.json` need not supply
`created_by`.

### Store registry (fr-1576dd)

Design: `docs/design/2026-10-12-pm-store-and-prefix-routing.md` section (a). This
**amends ADR Q9**, which put the registry at `~/.config/pm/stores.json` maintained by
`init`/`adopt`: sandboxed agents cannot write `~/.config`, and a file many sessions
write is a second, racy source of truth. The registry is authored in frontier instead.

- **Ownership lives in each store.** A store owns its `prefix` plus any
  `legacy_prefixes` (accepted, never minted). A missing `legacy_prefixes` reads as
  empty. The key is schema-legal since v2.1 (fr-401bf1). An edge to a legacy-prefixed
  id is local when the store holds the row; otherwise it is a cross-store edge
  resolved through the registry (a frozen owner of that prefix).
- **Locations live in one file.** `runtime-tools/pm/stores.json`:
  `{"stores": [{"path": "<dir holding .pm>", "role": "live"|"frozen"}]}`, `role`
  optional (default `live`), `path` `~`-expanded. It lists paths only. It is deployed
  with pm beside the code and found relative to the pm source file;
  `PM_STORES_FILE` overrides the location. `init`/`adopt` never write it.
- **Resolution** (`resolve_store(ref, explicit, cwd)`, `ref` = `pfx-id` or
  `pfx/pfx-id`): (1) the explicit `--store`/`--repo` store; (2) the cwd store, when it
  owns the prefix; (3) the registry entries whose config owns the prefix, live over
  frozen: two live owners are refused (`pm: prefix 'xx' is owned by two registered
  stores: <a>, <b>; fix runtime-tools/pm/stores.json or pass --store`), no owner is
  refused (`pm: no registered store owns prefix 'xx'; pass --store <repo>, or add the
  repo to ~/frontier/runtime-tools/pm/stores.json and deploy pm`); (4) a read of a row
  a live owner lacks falls back to a frozen owner that has it.
- **Routed verbs:** `show tree claim hold release close reopen note edit reparent
  unlink dep` (dep routes its src). Bulk ids must resolve to one store or the call is
  refused. Every mutation on a `frozen` store is refused (routed, cwd, explicit
  `--store`, and the store-scoped `create archive upgrade fix-labels adopt --apply
  history enable|disable|sync|restore`); reads are unaffected (`archive --dry-run`
  and `adopt` without `--apply` run; `upgrade --dry-run` is refused because it
  writes a sibling `.pm.upgrade-<pid>`). The check fails closed: a registry file that
  exists but is unreadable, unparsable or of the wrong shape, or any entry whose `role`
  is not exactly `live` or `frozen`, refuses every mutation (exit 1, naming the
  registry path and the fault); only no file and no symlink at the path (a dangling symlink is unreadable) means no
  frozen stores, and an absent `role` is `live`. Reads never look up the frozen role;
  a read of a current-store id tolerates a broken registry. **`successor` (v2.2,
  fr-66d647).** An entry may carry `"successor": "<repo dir>"` (a string, frozen entries only;
  printed as written, `~`-expanded only by `stores --check`). A mutation refused because the store is frozen then
  ends `; use <successor>/.pm`, in place of the live-owner hint. Text `summary` and `ready`
  on a frozen store print one line (`store <repo> is frozen; work is in <successor>/.pm`,
  without the tail when no successor) instead of listing work; `--json` is unchanged.
  `stores --check` flags a non-string/empty successor, one on a non-frozen entry, or one
  that is not a directory. A routed mutation commits
  in the owning store's repo exactly like `--store` does. Store-scoped verbs (`ready
  list summary board overview create init adopt validate upgrade archive lint
  fix-labels`) never route.
- **Flags.** `--store` is the canonical global and per-verb spelling; `--repo` is a
  working alias, hidden from help.
- **Verbs.** `pm ticket where <id>` prints the owning store's repo root (exit 1 with
  the refusal text). `pm ticket stores [--check]` lists entries with prefixes and
  role; `--check` reports a malformed registry, missing paths, bad configs,
  tickets whose id prefix their own store does not own, live prefix collisions (one
  repo listed twice or via a symlink is one owner), and a prefix owned by two frozen
  stores with no live owner (exit 2 when any). A routed id may be written
  `<prefix>/<id>`; the prefix must be the id's own. Cross-store edge checks are in
  section 4 ("Cross-store edges").

## 4. Rows in `tickets.jsonl`

One JSON object per line, UTF-8, `\n`-terminated, keys sorted, `ensure_ascii=false`,
blank lines tolerated on read / removed on next write -- unchanged from v1 section 4.
Schema: `ticket.schema.json`. A row has exactly these **14** keys (v1 had 13; v2 adds
`closure_reason`):

| key | type | rule |
|---|---|---|
| `id` | string | `^<prefix>-[0-9a-f]{6,11}$`, unique in file and archive index (unchanged) |
| `title` | string | non-empty, single line, <= 200 chars; **enforced at `create`, not only at `validate`** (folds cl-a53655, see section 8) |
| `body` | string | any, may be empty; see section 5 for the (non-schema) heading convention |
| `kind` | enum | `task` or `epic` (unchanged) |
| `status` | enum | `open`, `claimed`, `done-unmerged`, `closed` (unchanged) |
| `priority` | integer | 0..4 (unchanged) |
| `assignee` | string or null | see "Assignee identity" below (changed) |
| `parent` | string or null | an existing row of `kind == epic`, no parent cycle (unchanged) |
| `labels` | string[] | sorted, unique, each `^[a-z0-9][a-z0-9:_./-]*$` (unchanged) |
| `edges` | object[] | each `{"type": <blocks,related,discovered-from,blocked-by>, "to": <id or cross-store id>}`; see "Cross-store edges" below (changed) |
| `notes` | object[] | each `{"ts": <timestamp>, "text": <string>}`, non-decreasing `ts` (unchanged) |
| `created` | timestamp | unchanged |
| `updated` | timestamp | `>= created` (unchanged) |
| `closure_reason` | string or null | new in v2, see "Lifecycle: closure_reason" below |
| `hold` | object, **optional** | in-flight marker on a claimed row, see "In-flight hold" below; the key is absent, never null |
| `findings` | string[] (optional) | **optional key, absent unless set.** Written by `pm ticket close --findings none\|<id>[,<id>...]` (also `--unmerged`): `["none"]` or the ticket ids the closer routed findings to, each a row of this or another registered store at close time (fr-a58e7e), stored as bare ids (`<prefix>/` stripped by `close`, fr-1590f5). Absent = not attested. Cleared by `reopen`. Additive and optional, so no `spec_version` bump |
| `dedupe_overridden` | `true` (optional) | **optional key, absent unless set.** Written by `pm ticket create --new`, the override of the duplicate guard (fr-1bdf6d); never `false`. Additive and optional, so no `spec_version` bump |
| `findings_absent` | `true` (optional) | **optional key, absent unless set.** Written by `pm ticket close` (also `--unmerged`) without `--findings` while `findings_required` is off (fr-7e1d26); never `false`. Cleared by `reopen`. Additive and optional, so no `spec_version` bump |
| `closed_by` | string (optional) | **optional key, absent unless set.** Written by `pm ticket close` (also `--unmerged`, and bulk: every row) on a v2 store when a session token is known (`--session`, `PM_SESSION_ID`, `CLAUDE_CODE_SESSION_ID`): the identity string a claim by that session would carry (`ticket_core.session_assignee`, e.g. `agent:claude/claude#<8-hex>`), so the session-to-ticket link survives closure (fr-253a2d). Not written (and removed from the row) when no token is known. Cleared by `reopen` and `release`. Additive and optional, so no `spec_version` bump |
| `released_by` | string (optional) | **optional key, absent unless set.** Same identity as `closed_by`, written by `pm ticket release` (it does not close, hence its own key). Cleared by `claim`, `close` and `reopen`. Additive and optional, so no `spec_version` bump |
| `subtasks` | array of objects (optional) | **optional key, absent unless set, legal only on `kind: "epic"` rows** (I-04 otherwise). One tombstone per closed child task compacted by `compact_closed_after_days` (fr-44a827), entries sorted by (`closed`, `id`) (I-04 otherwise). Keys: `id`, `title`, `closed` (the row's `updated` at compaction, timestamp), `reason` (the row's `closure_reason` or null), and only when the row had them `note` (first line of its last note, at most 200 chars), `findings`, `closed_by`; no others. A subtask id never equals a live row id, another subtask id, or an archive-index id (I-05), and resolves as an existing closed ticket wherever an archived id does (edge targets, I-11, cross-store resolution, new-id allocation). Additive and optional, so no `spec_version` bump |

Reserved labels: unchanged from v1 (`semaphore`, `xrepo`, `imported:<yyyymmdd>`, `mao`,
`mao:<run>:<T-nnn>`, `mao-run:<id>`, `mao-phase:<id>`, `archive-pointer`, and the R4
types `backlog`, `failure-report`, `wishlist`, `question`).

### Assignee identity (ADR Q7)

v1 allowed any non-empty string. v2 narrows `assignee` to exactly one of:

- `null`
- `agent:<provider>/<name>#<8-hex-token>` -- an automated claim, e.g.
  `agent:claude/cl-f2a24e63-worker#3fa91c2d`
- `human:<name>` -- an operator claim
- `legacy:<anything>` -- **migration-only**, never written by a v2-aware writer. v1
  stores in the wild carry assignees in whatever shape they were claimed under (e.g.
  `@pm-cutover-overseer#f2a24e63`), and this migration has no way to know which
  provider made a given legacy claim. Rather than guess, `migrate_v1_to_v2.py` wraps
  the untouched original string as `legacy:<original>` (section 7). `validate` at v2
  accepts `legacy:` assignees without complaint; a future reclassification tool MAY
  turn a `legacy:` assignee into `agent:`/`human:` given external knowledge, but
  nothing in v2 requires it.

The non-null-iff-claimed rule for tasks and the always-null rule for epics (v1's I-07,
I-08) are unchanged regardless of which of the three non-null shapes is used.

The `#<8-hex-token>` in an `agent:`/bare claim is `sha256(session id)[:8]`; the session
id itself is an explicit `--session`, else `PM_SESSION_ID` (provider-neutral; any
provider's launch may set it), else `CLAUDE_CODE_SESSION_ID` (cl-ea6f1a -- Claude Code
keeps working unchanged when `PM_SESSION_ID` is unset).

### Cross-store edges (ADR Q6)

v1 edges only ever named a row in the *same* store: `to` matched `$defs/id`
(`^<prefix>-[0-9a-f]{6,11}$`), and a cross-repo relation that did not fit was
downgraded to a prose note (v1 CHANGELOG, P5 entry). v2 widens `to` to also accept a
**cross-store id**, `<other-prefix>/<id>`:

```
to: ^([a-z][a-z0-9]{1,7}/)?[a-z][a-z0-9]{1,7}-[0-9a-f]{6,11}$
```

i.e. an optional `<other-prefix>/` segment in front of an otherwise-ordinary local id.
A `to` with no `/` is local and resolved exactly as v1 (I-11: must resolve to a live
row or a `source: self` archive-index row in *this* store). A `to` with a `/` is
cross-store: v2's `validate` on a single repo checks **shape only** (the regex above)
-- it has no way to open another repo's store. Existence-checking a cross-store edge
target is the registry's job (`pm ticket stores --check`, below), the same way v1 left
cross-repo id-uniqueness to `--workspace` (W-02) rather than single-repo `validate`.

**`blocked-by` (v2.1, fr-b1b41c, additive; no `spec_version` bump).** A fourth edge
type, valid only with a cross-store `to`. `validate` checks that shape (a `blocked-by`
whose `to` has no `/` is I-04) and nothing else. Where each relation is stored:

| Relation | Same store | Different stores |
|---|---|---|
| A blocks B | on A: `{"type": "blocks", "to": "B"}` | on **B**, in B's store: `{"type": "blocked-by", "to": "<pA>/A"}` |
| A related B | on A | on A: `{"type": "related", "to": "<pB>/B"}` |
| B discovered-from A | on B at `create` | on B: `{"type": "discovered-from", "to": "<pA>/A"}` |

A cross-store `blocks` edge on the blocker side is never written by a tool; `ready`
ignores it and `pm ticket stores --check` reports it.

Writing. `dep`, `unlink` and `create --discovered-from` accept `lin-559399` or
`lin/lin-559399`; the colon form `lin:lin-559399` is refused. A pair whose ids this
store owns (own `prefix` plus `legacy_prefixes`) is local and runs the v2 code
unchanged. Otherwise the other id must resolve through the registry
(`resolve_store`) to an existing row, or the verb refuses and names
`pm ticket stores` and `runtime-tools/pm/stores.json`. `dep A blocks B` mutates B's
store and prints `B <--blocked-by-- pA/A`; `dep A related B` mutates A's.
`unlink A B --type blocks` removes the `blocked-by` on B. A cycle that crosses stores
is not detected at write time.

Reading. All foreign reads are read-only, take no lock, and share one per-invocation
cache of opened stores. A store whose rows carry no `blocked-by` edge never touches
the registry.

- `is_ready` holds the local rule AND every `blocked-by` target resolves to a row with
  status `closed` (or a `source: self` archive-index row in the target store). A target
  that does not resolve (no registered owner, unreadable registry or store, missing
  row) is not satisfied: the gate stays hidden.
- `claim` refusal names `lin/lin-559399 (claimed)` or
  `lin/lin-559399 (unresolved: <reason>)`. `--force` is unchanged.
- `ready` text and `--json`: gated rows are absent, shapes unchanged.
- `summary` text gains `waiting on other stores:`, one `<id> <- <ref> (<status or
  reason>)` line per gated row; `--json` is frozen.
- `show` text lists cross-store blockers with their status on the `blocked_by:` line
  and adds `blocks (other stores): <prefix>/<id>` from a scan of live registry stores
  (only `show` pays for it); `--json` is local-only and unchanged.
- `tree` text lists the ticket's cross-store blockers as leaves under "blocked-by
  chain" and never recurses into a foreign store; `--json` is unchanged.
- `stores --check` additionally reports a cross-store edge whose target does not
  resolve, and a cross-store `blocks` edge held on the blocker.

### Lifecycle: `closure_reason` (mined from workctl, consumer cl-496fb8)

workctl's five-state lifecycle carried a closure reason distinct from the terminal
state itself ("closed, and *why*"). v2 adopts exactly this one field, because it has a
named consumer: `pm work close` (cl-496fb8) sets it when delegating to `ticket close`,
derived from the worker-return `STATUS:` line it just validated. No other workctl
lifecycle concept (principals, approval receipts, leases/worktree identity, evidence
adoption, projection bundles, ULID typed ids) is adopted here -- each needs its own
named consumer before it lands in this schema (full mining ledger: the report for this
ticket, not this spec).

- `closure_reason`: `null`, or one of `done | wont-fix | duplicate | superseded |
  abandoned`.
- MUST be `null` when `status != closed` (you cannot have a reason for a closure that
  has not happened).
- MAY be `null` when `status == closed` -- deliberately **not** a non-null-iff rule
  like `assignee`'s. A row closed before v2 existed has no recoverable reason, and
  `migrate_v1_to_v2.py` sets `closure_reason: null` for every row regardless of status
  (section 7) rather than guessing one from, say, the ticket's last note text. Only a
  write path that actually knows the reason (`pm work close`, a human `ticket close
  --reason <r>` once built) ever sets it non-null.

### In-flight hold (fr-d088b2)

A session whose claim legitimately stays open across turns (a gate coordinator waiting
on a hardware trip) declares it with `pm ticket claim <id> --as <name> --hold "<reason>"`
or `pm ticket hold <id> "<reason>"`. The row then carries
`hold: {"token": <8-hex session token>, "reason": <non-empty string>, "since": <timestamp>}`;
`token` is the same `sha256(session id)[:8]` as the assignee's, and only the claiming
session can set it. The key is **absent** on every row without a hold (rows without it
are byte-identical to before).

- `release`, `close` (any form) and `reopen` remove the key; `pm ticket hold <id> --clear`
  removes it alone.
- The Stop hook (`hooks/pm/stop.py`) does not block on a held claim whose `hold.token`
  matches the stopping session: it warns once per held claim per session and refreshes
  that session's heartbeat file. Held claims of other sessions are ignored; claims
  without a hold behave as before.
- `pm ticket summary` lists a **stale hold**: a held claim whose token has no heartbeat
  newer than 12 h (`HOLD_STALE_SECONDS`; the heartbeat is `<token>.seen` under
  `$PM_HOLD_STATE_DIR`, default `~/.claude/.tmp/pm-holds`). Text view only: the
  `summary --json` projection is frozen and unchanged.
- A v1 store refuses `--hold`/`hold` (no such key in its schema).

## 5. Body conventions (cl-888843 slot, no schema fields)

v2 reserves this section for the dispatchable-ticket body-heading convention
(epic cl-7cda15 decision 2 / ADR Q11's "Dispatchable ticket" paragraph): a ticket body
MAY carry four fixed markdown headings, `Done:`, `Writes:`, `Read first:`, `Do not:`,
each a short runnable/scoped statement as described in the ADR. This is a **body
convention, not a schema change** -- `body` stays a free-form string (section 4); no
`references` property and no required-heading enforcement is added by this spec.
`pm ticket lint` (cl-888843, a separate ticket) is the verb that checks for the four
headings and reports `dispatchable` / `missing: <heading>`; this spec only reserves
the one section so that ticket does not also have to touch `SPEC.md`.

## 6. Archive

Unchanged in shape from v1 section 6, with two renames: the per-year archive file is
`tickets-<yyyy>.jsonl` (was `issues-<yyyy>.jsonl`), matching the `tickets.jsonl`
rename; gitignore lines are `.pm/archive/*` / `!.pm/archive/archive-index.jsonl` (and,
per section 1, `.pm/lock`). `archive-index.jsonl` rows, `meta` provenance, and the
"missing path is not a problem" rule are all unchanged.

**Selecting rows (v2.2, fr-66d647).** `pm ticket archive <id> [<id> ...] [--closed-before
YYYY-MM-DD] [--dry-run]`. Named ids are the primary form: every id must be a closed row of
the store (`<prefix>/<id>` accepted, duplicates ignored). A row that is not closed is refused
with a line naming `pm ticket close <id>` first; an unknown id (including one already
archived) is refused; if any id is bad nothing moves (exit 1). `--closed-before` is an
optional filter, not a selector requirement: with ids it additionally requires each named
row to have been last updated before the date (else refused, all-or-nothing); alone it
selects every closed row updated before the date (the former behavior). Neither ids nor the
date is a refusal. The date test is `ticket_core.closed_before(rows, date)`, shared so
`list` can adopt it later. A row that stays live with `parent` naming a row being archived would fail I-09, so archiving that parent is refused (exit 1, nothing moves) unless its live children are archived in the same call; the date-only form instead skips such parents, prints one `skipped <id>: ...` line each, and archives the rest. Other edges (`blocks`, `discovered-from`, `related`) to an archived row resolve through the archive index and are not guarded. **Compacted ids (v2.5, fr-44a827).** A `subtasks` entry (section 4) is a tombstone, not a row: `list`, `board`, `overview`, `summary`, `ready` and `tree` never list it. `show <id>` (text and `--json`) returns a synthesized closed row: `id`, `title`, `kind: "task"`, `status: "closed"`, `parent` (the epic), `closure_reason` (the entry's `reason`), `created` and `updated` (the entry's `closed`), `assignee: null`, `body: ""`, `labels: []`, `edges: []`, `priority: 2`, `notes` (one `{ts, text}` from the entry's `note`, else `[]`), `findings` and `closed_by` when the entry has them, `compacted: true`, plus the derived keys a live row carries; the text form adds `compacted into <parent> on close`. `where <id> --mutate` refuses it exactly as a closed row (`already closed`); `close --findings <id>` accepts it. Any verb that would change it (`reopen`, `note`, `edit`, `claim`, `hold`, `release`, `reparent`, `dep`, `unlink`, `close`, `archive`, including as the target of a new edge, except a `discovered-from` edge at `create`, which may point at a compacted or archived id) exits 1 with `<id> was compacted into <parent> when it closed (<closed>); it cannot be changed. File a new ticket.` A store-level archive is the registry's `frozen` role (section 3),
not a second mechanism.

**Auto-archive and archived reads (v2.5, fr-44a827).** With `archive_closed_after_days` (section 3) the sweep archives eligible rows (day granularity: every row closed on one day becomes eligible together; with `compact_closed_after_days` also set, a closed `task` with a live epic parent and no `keep` label is left to compaction, never archived) with the same mechanics as the verb. The year file is appended to (`open(path, "a")`; a missing final newline is repaired first), never rewritten, so earlier lines stay byte-identical; duplicate ids are not checked. Index rows are appended in archive order (within one pass, by id), each epic's subtask rows directly after the epic's row; no order is guaranteed or validated. Archiving a row that carries `subtasks` also appends one index row per entry: `source: "self"`, the epic's `path`, `closed` = the entry's `closed`, `meta: {"compacted_into": "<epic id>"}` (`meta` was already free-form; the row key set is unchanged). Those ids resolve as closed wherever archived ids do; I-17 requires the epic's year-file row to list a `subtasks` entry with that id (checked when that year file is present). After an op that archived, only `archive/archive-index.jsonl` is committed (`pm: archive <n> closed`); this is bookkeeping, never fatal, skipped with one stderr line `pm: archive index not committed: <reason>` on a non-default branch or a git failure, and skipped silently when `git check-ignore` reports the index ignored or the store is not in a git checkout. `show <id>` (text and `--json`) of an id whose index row has `source: "self"` reads the row from `archive/<path>` and prints it as stored plus `archived: true` (text adds `archived: <path>`); for a `compacted_into` row it prints the synthesized tombstone row plus `archived: true`. A missing year file or row exits 1 with `<id> is archived in <path> but that file is not on this machine`. `tree <archived id>` exits 1 with `<id> is archived; tree needs a live ticket`; `where <archived id> --mutate` refuses as already closed; every mutating verb keeps its refusal.

## 7. `migrate_v1_to_v2.py` contract

Same module API as `runtime-tools/pm/ticket/spec/v1/migrate_v0_to_v1.py` (loaded the same way by
`ticket/src/ticket`'s `discover_migrations`/`_upgrade_one`): a single
module-level `migrate(root)` function, pure over `root`'s `config.json` and
`issues.jsonl` (the v1 filenames -- see section 0; the directory/file rename is the
runtime's job, cl-37cb07, not this module's), returning a summary object the caller
`str()`s into its report. Concretely it:

1. Loads `config.json`; sets `spec_version: 2`; adds `store_id` if absent, computed as
   `sha256(prefix + "|" + sorted(ids joined by "|"))[:12]` -- deterministic, a pure
   function of this store's own content, no RNG, no wall clock (section 3 requires
   `store_id` never be reassigned once set, so a pre-existing `store_id` is left
   untouched); adds `created_by: null` if absent.
2. For each row in `issues.jsonl`: wraps a non-null `assignee` that does not already
   match `agent:`/`human:`/`legacy:` as `legacy:<original>`; adds `closure_reason:
   null` if the key is absent (every v1 row lacks it, so this always fires once).
3. Touches no other file, makes no network call, never reorders rows, never changes
   `created`/`updated` -- same constraints v1's `upgrade` contract (v1 SPEC.md section
   7) already places on every migration step.

## 8. `create` contract (new; folds cl-a53655)

v1 never specified `create` (only `validate`/`upgrade`/`init`/`adopt`/`archive` were
normative verbs). v2 adds one requirement so the gap cl-a53655 found (create could
write a title `validate` would then reject) cannot recur:

```
<tool> ticket create <title> [...]
```

`create` MUST refuse (exit 1, no row written, no store mutation) a `title` that is
empty, multi-line, or longer than 200 chars -- the same check `validate`'s I-06
performs. Per the invariants.md R-11 "never synthesize" principle (cited by
cl-a53655's own fix-shape note), `create` MUST NOT silently truncate an over-length
title; truncation would discard text the author wrote. The operator-facing remedy is
to resubmit a title that fits.

## 9. `validate`/`upgrade`/`init`/`adopt` contracts

Unchanged from v1 sections 5, 7, 9 except for the renames already stated (section 1,
6) and the lock-gitignore requirement (section 1). `validate`'s exit codes, `--json`
shape, and step-text ordering are identical; `upgrade`'s copy-apply-validate-swap
sequence is identical; `init`/`adopt` additionally populate `store_id` (section 3) and
write the lock gitignore line (section 1).

`validate --json` covers the cases v1 sections 5 and 8 left open (cl-87442e). Exit 2
(no store found, or a required file unreadable) still prints the v1 object, with
`"ok": false`, `"spec_version": null`, `"problems": []` plus `"error"` and `"path"`
(`null` when no store was found), on stdout and nothing on stderr. `--workspace --json`
prints one JSON document, not one block per repo:
`{"ok": bool, "repos": [{"repo": <path>, "ok", "spec_version", "problems"[, "error",
"path"]}], "workspace": [<W-01/W-02 problems>]}`, with the same exit code as the human
form (the max over repos, at least 1 when `workspace` is non-empty). Human output is
unchanged.

`lint` is no longer a pure alias (fr-67554d): it prints exactly what `validate` prints
and exits with the same code, then one `WARN stale-path <id> <path>` line per path
cited in the body of a not-closed ticket (rows labelled `worker:codex` skipped) that
does not exist: a repo-relative path whose first segment is a directory at the store's
repo root, a `~/` path, or an absolute `/Users/<u>/` or `/home/<u>/` path (fr-d98ada;
other absolute roots and URLs are never checked). A body line that says the file is
added/new/created, and paths through `.tmp/` or `.worktrees/`, are skipped. It also
prints one `WARN local-path <id> <path>` per path under the repo's `.local/` directory
(the per-workstream raw-resource dump, fr-66b2df), existing or not, planned or not: a
ticket should point at the curated `docs/` copy. Warnings never change the exit code
and never appear in `validate`; under `--json` they go to stderr; `--workspace` and
exit 2 print none.

`upgrade` on a store already at spec_version 2 is a repair pass: under the store lock it
adds each absent required row key whose default is null or empty (`assignee`, `parent`,
`closure_reason` -> null; `body` -> `""`; `labels`, `edges`, `notes` -> `[]`), never
`id`, `title`, `kind`, `status`, `priority`, `created`, or `updated`. It re-validates and
writes (committed like any mutating verb) only if the store then validates clean;
otherwise it writes nothing and exits 1 listing the remaining problems. `--dry-run`
lists the row/key pairs it would add and writes nothing; a store with nothing to repair
prints `already at spec_version=2; nothing to upgrade` and exits 0. `validate` points at
this pass (`run: pm ticket upgrade`) for a missing backfillable key.

## 10. Out of scope for v2

Everything v1 section 11 excluded, plus: detecting a blocks-cycle that crosses stores
(the store registry is section 3, "Store registry"; cross-store edge resolution is
section 4), `pm ticket lint` and its body-
heading enforcement (cl-888843), sharding to one file per ticket (cl-8fe293).
