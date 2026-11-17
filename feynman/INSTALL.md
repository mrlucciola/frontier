# Setup: Feynman skill and concept graph

Manual setup for Kiro CLI v3, the only provider this component ships configuration
for. You get the `feynman` skill (answers "how or why does X work" questions and
persists a card), the `cg` tool that owns the concept graph at `~/.kiro/concepts/`,
a UserPromptSubmit hook that recalls matching cards in any directory, permission
rules so `cg` runs without prompts, and one steering instruction file.
Design: [docs/design.md](/feynman/docs/design.md).

The skill and tool are linked from this directory, so the repository must stay in
place. Hook registration and trust mechanics on kiro v3 are CONFIRM items (see
[the branch policy](/docs/kiro-branch.md)); verify the hook fires with step 5.

| Source in this component | Kiro destination | How |
| --- | --- | --- |
| `skills/feynman/` | `~/.kiro/skills/feynman` | symlink |
| `tools/concept-graph/` (`cg.py`, `recall.sh`) | `~/.kiro/tools/concept-graph` | symlink |
| `config/kiro/hooks.json` | `~/.kiro/hooks/feynman.json` | copied, or merged by hand |
| `instructions/feynman.md` | `~/.kiro/steering/feynman.md` | copied once |
| card store, created by `cg init` | `~/.kiro/concepts/` | user data |

## Prerequisites

- macOS or Linux with `bash`, `git`, and `python3` 3.9 or newer.
- Kiro CLI installed; agents run through `kiro-cli --v3`.
- This repository checked out at `~/projects/frontier-clean`. If it lives elsewhere,
  substitute that path in every command and in the hook command of step 3.

Setup uses no network. `cg grade --grader <argv>` is the one command that calls a
model, and only when you run it (the headless model-call contract on kiro v3 is
CONFIRM, so `cg` ships no default grader).

## 1. Link the skill and the tool

Confirm nothing is already at the destinations. `ln -s` onto an existing directory
would create the link inside it instead of failing.

```sh
ls -d ~/.kiro/skills/feynman ~/.kiro/tools/concept-graph
# expect: "No such file or directory" twice; inspect anything that is listed before going on
```

```sh
mkdir -p ~/.kiro/skills ~/.kiro/tools
ln -s ~/projects/frontier-clean/feynman/skills/feynman ~/.kiro/skills/feynman
ln -s ~/projects/frontier-clean/feynman/tools/concept-graph ~/.kiro/tools/concept-graph
ls ~/.kiro/skills/feynman/SKILL.md ~/.kiro/tools/concept-graph/cg.py ~/.kiro/tools/concept-graph/recall.sh
# expect: three paths listed
```

The tool directory is linked because the hook file, the skill, and `cg`'s own
recall output all name `~/.kiro/tools/concept-graph/`, not the path inside this
component. `recall.sh` finds `cg.py` beside itself, so the two stay together.

## 2. Create the store

```sh
python3 ~/.kiro/tools/concept-graph/cg.py init
# expect: "ok" followed by the absolute path of ~/.kiro/concepts
python3 ~/.kiro/tools/concept-graph/cg.py status
# expect: four lines, the second starting "cards: 0"
```

`init` is safe to rerun and never touches existing cards.

## 3. Register the hook and the permission rules

The hook is a standalone command-hook file,
[config/kiro/hooks.json](/feynman/config/kiro/hooks.json).

```sh
mkdir -p ~/.kiro/hooks
cp ~/projects/frontier-clean/feynman/config/kiro/hooks.json ~/.kiro/hooks/feynman.json
python3 -m json.tool ~/.kiro/hooks/feynman.json /dev/null
# expect: no output (the file parses)
```

If `~/.kiro/hooks/feynman.json` already exists and holds your own entries, merge
the `UserPromptSubmit` group into it by hand instead of overwriting.

Permissions: add rules allowing `python3 ~/.kiro/tools/concept-graph/cg.py ...`
and, if you make the shortcut below, `cg ...` to run unprompted to
`permissions.yaml`. Review them by hand; a deploy step never writes that file.
The `permissions.yaml` schema is a CONFIRM item, so write the rules in whatever
form the runtime's current docs show.

## 4. Add the steering instruction

[instructions/feynman.md](/feynman/instructions/feynman.md) is the "## Recalled
concepts" section. Copy it once as a steering file.

```sh
mkdir -p ~/.kiro/steering
cp ~/projects/frontier-clean/feynman/instructions/feynman.md ~/.kiro/steering/feynman.md
grep -c "Recalled concepts" ~/.kiro/steering/feynman.md
# expect: 1
```

## 5. Verify without an agent

Component checks, which use temporary stores and never touch `~/.kiro/concepts/`:

```sh
python3 -B ~/projects/frontier-clean/feynman/tools/concept-graph/tests/test_cg.py
python3 -B ~/projects/frontier-clean/feynman/tests/test_recall_hook.py
# expect: OK, OK
```

Then create one card in your real store and watch the hook recall it:

