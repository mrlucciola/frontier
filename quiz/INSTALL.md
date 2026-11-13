# Setup: adaptive quiz

Manual setup for Claude Code, the only provider this component ships configuration
for. You get the `adaptive-quiz` skill, a fixed multiple-choice bank (24 items across
12 concepts; domains: distributed, rust, typescript) with answer history at
`~/.claude/knowledge/quiz.sqlite3`, and one allow rule so the quiz script runs
without prompts. No hooks, no instruction section, no background process.

The skill is linked from this directory, so the repository must stay in place. Quiz
concept keys equal feynman card slugs, so the optional link to the
[feynman component](/feynman/README.md) is by name only; neither reads the other's
storage, and each works alone.

| Source in this component | Provider destination | How |
| --- | --- | --- |
| `skills/adaptive-quiz/` (`SKILL.md`, `scripts/quiz.py`, `catalog.json`) | `~/.claude/skills/adaptive-quiz` | symlink |
| `config/settings.quiz.fragment.json` | `~/.claude/settings.json` | merged by hand |
| answer history, created by the first `start` | `~/.claude/knowledge/quiz.sqlite3` | user data |

## Prerequisites

- macOS or Linux with `python3` 3.9 or newer.
- Claude Code installed.
- This repository checked out at `~/projects/frontier-clean`. If it lives elsewhere,
  substitute that path in every command.

Setup uses no network.

## 1. Link the skill

Confirm nothing is already at the destination. `ln -s` onto an existing directory
would create the link inside it instead of failing.

```sh
ls -d ~/.claude/skills/adaptive-quiz
# expect: "No such file or directory"; inspect anything that is listed before going on
```

```sh
mkdir -p ~/.claude/skills
ln -s ~/projects/frontier-clean/quiz/skills/adaptive-quiz ~/.claude/skills/adaptive-quiz
ls ~/.claude/skills/adaptive-quiz/SKILL.md ~/.claude/skills/adaptive-quiz/scripts/quiz.py
# expect: two paths listed
```

The allow rule and the skill both name
`~/.claude/skills/adaptive-quiz/scripts/quiz.py`; this link is what makes that path
exist.

## 2. Add the allow rule

The rule lives in the [settings fragment](/quiz/config/settings.quiz.fragment.json).

If `~/.claude/settings.json` does not exist yet, the fragment is a complete settings
file:

```sh
cp ~/projects/frontier-clean/quiz/config/settings.quiz.fragment.json ~/.claude/settings.json
```

Otherwise keep a copy and edit the file by hand, leaving every other key and entry
as it is:

```sh
cp ~/.claude/settings.json ~/.claude/settings.json.bak-quiz
```

Add `"Bash(python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py:*)"` to the
`permissions.allow` array, creating it if absent.

```sh
python3 -m json.tool ~/.claude/settings.json /dev/null
grep -c "adaptive-quiz/scripts/quiz.py" ~/.claude/settings.json
# expect: no output from the first command (the file parses), then 1
```

## 3. Verify without an agent

```sh
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py doctor
# expect: JSON with "database_exists": false, "concepts": 12 and "questions": 24
python3 -B ~/projects/frontier-clean/quiz/tests/test_quiz.py
# expect: OK
```

A missing database is normal before the first quiz; the first `start` creates it. The
component check uses temporary directories and never touches `~/.claude/knowledge/`.

Then take two questions against your real store:

```sh
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --count 2 --domain rust
# expect: JSON with a "session" id and two questions, no "answer" fields
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py answer <SESSION_ID> <QUESTION_ID> A
# expect: JSON with "correct", the right label under "answer", and the explanation
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py profile
# expect: per-concept observed accuracy; one concept now has "distinct_items": 1
```

## 4. First use with the agent

Start a new session; skills are read at session start.

```sh
cd ~ && claude
# paste into the session: /adaptive-quiz five questions on rust
# expect: one question at a time with options A-D, graded by the CLI after each answer,
#         and a final correct/answered count with assisted answers reported separately
```

If the feynman component is set up, miss a question on purpose: the skill should
offer to record the missed idea as an open gap on the matching concept card.

## Everyday commands

```sh
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --count 5
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --concepts idempotency,backpressure
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --scope here   # per-repo history
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py profile
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py export > quiz-export.json   # keep private
```

## Update

```sh
git -C ~/projects/frontier-clean pull
```

The link picks up skill, script, and bank changes. Answer history is never touched.
The allow rule is a copy: if the fragment changed, repeat step 2 by hand.

## Disable

Remove the link (`rm ~/.claude/skills/adaptive-quiz`) and start a new session; the
allow rule then names a path that no longer exists. Recreate the link to turn the
skill back on. Deleting only the allow rule keeps the skill and brings the permission
prompts back.

## Remove

```sh
rm ~/.claude/skills/adaptive-quiz
ls ~/projects/frontier-clean/quiz/skills/adaptive-quiz/SKILL.md ~/.claude/knowledge
# expect: the source file and quiz.sqlite3 both still listed; rm without -r removes only the link
```

Then, by hand, delete `"Bash(python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py:*)"`
from `permissions.allow` in `~/.claude/settings.json`. Leave everything else, then
rerun the `json.tool` check from step 2.

User data: removal keeps `~/.claude/knowledge/quiz.sqlite3` (every session and
answer). It is read again if you repeat the setup. Run `export` before removing the
link if you want a readable copy. Deleting the database is a separate, deliberate
step and cannot be undone from this repository.

## If something is off

- Permission prompts: the agent must type the command exactly as
  `python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py ...`; check the rule from
  the fragment is in `permissions.allow`.
- "unknown concepts" from `start`: the bank is fixed; `doctor` lists sizes and
  `profile` lists the 12 concept keys. Asking for a topic outside the bank is expected
  to fail.
- The model answers its own questions: the skill forbids opening `catalog.json` or
  grading by itself; if it happens, quote the workflow rule and restart the quiz.
- The quiz and feynman disagree about a concept name: keys equal card slugs by
  convention; `profile` prints the expected card slug as `feynman_card`.

## Not verified

Nothing here was run against a real `~/.claude`. The link, the copy of the fragment
into an absent `settings.json`, `doctor`, `start`, `answer`, `profile`, and the
removal command were exercised against a scratch home directory. Not exercised at
all: the hand edit of an existing `settings.json`, Claude Code discovering the linked
skill, the allow rule suppressing prompts, and step 4.
