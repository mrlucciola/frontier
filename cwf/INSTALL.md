# CWF setup and Codex pilot

Python 3.11+ is required; Git is optional for ordinary text work. CWF uses only
the Python standard library. Start in `/Users/matthias/projects/frontier-clean/cwf`.
This component is independently usable without pm or repository initialization.

The source includes the repaired 0.1.0 candidate, its existing installer and
tests. No Frontier deployment pipeline is needed. [Operations](docs/OPERATIONS.md)
describes the general tool; the narrower steps here govern the C2 pilot.
Source filenames remain compatible with the existing package and relative skill
references. Do not run `scripts/author_content.py` during setup: it regenerates
authored content.

## Check the source before use

```sh
python3 -B -m unittest discover -s tests -v
python3 -B tests/qualify_codex.py
```

The first command checks local mechanics in disposable homes. The second uses
the installed Codex client's `config/read`, `skills/list` and `thread/start`
without `turn/start`: it checks global override selection, simulated base
deployment, fresh fallback, all-copy name exclusions, preserved settings and
fresh catalog rollback in a temporary configuration root. It prints JSON and
exits nonzero on failure. It creates no model request, copies no authentication
and changes neither HOME nor live configuration. A sandbox-helper failure is
an unproved client check: run this exact probe in an ordinary terminal, then
record its result on fc-2e70b4. It is not a semantic activation or cost test.
`python3 -B tests/qualify_codex.py --catalog-only` checks catalogs and settings
without starting threads; its `instruction_selection: NOT_TESTED` result leaves
the full host-side check outstanding.

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

The candidate [global entry](config/AGENTS.override.md) is the exact B2 accepted
entry (4170 UTF-8 bytes; SHA256
`888bb29edc2275ef35c716d93a175c30bcc33658983bbf0ff93a978a9b1c5e7f`).
Its only REM text retains the separate qualification gate. No REM wake or memory
hook belongs to this pilot. The override affects **every fresh Codex session on
that home**, including launches without skill exclusions. Existing sessions keep
their loaded context. Only reviewed launches with exclusions qualify for pilot
measurement.

C2 records the current candidate manifest digest, source revision, exact paths,
file types/modes/hashes, fallback/config/routing hashes and effective skill
configuration in fc-2e70b4. Resolve `CODEX_HOME` explicitly: this proposal expects
it unset or `/Users/matthias/.codex`. A different root requires reconciliation.
Reject existing override paths (including empty files/symlinks), foreign CWF
targets, changed owned files and pending transactions. Never overwrite/adopt a
collision. Recheck deployment manifests against the exact target list; the
current `instructions-codex` manifest targets only `~/.codex/AGENTS.md`.

Prepare a private install plan with `{"guidance":false}` and review every target.
Permitted runtime targets are `~/.local/share/cwf/releases/0.1.0`, its `current`
link, `~/.local/bin/cwf`, `~/.config/cwf/config.json`, the six
`~/.agents/skills/cwf-*` links, and CWF's receipt/transaction/cache state under
`~/.local/state/cwf`. C2 separately owns only `~/.codex/AGENTS.override.md`.
Do not edit base AGENTS, docs.AGENTS, config.toml, legacy skills, hooks,
permissions, memory stores, pm/wt internals or a shared continuity ledger.

Before activation, the operator rules on the concrete source/plan, global scope,
rollback owner C2, start time and `review_by` (three days after start by default).
No live activation is authorized merely by completing preparation. Record phases
in pm notes: prepared, runtime installed, override installed, client qualified,
measurement started, disabled, fallback verified, uninstalled; interrupted phases
remain incomplete. C2 retains its claim only during active work.

After that ruling, apply the reviewed runtime plan with the existing installer.
Verify the manifest and receipt. Create the reviewed override with exclusive
creation, never a copying command that can overwrite a foreign file:

```sh
python3 -B - <<'PY'
from pathlib import Path
import hashlib, os
assert os.environ.get('CODEX_HOME', str(Path.home()/'.codex')) == str(Path.home()/'.codex')
source = Path('config/AGENTS.override.md').read_bytes()
assert hashlib.sha256(source).hexdigest() == '888bb29edc2275ef35c716d93a175c30bcc33658983bbf0ff93a978a9b1c5e7f'
target = Path.home()/'.codex/AGENTS.override.md'
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'wb') as f:
    f.write(source)
PY
```

