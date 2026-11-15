# CWF setup for opencode

Python 3.11+ is required; Git is optional for ordinary text work. CWF uses only
the Python standard library. Start in `/Users/matthias/projects/frontier-clean/cwf`.
This component is independently usable without pm or repository initialization.

The source includes the repaired 0.1.0 candidate, its existing installer and
tests. No Frontier deployment pipeline is needed. [Operations](/cwf/docs/OPERATIONS.md)
describes the general tool; the narrower steps here govern the C2 pilot.
Source filenames remain compatible with the existing package and relative skill
references. Do not run `scripts/author_content.py` during setup: it regenerates
authored content.

## Provider destinations

| Path | Owner | Written by CWF |
| --- | --- | --- |
| `~/.agents/skills/cwf-<domain>` (six links) | CWF | Install, enable, disable, uninstall |
| `~/.config/opencode/AGENTS.md` | Operator | Only with `{"guidance":true}`: one owned block; never in the pilot |
| `~/.config/opencode/opencode.json` | Operator | Never read or written |
| `~/.local/share/cwf`, `~/.local/bin/cwf`, `~/.config/cwf/config.json`, `~/.local/state/cwf` | CWF | Release, launcher, settings, receipts and transactions |

`~/.agents/skills` is a documented opencode global skill root. The config
directory defaults to `<home>/.config/opencode`; when `opencode debug paths config`
prints another directory, pass it as `--config-root` on every command. CWF reads
no environment variable for it.

## Check the source before use

```sh
python3 -B -m unittest discover -s tests -v
```

This checks local mechanics in disposable homes. There is no opencode client
probe: whether a session discovers the six linked skills, and which instruction
sources it loads, is unqualified until checked by hand in a fresh session and
recorded on fc-2e70b4. The opencode documentation does not say whether symlinked
skill directories are followed.

For a complete disposable install/use/removal example, use a private canonical
directory and the same `--home` for every command:

```sh
cwf_test_home=$(mktemp -d /private/tmp/cwf-home.XXXXXX)
python3 -B cwf.py --home "$cwf_test_home" install plan --input - --output "$cwf_test_home/plan.json" <<'JSON'
{"guidance":false}
JSON
python3 -B - "$cwf_test_home" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
(p / 'apply.json').write_text(json.dumps({'plan_file': str(p / 'plan.json')}))
PY
# Review the plan's data.changes before applying it.
python3 -B cwf.py --home "$cwf_test_home" install apply --input "$cwf_test_home/apply.json"
"$cwf_test_home/.local/bin/cwf" doctor
"$cwf_test_home/.local/bin/cwf" disable
"$cwf_test_home/.local/bin/cwf" enable
"$cwf_test_home/.local/bin/cwf" uninstall
```

Expected: six namespaced skill links, launcher/current/config and an installation
receipt; no AGENTS edit. Disabling removes the six links, enabling restores them,
and uninstall restores owned targets. Retained releases and transaction state
are deliberate. Do not delete them as part of removal.

## Live pilot preparation and ruling

The candidate [global entry](/cwf/config/global-entry.md) is the exact B2 accepted
entry (4170 UTF-8 bytes; SHA256
`888bb29edc2275ef35c716d93a175c30bcc33658983bbf0ff93a978a9b1c5e7f`).
Its only REM text retains the separate qualification gate. No REM wake or memory
hook belongs to this pilot.

How the entry reaches opencode sessions is **not decided**. opencode has no
override file: it combines the global `AGENTS.md`, project `AGENTS.md` files and
`instructions` entries from `opencode.json`. The entry can therefore only be
added beside the existing global rules, either as an `instructions` entry or as
text in the global `AGENTS.md`; it cannot replace them. Either route changes an
operator-owned file and affects every fresh opencode session on that home.
fc-2e70b4 rules on the route; until then the pilot is skill-only and nothing in
`~/.config/opencode` changes.

C2 records the plan's `bundle_digest`, source revision, exact paths,
file types/modes/hashes, the global `AGENTS.md` and `opencode.json` hashes, and
the skill permission rules in effect in fc-2e70b4. This proposal expects the
config directory `/Users/matthias/.config/opencode`; a different root requires
reconciliation. Reject foreign CWF targets, changed owned files and pending
transactions. Never overwrite/adopt a collision. What deploys the existing
`~/.config/opencode/AGENTS.md` is not established; establish it before proposing
any edit there.

