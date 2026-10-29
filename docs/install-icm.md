# Install: ICM layer

What you get: one instruction section in `~/.claude/CLAUDE.md`, two skills
(`icm-architect` builds workspaces, `icm-run` executes stages), one SessionStart hook
that tells the agent when the cwd is an ICM workspace, and one allow rule so the
workspace's own `_tools/*.py` scripts run without prompts.

Requirements: macOS or Linux, `python3` 3.9 or newer, `bash`, Claude Code installed.
No network is used by the install or at runtime.

## 1. Clone and install

```
git clone <this repo> ~/frontier-clean
python3 ~/frontier-clean/vendor/claude/install.py --only icm --dry-run
python3 ~/frontier-clean/vendor/claude/install.py --only icm
```

The dry run prints every action and changes nothing. The install copies
`skills/icm-architect`, `skills/icm-run` and `hooks/icm-detect.sh` into `~/.claude`,
merges the SessionStart hook and the allow rule into `~/.claude/settings.json`
(a `settings.json.bak-<timestamp>` is written first), and appends the
"## ICM workspaces" section to `~/.claude/CLAUDE.md` (also backed up). Rerunning is
safe: it only replaces what it installed.

Prefer symlinks, so `git pull` updates the live files: add `--link`.

## 2. Check the files

```
ls ~/.claude/skills/icm-architect/SKILL.md ~/.claude/skills/icm-run/SKILL.md ~/.claude/hooks/icm-detect.sh
grep -c "ICM workspaces" ~/.claude/CLAUDE.md
grep -c "icm-detect.sh" ~/.claude/settings.json
python3 ~/frontier-clean/tests/test_hook.py
# expect: three paths listed, 1, 1, OK
```

## 3. First live test

The hook fires only inside an ICM workspace. Build a throwaway one by hand and run the
hook directly, no agent needed:

```
mkdir -p /tmp/icm-demo/stages/01-research && touch /tmp/icm-demo/CONTEXT.md /tmp/icm-demo/CLAUDE.md
cd /tmp/icm-demo && bash ~/.claude/hooks/icm-detect.sh
# expect: one JSON line containing "ICM workspace detected at /tmp/icm-demo. Entry file: CLAUDE.md (already loaded)"
cd ~ && bash ~/.claude/hooks/icm-detect.sh
# expect: no output
```

Then through the agent. Start a new session (skills are read at session start):

```
cd ~ && claude --model claude-opus-5-5 --effort medium
# paste into the session: build me an ICM workspace for writing a weekly engineering newsletter
# expect: the icm-architect skill runs its questionnaire and creates a directory with CONTEXT.md and stages/
```

Open a second session inside the workspace it created:

```
cd <the workspace it created> && claude --model claude-opus-5-5 --effort medium
# paste into the session: status
# expect: the icm-run skill renders the pipeline and names the next pending stage
```

## 4. Update

```
git -C ~/frontier-clean pull
python3 ~/frontier-clean/vendor/claude/install.py --only icm
```

With `--link` installs, the pull alone is enough.

## 5. Uninstall

```
python3 ~/frontier-clean/vendor/claude/install.py --only icm --uninstall
```

Removes the two skills, the hook, the hook registration and the allow rule. Leaves the
"## ICM workspaces" section in `~/.claude/CLAUDE.md`; delete it by hand if you want it
gone.

## If something is off

- The agent says a workspace is not detected: the test is a root `CONTEXT.md` plus a
  `stages/NN-*` or `stages/NN_*` directory. Run the hook by hand as in step 3.
- Permission prompts for `_tools/*.py`: the allow rule is `Bash(python3 _tools/*)`.
  Check it is in `permissions.allow` of `~/.claude/settings.json`; if your Claude Code
  version wants a different form, edit it there.
- The skill does not appear under `/`: start a new session; skills load at start.
- The `icm-architect` skill is vendored at a pinned upstream commit (see
  `general/skills/icm-architect/VENDOR.md`); re-vendoring needs network and is optional.
