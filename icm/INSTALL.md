# Setup: ICM

Manual setup for Claude Code, the only provider this component ships configuration
for. You get two skills (`icm-architect` builds workspaces, `icm-run` executes
stages), a SessionStart hook that tells the agent when the working directory is an
ICM workspace, one allow rule so a workspace's own `_tools/*.py` scripts run without
prompts, and one instruction section in `~/.claude/CLAUDE.md`.

The skills are linked from this directory and the hook runs from it, so the
repository must stay in place.

| Source in this component | Provider destination | How |
| --- | --- | --- |
| `skills/icm-architect/` | `~/.claude/skills/icm-architect` | symlink |
| `skills/icm-run/` | `~/.claude/skills/icm-run` | symlink |
| `hooks/icm-detect.sh` | none | run from this component by the registered command |
| `config/settings.icm.fragment.json` | `~/.claude/settings.json` | merged by hand |
| `instructions/icm.md` | `~/.claude/CLAUDE.md` | appended once |

## Prerequisites

- macOS or Linux with `bash` and `python3` 3.9 or newer.
- Claude Code installed.
- This repository checked out at `~/projects/frontier-clean`. If it lives elsewhere,
  substitute that path in every command and in the hook command of step 2.

Setup uses no network.

## 1. Link the skills

Confirm nothing is already at the destinations. `ln -s` onto an existing directory
would create the link inside it instead of failing.

```sh
ls -d ~/.claude/skills/icm-architect ~/.claude/skills/icm-run
# expect: "No such file or directory" twice; inspect anything that is listed before going on
```

```sh
mkdir -p ~/.claude/skills
ln -s ~/projects/frontier-clean/icm/skills/icm-architect ~/.claude/skills/icm-architect
ln -s ~/projects/frontier-clean/icm/skills/icm-run ~/.claude/skills/icm-run
ls ~/.claude/skills/icm-architect/SKILL.md ~/.claude/skills/icm-run/SKILL.md
# expect: two paths listed
```

## 2. Register the hook and the allow rule

The entries live in the [settings fragment](/icm/config/settings.icm.fragment.json).
The registered command is the hook's path in this component; nothing is linked into
`~/.claude/hooks`.

If `~/.claude/settings.json` does not exist yet, the fragment is a complete settings
file:

```sh
cp ~/projects/frontier-clean/icm/config/settings.icm.fragment.json ~/.claude/settings.json
```

Otherwise keep a copy and edit the file by hand, leaving every other key and entry
as it is:

```sh
cp ~/.claude/settings.json ~/.claude/settings.json.bak-icm
```

- Add this group to the `hooks.SessionStart` array, creating `hooks` and
  `SessionStart` if they are absent:

  ```json
  {
    "hooks": [
      {
        "type": "command",
        "command": "\"$HOME/projects/frontier-clean/icm/hooks/icm-detect.sh\"",
        "timeout": 5
      }
    ]
  }
  ```

- Add `"Bash(python3 _tools/*)"` to the `permissions.allow` array, creating it if
  absent.

```sh
python3 -m json.tool ~/.claude/settings.json /dev/null
grep -c "icm-detect.sh" ~/.claude/settings.json
# expect: no output from the first command (the file parses), then 1
```

## 3. Add the instruction section

[instructions/icm.md](/icm/instructions/icm.md) is the "## ICM workspaces" section. Append
it once.

```sh
grep -c "ICM workspaces" ~/.claude/CLAUDE.md
# expect: 0 or "No such file or directory"; if it prints 1 the section is already there, skip this step
printf '\n\n' >> ~/.claude/CLAUDE.md
cat ~/projects/frontier-clean/icm/instructions/icm.md >> ~/.claude/CLAUDE.md
grep -c "ICM workspaces" ~/.claude/CLAUDE.md
# expect: 1
```

## 4. Verify without an agent

The hook prints only inside an ICM workspace: a root `CONTEXT.md` plus a `stages/NN-*`
or `stages/NN_*` directory. Build a throwaway one in `.tmp/`, the repository's
ignored scratch directory, and run the hook by the path step 2 registered.

```sh
mkdir -p ~/projects/frontier-clean/.tmp/icm-demo/stages/01-research
touch ~/projects/frontier-clean/.tmp/icm-demo/CONTEXT.md ~/projects/frontier-clean/.tmp/icm-demo/CLAUDE.md
cd ~/projects/frontier-clean/.tmp/icm-demo && "$HOME/projects/frontier-clean/icm/hooks/icm-detect.sh"
# expect: one JSON line containing "ICM workspace detected at" the demo directory, then ". Entry file: CLAUDE.md (already loaded)"
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
cd ~ && claude
# paste into the session: build me an ICM workspace for writing a weekly engineering newsletter
# expect: the icm-architect skill runs its questionnaire and creates a directory with CONTEXT.md and stages/
```

Open a second session inside the workspace it created:

```sh
cd <the workspace it created> && claude
# paste into the session: status
# expect: the icm-run skill renders the pipeline and names the next pending stage
```

## Update

```sh
git -C ~/projects/frontier-clean pull
```

The links pick up skill changes, and the hook runs from the checkout. The settings
entries and the instruction
section are copies: if the fragment or `instructions/icm.md` changed, repeat step 2
or 3 by hand.

## Disable

To stop detection and keep the skills, delete the `icm-detect.sh` group from
`hooks.SessionStart` in `~/.claude/settings.json`. To hide one skill, remove its link
(`rm ~/.claude/skills/icm-run`). Start a new session afterwards.

## Remove

```sh
rm ~/.claude/skills/icm-architect ~/.claude/skills/icm-run
ls ~/projects/frontier-clean/icm/skills/icm-architect/SKILL.md ~/projects/frontier-clean/icm/skills/icm-run/SKILL.md
# expect: both source paths still listed; rm without -r removes only the links
```

Then, by hand:

- In `~/.claude/settings.json`, delete the `icm-detect.sh` group from
  `hooks.SessionStart` and `"Bash(python3 _tools/*)"` from `permissions.allow`. Leave
  everything else, then rerun the `json.tool` check from step 2.
- In `~/.claude/CLAUDE.md`, delete the "## ICM workspaces" heading and the paragraph
  and bullets under it.

User data: this component keeps no store. Workspaces you built are ordinary
directories and are not touched by removal; they stay readable, but nothing detects
them or runs their stages until you set the component up again.

## If something is off

- The agent says a workspace is not detected: run the hook by hand as in step 4 from
  the workspace root.
- Permission prompts for `_tools/*.py`: check that `Bash(python3 _tools/*)` is in
  `permissions.allow` of `~/.claude/settings.json`; if your Claude Code version wants
  a different form, edit it there.
- A skill does not appear under `/`: start a new session.
- The `icm-architect` skill is vendored at a pinned upstream commit; see
  [VENDOR.md](/icm/skills/icm-architect/VENDOR.md). Re-vendoring needs network and is
  optional.

## Not verified

Nothing here was run against a real `~/.claude`. The links, the copy of the fragment
into an absent `settings.json`, the append, the direct hook run, and the removal
commands were exercised against a scratch home directory. Not exercised at all: the
hand merge into an existing `settings.json`, Claude Code discovering the linked
skills, the hook firing at session start, the allow rule suppressing prompts, and
step 5.
