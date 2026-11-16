# Contribution standards

Read the [behavioral contract](/README.md#behavioral-contract) for shared
requirements. This page says where a component's files go and what its routing
documents contain. Component guides describe their current implementation and
supported setup. `docs/check_structure.py` enforces each rule tagged with an id
below; agreed deviations are recorded under [Exemptions](#exemptions).

## Components

Each top-level directory with tracked files is a component, except `docs/` and
directories beginning with `.`. `docs/` holds shared documentation and the
structure check. Untracked and ignored directories are not checked until their
first file is tracked.

A component brought in from elsewhere conforms to this page and the
[component principles](/docs/component-principles.md) before its first use, or
stays out of the index until it does.

- `I-UNINDEXED`: every component has a row in the [component index](/README.md#components).
- `I-ROW`: the row links `/<component>/README.md` in its first column and
  `/<component>/AGENTS.md` in its third.
- `I-MISSING`: every indexed directory exists.

## Required files

| File | Required | Contents | Rule |
| --- | --- | --- | --- |
| `AGENTS.md` | Always | Maintenance routes and validation, in the [template](#agentsmd-template) form | `C-AGENTS` |
| `CLAUDE.md` | Always | Exactly `@AGENTS.md`, so Claude loads the component's `AGENTS.md` when it works in the directory | `C-CLAUDE` |
| `README.md` | Always | Purpose, supported providers, and links to `AGENTS.md` and to `INSTALL.md` when present | `C-README`, `C-README-ROUTE` |
| `INSTALL.md` | When the component has `skills/`, `hooks/`, `instructions/`, `config/`, or `cli/` | What `deploy.sh` links and where, how to run and verify it, and the commands that remove it | `C-INSTALL` |
| `deploy.sh` | Same condition as `INSTALL.md` | The component's whole deployment, in the [deploy script](#deploy-script) form | Not checked yet |

A component without provider integration documents its setup in `README.md`.
The repository root has `CLAUDE.md` (exactly `@AGENTS.md`), `AGENTS.md`,
`README.md`, and this page (`R-FILE`, `R-CLAUDE`).

## Optional directories

Create a directory only for files the component has. Use these names for these
roles. A component that needs another role names its directory in `AGENTS.md`
or `README.md`.

```text
instructions/       Agent instructions
skills/<name>/      A skill and its supporting files, including scripts only that skill runs
hooks/              Event hooks
cli/                Executables exposed on PATH
tools/<name>/       Internal runtime tools; a tool may keep its own tests/ beside it
config/             Provider configuration fragments
tests/              Component tests
docs/               Detailed design and reference documentation
```

Document exact provider destinations, such as paths under `~/.claude/`,
`~/.codex/`, or `~/.config/opencode/`, in the component's setup guide.

## `AGENTS.md` template

````text
# <Component> maintenance

<What this component, or a named file in it, owns.>

| Change | Read |
| --- | --- |
| <Behavior being changed> | <Link to the owning file or guide, and what to look for> |

<Constraints that hold across routes.>

Run the <component> checks from the repository root.

```sh
python3 -B <component>/tests/test_<name>.py
```
````

Open with what the component, or a named file in it, owns; the check does not
read that paragraph. The route table's first header may be `Work` instead of
`Change`.

- `A-TITLE`: the first line is `# <Name> maintenance`.
- `A-TABLE`: the first table has exactly two columns, headed `Change` or `Work`
  and then `Read`, and at least one row with both cells filled.
- `A-RUN`: the first `sh` fence is the validation block, and the paragraph
  directly above it begins with `Run` and names where to run it.
- `A-CWD`: that paragraph says `from the repository root`. Agent shells reset
  their working directory between commands, so a command that needs another
  directory cannot be run as written.
- `A-TARGET`: each command in the block begins with `python3` or
  `/usr/bin/python3`, and the script it names, or the `-s` directory and `-p`
  pattern of `-m unittest discover`, exists. Later `sh` fences are not checked.

## Links

Routing documents are the root `CLAUDE.md`, `AGENTS.md`, and `README.md`, every
`docs/*.md` page, and each component's `AGENTS.md`, `README.md`, and
`INSTALL.md`. In them:

- `L-ROOT`: a local link target is repository-root-relative with a leading `/`,
  such as `/docs/contributing.md`. Claude's documentation hook writes this form
  on every edit; write it by hand elsewhere. Inside a worktree, `/` is the
  worktree root. Same-page `#fragment` links are allowed.
- `L-TARGET`: the target exists inside the repository.
- `L-ANCHOR`: a `#fragment` on a markdown target matches one of its headings.

External URLs, code spans, and fenced blocks are not checked.

## Deploy script

A component is deployed by `<component>/deploy.sh` and by nothing else. It is a
zsh script with no arguments, and it may do only these things:

- create a provider directory with `mkdir -p`;
- symlink a skill, hook, or executable from the provider's location into this
  checkout with `ln -sfn`;
- replace the component's marked block in a shared instruction file with the
  contents of `instructions/<provider>.<file>.md`.

It never copies a component file, generates one, writes state, records a version,
or reaches the network. The script must hold these properties:

- Running it any number of times leaves the same result as running it once.
- It touches only the paths it names. In a shared file it changes only the bytes
  from `<!-- NAME:BEGIN -->` to `<!-- NAME:END -->`, where `NAME` is the component
  name in capitals; every other byte is kept, and a file without the markers gets
  the block appended.
- The checkout wins. A hand edit to a deployed copy lasts until the next run, so
  durable edits go in the source file.
- A missing source file ends the script with exit 1 and a line naming the file,
  before anything is written.
- It stays under 60 lines. A step that does not fit is a sign the component is
  doing something this page does not allow.

Three things stay out of the script. Executable bits are committed. A settings
file edit, such as registering a hook, is a manual step in `INSTALL.md` that
preserves unrelated configuration, until a second component needs the same edit.
Removal is the list of commands in `INSTALL.md` that delete the links and the
block.

````text
#!/usr/bin/env zsh
# Deploy <component>: links into this checkout and one marked block. Safe to run again.
here="${0:A:h}"
snippet="$here/instructions/opencode.AGENTS.md"
[[ -r "$snippet" ]] || { print -u2 "missing $snippet"; exit 1 }

# opencode: skills
dest="$HOME/.config/opencode/skills"
mkdir -p "$dest"
for d in "$here/skills"/*(/); do
	ln -sfn "$d" "$dest/${d:t}"
done

# command line
mkdir -p "$HOME/.local/bin"
ln -sfn "$here/cli/<name>" "$HOME/.local/bin/<name>"

# opencode: instruction block
target="$HOME/.config/opencode/AGENTS.md"
begin='<!-- NAME:BEGIN -->' end='<!-- NAME:END -->' nl=$'\n'
block="$begin$nl$(<"$snippet")$nl$end"
text=""
[[ -f "$target" ]] && { text="$(cat "$target"; print -n x)"; text="${text%x}" }
if [[ "$text" == *"$begin"*"$end"* ]]; then
	text="${text%%"$begin"*}$block${text#*"$end"}"
else
	[[ -n "$text" && "$text" != *"$nl" ]] && text+="$nl"
	text+="${text:+$nl}$block$nl"
fi
mkdir -p "${target:h}"
print -rn -- "$text" >"$target"
````

The sentinel `x` keeps zsh from dropping the file's trailing newlines, which is
what makes the write byte-exact outside the markers. `cwf/deploy.sh` is the first
script of this kind. The structure check does not read deploy scripts yet; a
reviewer holds them to this section.

Each deploy script has one black-box test: run it twice with `HOME` set to a
temporary directory that already holds other text in the shared file, and compare
the two results and the bytes outside the markers.

## State outside the repository

Anything a component keeps under `~/.local/state` or `~/.local/share` is optional.
Deleting it must not stop the component's skills, instructions, or command line
from working, and the component recreates what it needs on the next write. Keep
such state in a provider-independent location, and document its path and what is
lost when it is deleted.

## Documentation and validation

`INSTALL.md` is short: a table of each source path and the destination
`deploy.sh` links it to, the command that runs it, how to verify the result in a
fresh session, and the exact commands that remove it, with what removal does to
user data.

Put validation commands in the component's `AGENTS.md` and update instructions
when behavior or setup changes. Keep component tests inside the component. Write
a component's code and tests by the [component principles](/docs/component-principles.md).
A component that departs from them records the departure and its reason in its
`AGENTS.md`. A test that fixes behavior the maintainer must not change is named in
the route table, with who may change it.

Run the structure check from the repository root after changing a routing
document, a component's top-level layout, or the component index.

```sh
python3 -B docs/check_structure.py
python3 -B docs/test_check_structure.py
```

## Exemptions

An exemption is a row in this table, never a change to the check. It covers
every violation of one rule in one component. The check fails on a row that
matches no violation (`X-STALE`) and on a row that names an unknown component,
an unknown rule, a rule that cannot be exempted, or no reason (`X-ROW`). Delete
the row when the component conforms.

An exemption records a temporary gap, and its reason names the ticket that closes
it. A reason that restates the component's own design is not a reason: the design
is what has to change.

| Component | Rule | Reason |
| --- | --- | --- |
| `cwf` | `C-CLAUDE` | Legacy installer copies every file under `cwf/` into a release; fc-6441eb removes the installer and this row. |
| `cwf` | `A-CWD` | cwf tests are documented to run from `cwf/`; fc-6441eb moves the command to the repository root and removes this row. |
