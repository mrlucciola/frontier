# setup

Configures the factory, not the product. Runs once per workspace.

## Procedure

1. Read `setup/questionnaire.md`. If absent, say the workspace has no setup step and stop.
2. Present every question in one message, numbered, each with its default or example. Flat list, no grouping. The user answers everything in one reply (Pattern 8: all at once).
3. Derive fields the questionnaire marks as derived. Do not ask for them.
4. Apply defaults for anything skipped.
5. Replace `{{SCREAMING_SNAKE_CASE}}` placeholders across the workspace. Grep first to list every file that will change; show the list; then replace.
6. Verify: grep for `{{` again. Zero hits, or list what remains and why.
7. Report which files changed. Do not run stage 01.

## Rules

- System-level only. If a question asks for per-run detail (topic, audience for this piece), flag it as a questionnaire defect and still collect it, but note that it belongs in the entry stage's per-run intake.
- Voice questions want examples, not adjectives. If the user answers "professional but warm", ask for two sentences they consider on-voice before proceeding.
- Never re-ask after setup completes. If the user wants to change an answer later, edit the reference file directly; that is a Layer 3 edit, not a setup re-run.
