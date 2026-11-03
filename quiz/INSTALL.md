# Install: adaptive quiz

What you get: the `adaptive-quiz` skill, a fixed multiple-choice bank (24 items across
12 concepts; domains: distributed, rust, typescript) with deterministic answer history
at `~/.claude/knowledge/quiz.sqlite3`, and one allow rule so the quiz script runs
without prompts. No hooks, no instruction section, no background process, no network.

Everything this component needs lives in this directory: `skills/`, `config/`,
`tests/`, `install.py`. Quiz concept keys equal feynman card slugs, so the optional
link to the feynman component is by name only; neither reads the other's storage, and
each works alone.

Requirements: macOS or Linux, `python3` 3.9 or newer, Claude Code installed.

## 1. Clone and install

```
git clone <this repo> ~/frontier-clean
python3 ~/frontier-clean/quiz/install.py --dry-run
python3 ~/frontier-clean/quiz/install.py
```

The dry run prints every action and changes nothing. The install copies
`skills/adaptive-quiz` into `~/.claude/skills/` and merges one allow rule into
`~/.claude/settings.json` (a `settings.json.bak-<timestamp>` is written first).
Rerunning is safe: it only replaces what it installed and never touches your answer
history. Prefer symlinks, so `git pull` updates the live files: add `--link`.

## 2. Check the files and run the tests

```
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py doctor
grep -c "adaptive-quiz/scripts/quiz.py" ~/.claude/settings.json
python3 ~/frontier-clean/quiz/tests/test_quiz.py
python3 ~/frontier-clean/quiz/tests/test_install.py
# expect: JSON with "database_exists": false and "questions": 24, then 1, OK, OK
```

A missing database is normal before the first quiz; it is created on the first start.
The tests use temporary directories and never touch `~/.claude/knowledge/`.

## 3. First live test, no agent

```
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --count 2 --domain rust
# expect: JSON with a session id and two questions, no "answer" fields
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py answer <SESSION_ID> <QUESTION_ID> A
# expect: JSON with "correct", the right label, and the explanation
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py profile
# expect: per-concept observed accuracy; one concept now has distinct_items 1
```

## 4. First live test, with the agent

Start a new session (skills load at session start):

```
cd ~ && claude
# paste into the session: /adaptive-quiz five questions on rust
# expect: one question at a time with options A-D, graded by the CLI after each answer,
#         and a final correct/answered count with assisted answers reported separately
```

If the feynman component is installed, miss a question on purpose: the skill should
offer to record the missed idea as an open gap on the matching concept card.

## 5. Everyday commands

```
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --count 5
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --concepts idempotency,backpressure
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py start --scope here   # per-repo history
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py profile
python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py export > quiz-export.json   # keep private
```

## 6. Update

```
git -C ~/frontier-clean pull
python3 ~/frontier-clean/quiz/install.py
```

With `--link` installs, the pull alone is enough. Answer history is never touched.

## 7. Uninstall

```
python3 ~/frontier-clean/quiz/install.py --uninstall
```

Removes the skill and the allow rule. Keeps `~/.claude/knowledge/` (your answer
history); delete it by hand as a separate, deliberate step.

## If something is off

- Permission prompts: the agent must type the command exactly as
  `python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py ...`; check the rule from
  `quiz/config/settings.quiz.fragment.json` is in `permissions.allow`.
- "unknown concepts" from start: the bank is fixed; `doctor` lists sizes and `profile`
  lists the 12 concept keys. Asking for a topic outside the bank is expected to fail.
- The model answers its own questions: the skill forbids opening `catalog.json` or
  grading by itself; if it happens, quote the workflow rule and restart the quiz.
- The quiz and feynman disagree about a concept name: keys equal card slugs by
  convention; `profile` prints the expected card slug as `feynman_card`.