```sh
python3 ~/.kiro/tools/concept-graph/cg.py add wal-mode --title "SQLite WAL mode" --alias wal \
  --explain "Writes go to a side file first; readers keep reading the main file until a checkpoint folds the side file in." \
  --analogy "A restaurant order pad: orders pile up on the pad while the kitchen keeps cooking from the last menu." \
  --breaks "The pad is replayed strictly in order; real kitchens reorder tickets." \
  --pitch "WAL lets many readers and one writer work at the same time." --confidence 3
# expect: added wal-mode
python3 ~/.kiro/tools/concept-graph/cg.py recall how does wal work
# expect: a block starting "memory: 1 concept (scope: global)" and ending with the guard line
printf '{"session_id":"demo","cwd":"%s","prompt":"why does WAL let readers continue?"}' "$PWD" | bash ~/.kiro/tools/concept-graph/recall.sh
# expect: one JSON line with hookSpecificOutput.additionalContext holding the same block
printf '{"session_id":"demo","cwd":"%s","prompt":"why does WAL let readers continue?"}' "$PWD" | bash ~/.kiro/tools/concept-graph/recall.sh
# expect: no output (the same session already saw this card)
printf '{"session_id":"demo","cwd":"%s","prompt":"tell me a joke"}' "$PWD" | bash ~/.kiro/tools/concept-graph/recall.sh
# expect: no output
```

Remove the demo card when done, or keep it:

```sh
rm ~/.kiro/concepts/cards/wal-mode.md
python3 ~/.kiro/tools/concept-graph/cg.py index
# expect: indexed 0 cards (or the number of cards you have left)
```

## 6. First use with the agent

Start a new session; skills are read at session start.

```sh
cd ~ && kiro-cli --v3
# paste into the session: /feynman git worktrees
# expect: the four-step protocol, then a "Card" section listing the cg commands it ran
python3 ~/.kiro/tools/concept-graph/cg.py list
# expect (in another terminal): a git-worktrees card, status learning or understood
```

Now a second session, from any other directory, with an ordinary question:

```sh
cd /tmp && kiro-cli --v3
# paste into the session: how do git worktrees differ from branches?
# expect: a "memory: 1 concept" block ahead of your prompt (visible in the transcript),
#         and the skill's lite form that refines the existing card instead of starting over
```

Ask the same thing once more in that second session: no second memory block.

## Everyday commands

```sh
python3 ~/.kiro/tools/concept-graph/cg.py list                   # all cards
python3 ~/.kiro/tools/concept-graph/cg.py gaps --due             # gaps to revisit
python3 ~/.kiro/tools/concept-graph/cg.py check                  # mark cards whose code anchors moved
python3 ~/.kiro/tools/concept-graph/cg.py neighbors <slug> --depth 2
python3 ~/.kiro/tools/concept-graph/cg.py export --format mermaid
python3 ~/.kiro/tools/concept-graph/cg.py grade <slug> --grader <argv>   # blind grade by a model, costs one call
```

Optional shortcut, if `~/.local/bin` is on your `PATH`. The `cg` permission rule
above covers it.

```sh
mkdir -p ~/.local/bin
ln -s ~/projects/frontier-clean/feynman/tools/concept-graph/cg.py ~/.local/bin/cg
cg status
# expect: the same four lines as step 2
```

## Update

```sh
git -C ~/projects/frontier-clean pull
```

The links pick up skill, tool, and hook changes. Cards are never touched. The
hook file and the steering file are copies: if `config/kiro/hooks.json` or
`instructions/feynman.md` changed, repeat step 3 or 4 by hand.

## Disable

To stop recall and keep the skill and your cards, delete `~/.kiro/hooks/feynman.json`
(or its `UserPromptSubmit` group if you merged your own entries in); the skill's
own recall step keeps working. To hide the skill, remove its link
(`rm ~/.kiro/skills/feynman`). Start a new session afterwards.

## Remove

```sh
rm ~/.kiro/skills/feynman ~/.kiro/tools/concept-graph
ls ~/projects/frontier-clean/feynman/tools/concept-graph/cg.py ~/.kiro/concepts
# expect: the source file and your store both still listed; rm without -r removes only the links
```

If you made the shortcut, `rm ~/.local/bin/cg` as well. Then, by hand:

- Delete `~/.kiro/hooks/feynman.json` and `~/.kiro/steering/feynman.md`.
- In `permissions.yaml`, delete the two `cg` rules. Leave everything else.

User data: removal keeps `~/.kiro/concepts/` (cards, index, lexicon, write log, and
per-session recall state). The cards stay readable as markdown and are picked up
again if you repeat the setup. Deleting that directory is a separate, deliberate
step and cannot be undone from this repository.

## If something is off

- `cg` asks for permission every time: the agent must type the command exactly as
  `python3 ~/.kiro/tools/concept-graph/cg.py ...`; the skill says so. Check the
  two rules are in `permissions.yaml`.
- No memory block appears: run step 5's `printf | bash recall.sh` line from the same
  directory. Silence there means no card matched (titles, aliases and slugs match as
  whole words; check with `cg recall <words>`). Output there but none in the agent
  means the hook file is missing from `~/.kiro/hooks/` or not trusted (a CONFIRM
  item — check the runtime's hook docs).
- The block appears on every prompt for the same card: the per-session state lives in
  `~/.kiro/concepts/.state/`; the hook needs a `session_id` in its payload, which
  the runtime provides (a kiro-exported session variable is a CONFIRM recon item).
- A card looks wrong: edit it through `cg write` and `cg set`, not by hand, so the
  index and lexicon stay in step. If you did edit by hand, run `cg index`.
- The skill never fires on ordinary questions: it is meant to fire on "how/why does X
  work" and "explain X" shapes, not on tasks or one-line lookups. `/feynman <topic>`
  always works.

## Not verified

Nothing here was run against a real `~/.kiro`. The links, `cg init`, the hook-file
copy, the steering copy, the demo card and hook runs in step 5, the `cg` shortcut,
and the removal commands were exercised against a scratch home directory. Not
exercised at all: hook-file registration and trust, steering pickup, kiro
discovering the linked skill, the hook firing on a prompt and its stdout envelope,
the permission rules suppressing prompts, and step 6.
