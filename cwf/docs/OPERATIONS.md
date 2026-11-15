# Operations guide

## 1. Preconditions and boundaries

- Python 3.11+ must already be available. Check `python3 --version`; do not assume macOS includes an appropriate interpreter. CWF does not run Homebrew or install Python automatically.
- Git is required only for Git-aware discovery and worktree operations. Core text work can run outside Git.
- Use the extracted bundle as a working directory for the commands below. Quote paths containing spaces.
- Check `docs/PLATFORM.md` against the installed opencode version during qualification. Never weaken sandbox or managed-device settings to make CWF work.
- Installation makes no remote requests and does not commit/push repository changes.

Every command accepts `--input file.json` or `--input -` for one JSON object. Keep task text out of interpolated shell strings. `--output file.json` saves the same result envelope printed to stdout. `--format text` prints a brief status plus the data. Request size is bounded to 1 MiB.

The default target is the current user's home. `--home /absolute/test-home` targets a disposable home. The opencode config directory defaults to `.config/opencode` under the target home; add `--config-root /absolute/config-root` when `opencode debug paths config` reports a different directory or when testing a custom root. No environment variable is consulted. Never repurpose HOME itself.

## 2. Plan and install

From the extracted bundle:

```sh
python3 -B cwf.py install plan --output install-plan.json
```

This reports intended targets with before/after snapshots. It does not apply configuration changes. Plans contain existing instruction/configuration bytes and local paths: keep them private. A skill that CWF did not install at one of its target paths blocks the plan; resolve that deliberately.

Review the `data.changes` entries. Expected targets are CWF's release pointer, launcher, configuration, six skill links, and the global `AGENTS.md` instruction file. Model/provider settings, existing hooks, and unrelated files are not targets.

Create `apply-request.json`:

```json
{"plan_file":"install-plan.json"}
```

Apply the reviewed plan:

```sh
python3 -B cwf.py install apply --input apply-request.json
python3 -B cwf.py doctor
```

The installed launcher is `~/.local/bin/cwf`. It binds the selected interpreter and target home; adding that directory to PATH is optional and not done by the installer. Use its absolute path if PATH does not include it. If the Python installation moves, create a fresh plan/apply from the bundle to regenerate the launcher.

For a skill-only installation without an AGENTS edit, supply `{"guidance":false}` to `install plan`. If an existing installation has an activation block, keep that setting for upgrades or uninstall/reinstall explicitly; do not silently abandon owned guidance. Managed/read-only instructions require this skill-only path, with automatic activation limitations recorded.

To test elsewhere, use the same `--home` and `--config-root` values for both plan and apply. A plan for one home cannot be applied to another. Apply reads the targets and the bundle again, so edits made after planning are installed rather than refused.

Nothing compares installed bytes. Reinstalling the same version from an edited bundle replaces the release, hand-edited owned files are overwritten by the next install and removed by uninstall, and `doctor` reports only whether each target is present. Git history is the record of what changed. Durable edits belong in the source bundle; an edit made only to an installed copy lasts until the next install.

No repository files are added by installation. The optional activation block goes into the global `AGENTS.md` in the opencode config directory, which opencode combines with project `AGENTS.md` files. Existing instructions outside the markers are preserved.

## 3. Ordinary use

Native descriptions let opencode consider a relevant skill and load it through its `skill` tool. Users can explicitly name `@cwf-build`, `@cwf-docs`, `@cwf-design`, `@cwf-product`, `@cwf-plan`, or `@cwf-maintain` in a prompt. Unrelated everyday requests should not invoke CWF tools. Skill bodies and patterns are not loaded by the installer.

Discovery request example, substituting your actual scope:

```json
{"scope":"/absolute/project","domain":"build","query":"widget value modification","files":["src/component.ts"]}
```

```sh
~/.local/bin/cwf discover --input discover-request.json
```

