# Contract extensions

Upstream requires Inputs, Process, Outputs (Pattern 1) and recognizes Checkpoints (11) and Audit (12). Three further sections appear in the paper's future work or in the LvlyBot adaptation and are cheap to support. A workspace may include any of them; icm-run honors them when present and ignores their absence.

## Verify (paper §6.2)

Cross-stage trace check. Runs after Process, before Audit.

```
## Verify

| Against | Criteria |
|---|---|
| ../02-script/output/[slug]-script.md | Every scene references a phrase that exists verbatim in the script; timing sums to script duration |
```

Behavior: open the named earlier output, check each criterion, list discrepancies. Discrepancies are reported, not silently fixed, because the right fix may be upstream.

## Completion (gist)

Says what happens after output is written. In a human-gated pipeline the only valid values are "stop for review" (default when absent) or "final stage: deliverable is X". If a contract says "proceed directly to stage N+1", treat that as advisory and still stop unless the user said to chain, because the global instruction's gate rule is the floor. Note the conflict in the report.

```
## Completion

Final stage. Deliverable: output/[slug]-deck.pptx. Nothing follows.
```

## What NOT to Load (gist)

An explicit exclusion table, usually in the entry file or root CONTEXT.md. It gives the agent permission to not look.

```
## What NOT to Load

| Resource | Why |
|---|---|
| Application source code | Only the stage that edits it loads the files it identifies |
| Other workspaces | Irrelevant |
| README.md | Human-facing; routing is in CONTEXT.md |
```

Behavior: these are hard exclusions for the whole run. If an Inputs row contradicts an exclusion, the Inputs row wins for that stage only, and the conflict is reported.

## Sections icm-run does not add

Do not inject Verify, Completion, or exclusion tables into a workspace's contracts during a run. Suggest them in the end-of-stage report if their absence caused a problem. Adding them is an icm-architect (restructure mode) decision the human approves.
