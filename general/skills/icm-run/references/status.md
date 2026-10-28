# status

State is the filesystem. Derive it; never maintain a status file.

## Scan

1. List `stages/` entries matching `NN-name` or `NN_name`, sorted by number.
2. For each, list `output/` excluding `.gitkeep`.
3. COMPLETE if any file remains, else PENDING.
4. Current stage = first PENDING. If none, pipeline COMPLETE.

Use a shell `ls` or `find` for this; do not open the output files.

## Render

```
Pipeline Status: [workspace-name]

  [01-research]  ------>  [02-script]  ------>  [03-production]
     COMPLETE                PENDING               PENDING
  (topic-research.md)       (empty)               (empty)

Next: 02-script
```

Workspace name comes from the entry file's title or the folder name.

## Extras, only if present

- `setup/questionnaire.md` with unresolved `{{PLACEHOLDER}}` tokens anywhere in the workspace: say "setup incomplete" above the diagram. Check with a grep, do not read files.
- Non-pipeline forms (record library, knowledge bundle): status is the count of records or nodes and the most recently modified one. Say so instead of drawing a pipeline.