A crash or partial override write requires byte comparison and explicit recovery;
do not retry exclusive creation or launch into an incomplete phase.

## Fresh launch and first use

First obtain `config/read(cwd=<actual working root>, includeLayers=true)` and
`skills/list(forceReload=true)` from the selected client. Preserve the effective
`skills.config` entries **in order**, then append the nine disables below. A
different working root or newly added setting invalidates an old launch array.
The preparation-time frontier-clean result had no existing entries; only under
that still-verified condition is this complete array suitable:

```sh
cd /Users/matthias/projects/frontier-clean
codex -m gpt-6.1-sol -c 'model_reasoning_effort="high"' -c 'skills.config=[{name="design-pattern-language",enabled=false},{name="architecture-review",enabled=false},{name="implementation-planning",enabled=false},{name="dependency-decision",enabled=false},{name="validation-gate",enabled=false},{name="failure-retro",enabled=false},{name="docs-sync",enabled=false},{name="repo-onboarding",enabled=false},{name="session-continuity",enabled=false}]' 'Use $cwf-maintain to verify the scoped CWF installation. Inspect only the installed receipt and relevant doctor output; do not change configuration or write task or memory state.'
```

Use that launch only after activation and selection qualification. There is no
new launcher/profile or persistent settings file. Names cover all exact-name
copies; unexpected aliases need investigation. pm/wt, official documentation and
specialized skills remain available. Conflicting higher-priority or scoped repo
requirements stop/exclude the dependent pilot case; exclusions never waive them.

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
fc-e902b6, recording actual skill/procedure calls and mutations. A disabled
catalog entry is not proof of implicit/explicit no-cofire. Fresh rollback must
restore source selection and catalogs. C3 then owns paired/interleaved baseline
comparison using A2's frozen quality/cost thresholds; source size is not savings.

## Disable, rollback, remove and recover

Stop launching pilot sessions. Recheck the recorded fallback and pilot hashes
before each phase. Do not expose a drifted fallback or overwrite newer bytes.

```sh
~/.local/bin/cwf disable
```

This removes owned skill links and disables new runtime work. **It leaves the
separately owned global override in place.** After verifying the fallback is the
approved baseline, remove only an unchanged owned override:

```sh
python3 -B - <<'PY'
from pathlib import Path
import hashlib, os
assert os.environ.get('CODEX_HOME', str(Path.home()/'.codex')) == str(Path.home()/'.codex')
base = Path.home()/'.codex/AGENTS.md'
override = Path.home()/'.codex/AGENTS.override.md'
assert not base.is_symlink() and not override.is_symlink()
assert hashlib.sha256(base.read_bytes()).hexdigest() == '3c8ac846b29656cf0ae99ff1e9ae55e12f5eb17b642bfa060f49cd28f3c604f9'
assert hashlib.sha256(override.read_bytes()).hexdigest() == '888bb29edc2275ef35c716d93a175c30bcc33658983bbf0ff93a978a9b1c5e7f'
override.unlink()
PY
```

The fallback hash above is preparation-time evidence; if the approved activation
snapshot differs, reconcile and review the concrete removal command first.
Use a fresh client **without** the one-off exclusions to verify baseline source
and catalog; compare unrelated settings and files to the activation snapshots.
Then remove runtime integration:

```sh
~/.local/bin/cwf uninstall
```

`cwf rollback` instead reverts the last installation transaction; it neither
owns nor removes C2's override. Use only the operation matching the recorded
phase. Release/state retention is intentional; no purge or manual deletion.
If interrupted, run from this unchanged bundle, using the same target roots:

```sh
python3 -B cwf.py install recover
```

Recovery checks before/after snapshots and refuses ambiguous bytes. Preserve
foreign edits and record the exact incomplete phase and conflict on fc-2e70b4.
Never blanket-restore a global file. Already loaded sessions require restarting
before they can establish rollback behavior.