Prepare a private install plan with `{"guidance":false}` and review every target.
Permitted runtime targets are `~/.local/share/cwf/releases/0.1.0`, its `current`
link, `~/.local/bin/cwf`, `~/.config/cwf/config.json`, the six
`~/.agents/skills/cwf-*` links, and CWF's receipt/transaction/cache state under
`~/.local/state/cwf`. Do not edit the global `AGENTS.md`, `opencode.json`,
legacy skills, plugins, permissions, memory stores, pm/wt internals or a shared
continuity ledger.

Before activation, the operator rules on the concrete source/plan, global scope,
rollback owner C2, start time and `review_by` (three days after start by default).
No live activation is authorized merely by completing preparation. Record phases
in pm notes: prepared, runtime installed, client qualified, measurement started,
disabled, baseline verified, uninstalled; interrupted phases remain incomplete.
C2 retains its claim only during active work.

After that ruling, apply the reviewed runtime plan with the existing installer
and verify the receipt.

## Fresh session and first use

The nine legacy skills (`design-pattern-language`, `architecture-review`,
`implementation-planning`, `dependency-decision`, `validation-gate`,
`failure-retro`, `docs-sync`, `repo-onboarding`, `session-continuity`) stay
available beside CWF unless excluded. opencode documents no per-launch skill
exclusion; its mechanism is persistent `permissions` rules in `opencode.json`:

```json
{ "permissions": [ { "action": "skill", "resource": "docs-sync", "effect": "deny" } ] }
```

Rules run in order and the last match wins. Skill IDs come from the skill's
path, so confirm the exact IDs in a session before writing rules. Which file
holds the rules, who owns them, and whether a denied skill is still advertised
to the model are open on fc-2e70b4. No rule has been added; without them a pilot
session measures CWF alongside the legacy skills.

After activation, start a fresh session and send the first prompt:

```sh
cd /Users/matthias/projects/frontier-clean
opencode
```

```text
Use @cwf-maintain to verify the scoped CWF installation. Inspect only the installed receipt and relevant doctor output; do not change configuration or write task or memory state.
```

No model or reasoning setting is fixed here; record what the session used. pm/wt,
official documentation and specialized skills remain available. Conflicting
higher-priority or scoped repo requirements stop/exclude the dependent pilot
case; exclusions never waive them.

For ordinary tool use on an explicitly authorized non-Git directory:

```sh
~/.local/bin/cwf discover --ephemeral --input - <<'JSON'
{"scope":"/absolute/selected-directory","domain":"build","query":"widget","files":["source.txt"]}
JSON
```

Substitute real authorized paths. Results are bounded lexical evidence. Partial
or empty results do not prove absence or semantic equivalence. No `.pm`, `.icm`
or repository initialization is required. Ticketed pilot work writes continuation
only to pm notes; never CWF checkpoint/observe or competing worktree state.

Before measurements, execute the B2 positive P1-P7 and negative N1-N12 cases in
fc-e902b6, recording actual skill/procedure calls and mutations. A denied skill
is not proof of implicit/explicit no-cofire. Fresh rollback must restore the
skill catalog. C3 then owns paired/interleaved baseline comparison using A2's
frozen quality/cost thresholds; source size is not savings.

## Disable, rollback, remove and recover

Stop launching pilot sessions. Recheck the recorded hashes before each phase.

```sh
~/.local/bin/cwf disable
```

This removes owned skill links and disables new runtime work. It touches nothing
in `~/.config/opencode`: a global entry or permission rules that C2 added there
are removed by C2, by the reviewed reverse of the step that added them. Use a
fresh session to verify the baseline skill catalog; compare unrelated settings
and files to the activation snapshots. Then remove runtime integration:

```sh
~/.local/bin/cwf uninstall
```

`cwf rollback` instead reverts the last installation transaction; it neither
owns nor removes anything C2 added to the opencode config directory. Use only
the operation matching the recorded phase. Release/state retention is
intentional; no purge or manual deletion. If interrupted, run from this
unchanged bundle, using the same target roots:

```sh
python3 -B cwf.py install recover
```

Recovery checks before/after snapshots and refuses ambiguous bytes. Preserve
foreign edits and record the exact incomplete phase and conflict on fc-2e70b4.
Never blanket-restore a global file. Already loaded sessions require restarting
before they can establish rollback behavior.