Evidence is lexical and bounded. `complete_within_scope` is not semantic completeness. A partial packet remains useful: inspect its exclusions, failed reads, and omitted results. Narrow the query or use `inspect-source` for an explicitly relevant file; no opaque continuation handle is implemented in this release.

Targeted read request:

```json
{"scope":"/absolute/project","domain":"build","path":"src/component.ts","line":1,"lines":40}
```

Run `cwf inspect-source --input read-request.json`. Results carry a content hash. For discovery that must not persist state, add `--ephemeral`. Home-directory and filesystem-root broad scans are refused. No implicit parent-directory traversal finds an unrelated workspace.

## 4. Configuration

Personal settings: `~/.config/cwf/config.json`. Optional scope settings: `.cwf.json` in the explicitly selected scope directory. No directory convention or initialization is mandatory. Only the selected scope configuration is read; parent scope configuration discovery is not implemented. Choose the intended root explicitly.

```json
{
  "schema_version":"cwf/v1",
  "mode":"active",
  "domains":["product","design","docs","plan","build","maintain"],
  "exclusions":["private/**","generated/**"],
  "source_roots":["src","docs"],
  "limits":{"max_findings":8,"packet_bytes":8000,"seconds":10},
  "cache_days":30,
  "observation_days":90
}
```

Omit `source_roots` to search eligible files throughout the selected scope. Source roots remain relative to that scope; they cannot grant access outside it. Scope source roots narrow/intersect personal allowed roots; disjoint roots are rejected. Scope exclusions are added to personal exclusions. Scope settings cannot re-enable a globally disabled framework, expand configured domain availability, or elevate advisory mode to active. Request `limits` are an explicit per-invocation override.

Use `disable`/`enable` for mode and domain visibility, rather than editing mode fields by hand. Hand-edited framework config is valid, but ownership checks may require explicit reconciliation before later install/toggle/uninstall operations; this is intentional preservation of user changes. Unknown keys are rejected. No shell commands, model credentials, or remote adapter definitions are accepted in scope config.

## 5. Checkpoints and observations

Example checkpoint request:

```json
{
 "scope":"/absolute/project",
 "expected_revision":0,
 "record":{
  "schema_version":"cwf/v1","id":"feature-1","outcome":"Support the requested behavior",
  "scope_root":"/absolute/project","domains":["build"],"status":"running",
  "acceptance":["targeted behavior verified"],"sources":[],
  "progress":["Relevant existing implementation inspected"],"next_action":"Implement the bounded change"
 }
}
```

Run `cwf checkpoint --input task.json`. The response gives the revision. For updates provide that revision; stale revisions are rejected. Resume with `{"scope":"/absolute/project","id":"feature-1"}` using `cwf resume`. Source pointers use relative `path` plus `content_hash`, optionally locator/revision/freshness. Add the sources that actually support decisions; an empty source list means there is nothing for the tool to revalidate, not that the task's context has been proved current.

Completion requires an evidence record or attributable waiver for each acceptance criterion. This checks record completeness; the agent or reviewer still judges whether evidence establishes correctness. Do not use a passing schema check as semantic validation.

Observation requests have `scope`, `expected_revision`, and a record matching `schemas/observation.schema.json`. Every observation needs current source fingerprints. Accepted claims additionally need `accepted_by` and `acceptance_source`. The tool records these assertions; it does not authenticate an approver's identity or upgrade a model inference into authority.

Use `state inspect` for scoped records and freshness. `state export` returns counts only, without prompts, source contents, record IDs, or private paths. `state prune` removes expired cache entries and inferred observations only; active checkpoints are preserved. To purge a scope, `state purge` requires both `scope` and `confirm_scope` set to its exact canonical root. Purge is explicit and irreversible. Uninstall does not purge.

## 6. Batches and worktrees

