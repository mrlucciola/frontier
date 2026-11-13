# Install: Feynman skill and concept graph

> Historical setup reference. The `install.py` commands below describe a removed
> installer. Use [component maintenance instructions](AGENTS.md) for current source
> checks and treat this guide as input when documenting replacement setup.

What you get: the `feynman` skill (answers "how or why does X work" questions the
Feynman way and persists a card), the `cg` tool that owns the concept graph at
`~/.claude/concepts/`, a UserPromptSubmit hook that recalls matching cards in any
directory, a three-line instruction section, and two allow rules so `cg` runs without
prompts. Design: `docs/design.md`.

Everything this component needs lives in this directory: `skills/`, `tools/`
(the engine `cg.py` and the hook `recall.sh`, side by side), `config/`,
`instructions/`, `tests/`, `install.py`.

Requirements: macOS or Linux, `python3` 3.9 or newer, `bash`, `git`, Claude Code
installed. No network is used by the install or at runtime. `cg grade` is the one
command that calls a model, and only when you run it.

## 1. Clone and install

```
git clone <this repo> ~/frontier-clean
python3 ~/frontier-clean/feynman/install.py --dry-run
python3 ~/frontier-clean/feynman/install.py
```

The dry run prints every action and changes nothing. The install copies
`skills/feynman` and `tools/concept-graph` into `~/.claude`, merges the hook and the
allow rules into `~/.claude/settings.json` (a `settings.json.bak-<timestamp>` is
written first), appends the "## Recalled concepts" section to `~/.claude/CLAUDE.md`
(also backed up), and creates `~/.claude/concepts/`. Rerunning is safe: it only
replaces what it installed and never touches your cards.

Prefer symlinks, so `git pull` updates the live files: add `--link`.

## 2. Check the files and run the tests

```
python3 ~/.claude/tools/concept-graph/cg.py status
grep -c "Recalled concepts" ~/.claude/CLAUDE.md
grep -c "concept-graph/recall.sh" ~/.claude/settings.json
python3 ~/frontier-clean/feynman/tools/concept-graph/tests/test_cg.py
python3 ~/frontier-clean/feynman/tests/test_recall_hook.py
python3 ~/frontier-clean/feynman/tests/test_install.py
# expect: "cards: 0", 1, 1, OK, OK, OK
```

The tests use temporary directories and never touch `~/.claude/concepts/`.

## 3. First live test, no agent

Create one card by hand and watch the hook recall it:

```
python3 ~/.claude/tools/concept-graph/cg.py add wal-mode --title "SQLite WAL mode" --alias wal \
  --explain "Writes go to a side file first; readers keep reading the main file until a checkpoint folds the side file in." \
  --analogy "A restaurant order pad: orders pile up on the pad while the kitchen keeps cooking from the last menu." \
  --breaks "The pad is replayed strictly in order; real kitchens reorder tickets." \
  --pitch "WAL lets many readers and one writer work at the same time." --confidence 3
python3 ~/.claude/tools/concept-graph/cg.py recall how does wal work
# expect: a block starting "memory: 1 concept (scope: global)" and ending with the guard line
printf '{"session_id":"demo","cwd":"%s","prompt":"why does WAL let readers continue?"}' "$PWD" | bash ~/.claude/tools/concept-graph/recall.sh
# expect: one JSON line with hookSpecificOutput.additionalContext holding the same block
printf '{"session_id":"demo","cwd":"%s","prompt":"why does WAL let readers continue?"}' "$PWD" | bash ~/.claude/tools/concept-graph/recall.sh
# expect: no output (the same session already saw this card)
printf '{"session_id":"demo","cwd":"%s","prompt":"tell me a joke"}' "$PWD" | bash ~/.claude/tools/concept-graph/recall.sh
# expect: no output
```

Remove the demo card when done (or keep it):

```
rm ~/.claude/concepts/cards/wal-mode.md && python3 ~/.claude/tools/concept-graph/cg.py index
```

## 4. First live test, with the agent

Start a new session (skills load at session start; the hook and permissions are live
immediately):

```
cd ~ && claude
# paste into the session: /feynman git worktrees
# expect: the four-step protocol, then a "Card" section listing the cg commands it ran
python3 ~/.claude/tools/concept-graph/cg.py list
# expect (in another terminal): a git-worktrees card, status learning or understood
```

Now a second session, from any other directory, with an ordinary question:

```
cd /tmp && claude
# paste into the session: how do git worktrees differ from branches?
# expect: a "memory: 1 concept" block ahead of your prompt (visible in the transcript),
#         and the skill's lite form that refines the existing card instead of starting over
```

Ask the same thing once more in that second session: no second memory block.

## 5. Everyday commands

```
python3 ~/.claude/tools/concept-graph/cg.py list                   # all cards
python3 ~/.claude/tools/concept-graph/cg.py gaps --due             # gaps to revisit
python3 ~/.claude/tools/concept-graph/cg.py check                  # mark cards whose code anchors moved
python3 ~/.claude/tools/concept-graph/cg.py neighbors <slug> --depth 2
python3 ~/.claude/tools/concept-graph/cg.py export --format mermaid
python3 ~/.claude/tools/concept-graph/cg.py grade <slug>           # blind grade by a model, costs one call
```

Optional shortcut: put a `cg` wrapper on your PATH; the allow rule `Bash(cg:*)` already
covers it.

```
printf '#!/bin/sh\nexec python3 "$HOME/.claude/tools/concept-graph/cg.py" "$@"\n' > ~/.local/bin/cg && chmod +x ~/.local/bin/cg
```

## 6. Update

```
git -C ~/frontier-clean pull
python3 ~/frontier-clean/feynman/install.py
```

With `--link` installs, the pull alone is enough. Cards are never touched by an update.

## 7. Uninstall

```
python3 ~/frontier-clean/feynman/install.py --uninstall
```

Removes the skill, the tool (hook included), its registration and the allow rules.
Keeps `~/.claude/concepts/` (your cards) and the "## Recalled concepts" section in
`~/.claude/CLAUDE.md`; delete those by hand if you want them gone.

## If something is off

- `cg` asks for permission every time: the agent must type the command exactly as
  `python3 ~/.claude/tools/concept-graph/cg.py ...`; the skill says so. Check that
  `permissions.allow` in `~/.claude/settings.json` holds the two rules from
  `feynman/config/settings.feynman.fragment.json`.
- No memory block appears: run step 3's `printf | bash recall.sh` line from the same
  directory. Silence there means no card matched (titles, aliases and slugs match as
  whole words; check with `cg recall <words>`). Output there but none in the agent means
  the hook registration is missing from `settings.json`.
- The block appears on every prompt for the same card: the per-session state lives in
  `~/.claude/concepts/.state/`; the hook needs a `session_id` in its payload, which
  Claude Code provides.
- A card looks wrong: edit it through `cg write` and `cg set`, not by hand, so the index
  and lexicon stay in step. If you did edit by hand, run `cg index`.
- The skill never fires on ordinary questions: it is meant to fire on "how/why does X
  work" and "explain X" shapes, not on tasks or one-line lookups. `/feynman <topic>`
  always works.
