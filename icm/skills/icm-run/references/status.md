# status

State is the filesystem. Derive it; never maintain a status file.

## Scan

Run `python3 <skill dir>/scripts/state.py <workspace root>`. It reads only names, sizes, hashes and each `check.md`, never asking you to open the outputs. It lists stages in number order with their state:

| State | Means | Next action |
|---|---|---|
| unproduced | required output absent, empty or partial | run the stage once its inputs exist |
| pending | output exists; no verdict for the current files | the stage's check; no later stage |
| rejected | the check failed | revise within the stage, then check again |
| accepted | a verdict bound to the current outputs, inputs and contract passed | a later stage, on request |
| stale | an output, input or contract changed after the verdict | re-run or re-check before anything uses it |
| blocked | no contract, a missing input, or a path that escapes the stage | report the blocker |

Its last line is the one next action. A status request writes nothing.

## Render

```
Pipeline Status: [workspace-name]

  [01-research]  ------>  [02-script]  ------>  [03-production]
     ACCEPTED                PENDING               UNPRODUCED
  (topic-research.md)   (hello-script.md)          (empty)

Next: review 02-script (human check)
```

Workspace name comes from the entry file's title or the folder name.

## Extras, only if present

- `setup/questionnaire.md` with unresolved `{{PLACEHOLDER}}` tokens anywhere in the workspace: say "setup incomplete" above the diagram. Check with a grep, do not read files.
- Non-pipeline forms (record library, knowledge bundle) have no numbered stages, so state.py reports no workspace. Report the count of records or nodes and the most recently modified one, and say that this is not a pipeline status.
