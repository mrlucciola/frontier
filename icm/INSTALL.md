# Setup: ICM

Manual setup for Kiro CLI v3, the only provider this component ships configuration
for. You get two skills (`icm-architect` builds workspaces, `icm-run` executes
stages), a SessionStart hook that tells the agent when the working directory is an
ICM workspace, one permission rule so a workspace's own `_tools/*.py` scripts run
without prompts, and one steering instruction file.

The skills are linked from this directory and the hook runs from it, so the
repository must stay in place.

| Source in this component | Kiro destination | How |
| --- | --- | --- |
| `skills/icm-architect/` | `~/.kiro/skills/icm-architect` | symlink |
| `skills/icm-run/` | `~/.kiro/skills/icm-run` | symlink |
| `hooks/icm-detect.sh` | none | run from this component by the registered command |
| `config/kiro/hooks.json` | `~/.kiro/hooks/icm.json` | copied, or merged by hand |
| `instructions/icm.md` | `~/.kiro/steering/icm.md` | copied once |

Hook registration and trust mechanics on kiro v3 are CONFIRM items (see
[the branch policy](/docs/kiro-branch.md)); until recon settles them, follow the
steps here and verify the hook fires in step 4.

## Prerequisites

- macOS or Linux with `bash` and `python3` 3.9 or newer.
- Kiro CLI installed; agents run through `kiro-cli --v3`.
- This repository checked out at `~/projects/frontier-clean`. If it lives elsewhere,
  substitute that path in every command and in the hook command of step 2.

Setup uses no network.

## 1. Link the skills

Confirm nothing is already at the destinations. `ln -s` onto an existing directory
would create the link inside it instead of failing.

```sh
ls -d ~/.kiro/skills/icm-architect ~/.kiro/skills/icm-run
# expect: "No such file or directory" twice; inspect anything that is listed before going on
```

```sh
mkdir -p ~/.kiro/skills
ln -s ~/projects/frontier-clean/icm/skills/icm-architect ~/.kiro/skills/icm-architect
ln -s ~/projects/frontier-clean/icm/skills/icm-run ~/.kiro/skills/icm-run
ls ~/.kiro/skills/icm-architect/SKILL.md ~/.kiro/skills/icm-run/SKILL.md
# expect: two paths listed
```

## 2. Register the hook

The hook is a standalone command-hook file. It lives in
[config/kiro/hooks.json](/icm/config/kiro/hooks.json); the registered command is
the hook's path in this component, nothing is linked into `~/.kiro/hooks/`.

```sh
mkdir -p ~/.kiro/hooks
cp ~/projects/frontier-clean/icm/config/kiro/hooks.json ~/.kiro/hooks/icm.json
python3 -m json.tool ~/.kiro/hooks/icm.json /dev/null
# expect: no output (the file parses)
```

If `~/.kiro/hooks/icm.json` already exists and holds your own entries, merge the
`SessionStart` group into it by hand instead of overwriting.

Permissions: workspaces run their own `_tools/*.py` scripts, so add a rule allowing
`python3 _tools/*` to `permissions.yaml`. Review it by hand; a deploy step never
writes that file. The `permissions.yaml` schema is a CONFIRM item, so write the
rule in whatever form the runtime's current docs show.

## 3. Add the steering instruction

[instructions/icm.md](/icm/instructions/icm.md) is the "## ICM workspaces" section.
Copy it once as a steering file.

```sh
mkdir -p ~/.kiro/steering
cp ~/projects/frontier-clean/icm/instructions/icm.md ~/.kiro/steering/icm.md
grep -c "ICM workspaces" ~/.kiro/steering/icm.md
# expect: 1
```

## 4. Verify without an agent

The hook prints only inside an ICM workspace: a root `CONTEXT.md` plus a `stages/NN-*`
or `stages/NN_*` directory. Build a throwaway one in `.tmp/`, the repository's
ignored scratch directory, and run the hook by the path step 2 registered.

```sh
mkdir -p ~/projects/frontier-clean/.tmp/icm-demo/stages/01-research
touch ~/projects/frontier-clean/.tmp/icm-demo/CONTEXT.md ~/projects/frontier-clean/.tmp/icm-demo/AGENTS.md
cd ~/projects/frontier-clean/.tmp/icm-demo && "$HOME/projects/frontier-clean/icm/hooks/icm-detect.sh"
# expect: one JSON line containing "ICM workspace detected at" the demo directory, then ". Entry file: AGENTS.md"
cd ~ && "$HOME/projects/frontier-clean/icm/hooks/icm-detect.sh"
# expect: no output
```

Component check, which uses temporary directories only:

```sh
python3 -B ~/projects/frontier-clean/icm/tests/test_hook.py
# expect: last line OK
```

## 5. First use with the agent

Start a new session; skills are read at session start.

```sh
cd ~ && kiro-cli --v3
# paste into the session: build me an ICM workspace for writing a weekly engineering newsletter
# expect: the icm-architect skill runs its questionnaire and creates a directory with CONTEXT.md and stages/
```

Open a second session inside the workspace it created:

```sh
cd <the workspace it created> && kiro-cli --v3
# paste into the session: status
# expect: the icm-run skill renders the pipeline and names the next pending stage
```

## Update

```sh
git -C ~/projects/frontier-clean pull
```

The links pick up skill changes, and the hook runs from the checkout. The hook
file and the steering file are copies: if `config/kiro/hooks.json` or
`instructions/icm.md` changed, repeat step 2 or 3 by hand.

## Disable

To stop detection and keep the skills, delete `~/.kiro/hooks/icm.json` (or its
`SessionStart` group if you merged your own entries in). To hide one skill, remove
its link (`rm ~/.kiro/skills/icm-run`). Start a new session afterwards.

## Remove

```sh
rm ~/.kiro/skills/icm-architect ~/.kiro/skills/icm-run
ls ~/projects/frontier-clean/icm/skills/icm-architect/SKILL.md ~/projects/frontier-clean/icm/skills/icm-run/SKILL.md
# expect: both source paths still listed; rm without -r removes only the links
```

Then, by hand:

- Delete `~/.kiro/hooks/icm.json` and `~/.kiro/steering/icm.md`.
- In `permissions.yaml`, delete the `python3 _tools/*` rule. Leave everything else.

User data: this component keeps no store. Workspaces you built are ordinary
directories and are not touched by removal; they stay readable, but nothing detects
them or runs their stages until you set the component up again.

## If something is off

- The agent says a workspace is not detected: run the hook by hand as in step 4 from
  the workspace root; if it prints there but not in a session, the hook file is not
  trusted or not picked up (a CONFIRM item — check the runtime's hook docs).
- Permission prompts for `_tools/*.py`: check the rule is in `permissions.yaml`; if
  your kiro version wants a different form, edit it there.
- A skill does not appear: start a new session.
- The `icm-architect` skill is vendored at a pinned upstream commit; see
  [VENDOR.md](/icm/skills/icm-architect/VENDOR.md). Re-vendoring needs network and is
  optional.

## Not verified

Nothing here was run against a real `~/.kiro`. The links, the hook-file copy, the
steering copy, the direct hook run, and the removal commands were exercised against
a scratch home directory. Not exercised at all: hook-file registration and trust,
steering pickup, kiro discovering the linked skills, the hook firing at session
start, the permission rule suppressing prompts, and step 5.
