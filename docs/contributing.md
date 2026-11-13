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
| `INSTALL.md` | When the component has `skills/`, `hooks/`, `instructions/`, `config/`, or `cli/` | Setup, first use, verification, disabling, and removal | `C-INSTALL` |

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

- `A-TITLE`: the first line is `# <Name> maintenance`.
- `A-OWNS`: the first paragraph after the title uses the word `owns`.
- `A-TABLE`: the first table has exactly the header `| Change | Read |` and at
  least one row with both cells filled.
- `A-RUN`: the first `sh` fence is the validation block, and the nearest
  non-blank line above it begins with `Run` and names where to run it.
- `A-CWD`: that line says `from the repository root`. Agent shells reset their
  working directory between commands, so a command that needs another directory
  cannot be run as written.
- `A-TARGET`: each command in the block begins with `python3`, and the script it
  names, or the `-s` directory and `-p` pattern of `-m unittest discover`,
  exists.

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

## Setup and integration standards

- Symlink skills into the provider's supported discovery location.
- Expose command-line executables through symlinks in `~/.local/bin` when needed.
- Run hooks from their component directory wherever supported. Add provider-side
  symlinks only where the provider requires files at a particular location.
- Document the minimal configuration needed to register hooks, expose skills, and
  load instructions. Preserve unrelated user configuration during setup and removal.
- Keep shared component state in a provider-independent location where practical,
  such as `~/.local/state/concepts/`. Document current paths and any migration steps.
- Begin with clear operator instructions. Add small setup scripts when actual use
  demonstrates repetitive work worth automating.

## Documentation and validation

Write component setup guides as concise walkthroughs with enough explanation to
understand each step. Include prerequisites, copyable commands, expected results,
and instructions for disabling and removing the integration. Explain how removal
affects user data.

Put validation commands in the component's `AGENTS.md` and update instructions
when behavior or setup changes. Keep component tests inside the component and
runnable with Python's standard library. Measure context and hook overhead before
making performance claims.

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

| Component | Rule | Reason |
| --- | --- | --- |
| `cwf` | `C-CLAUDE` | Every regular file under `cwf/` becomes part of its release manifest. |
| `cwf` | `A-TABLE` | The route table header is `Work`; `cwf/` is not edited for repository conventions. |
| `cwf` | `A-CWD` | cwf tests are documented to run from `cwf/`. |
| `cwf` | `L-ROOT` | cwf routing documents use relative links; `cwf/` is not edited for repository conventions. |