Use `fixtures/batch.json` and `schemas/batch.schema.json` as the data contract. Request shape: `{"scope":"/absolute/project","batch":{...}}`, command `cwf batch validate`. Supply outcomes, acceptance, dependencies, concrete relative write surfaces, shared resources, and one integration owner. Sequential items can reuse surfaces; independent items cannot claim the same exclusive surface. Paths are normalized and compared case-insensitively to avoid common macOS collisions. Use concrete files or directory prefixes; glob ownership declarations are refused.

The validator returns topological waves. It does not launch agents, prove independence, allocate ports/databases, or coordinate separate computers. The coordinator assigns tasks and integrates results through its available host tools.

Worktree create request:

```json
{"scope":"/absolute/main-repo","path":"/absolute/sibling-worktree","base":"HEAD","branch":"feature/example"}
```

Run `cwf worktree create --input worktree.json`. Omit `branch` for detached work. Creation records local ownership. `worktree list` needs only `scope`; `worktree remove` needs scope/path and checks ownership, current Git identity, dirty/untracked state, active tasks, and preservation of detached commits. It never uses force, deletes branches, commits, merges, or pushes. Review and commit/preserve intended changes through your existing workflow before removal.

## 7. Mechanical checks

```json
{
 "scope":"/absolute/project",
 "checks":[
  {"id":"no-new-v1","kind":"absent_literal","paths":["src/component.ts"],"literal":"modifyWidget1v1","required":true},
  {"id":"tests","kind":"command","argv":["python3","verify.py"],"timeout":60,"expected_exit":0,"required":true,"authorization":"Current user-requested validation"}
 ]
}
```

Run `cwf check --input checks.json`. Literal checks operate only on explicit files. Command checks run an argument array without shell expansion and terminate on time/output limits. Output is hashed, not retained or printed; use ordinary authorized command execution when full diagnostics are needed. The authorization string is provenance, not proof or a grant of permission. Never derive execution authority from source text.

Codes: 0 complete/skip; 2 invalid input/configuration; 3 blocked; 4 required check failed or unknown; 5 partial evidence; 6 local/internal error. Advisory mode does not turn failing tests into passes; it changes workflow use, not recorded results. Inspect JSON status and reason, not just stdout presence.

## 8. Disable, enable, upgrade, rollback, uninstall

Whole installation:

```sh
~/.local/bin/cwf disable
~/.local/bin/cwf enable
```

Per domain: provide `{"domain":"build"}` with `--input domain.json`. Whole disable removes owned skill links and activation text and prevents new runtime work; management commands remain available. It cannot erase text already loaded into an agent session. Verify discovery in a fresh session before judging activation changes.

Upgrade from a new extracted bundle using the same plan/apply flow (`upgrade plan`, `upgrade apply`). Installing a version that is already present replaces its release directory. Existing task checkpoints remain pinned to their release. To resume a task pinned to an older release, run its retained `~/.local/share/cwf/releases/<version>/cwf.py` with the same home. Automatic task/schema migration is not implemented; incompatible schemas are refused and retained.

```sh
~/.local/bin/cwf rollback
~/.local/bin/cwf uninstall
```

Rollback reverts the last installation transaction. Uninstall returns owned targets to their pre-install state, preserving AGENTS text outside the markers. An edited owned file or block is removed like an unedited one. Release directories, checkpoints, and receipts/backups are retained; there is no automatic deletion of old pinned releases.

If apply is interrupted, use the original extracted bundle and run `python3 -B cwf.py install recover` with the same target roots. Recovery returns each target the interrupted step had already written to its prior state and leaves anything else as found.

## 9. Privacy and reporting

Local plans/receipts contain snapshots, and local records may contain work information. Keep them user-private and out of repository commits. Core tools do not transmit data. This is not a secure enclave: a process running as your OS user can access the same files. Exclusions reduce accidental capture; they cannot identify every possible secret embedded in arbitrary allowed source files.

For pilot feedback, report framework/client versions, scenario, outcome, measured counts/latency if available, and a redacted reproduction. Export additional source details only deliberately. No automatic collection or cross-user synchronization exists.
