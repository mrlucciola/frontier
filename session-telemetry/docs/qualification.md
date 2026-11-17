# Qualification

Read this when evaluating measurement evidence or planning a baseline. The
[usage guide](/session-telemetry/README.md) covers invocation and the [observation contract](/session-telemetry/docs/observations.md)
defines output semantics.

Session-cost readers, ledger schemas, and compare live in Frontier under
fr-87c29f. This component has no import or runtime dependency on that repository.
Synthetic fixtures validate runner behavior. Real measurements require a successful
authorized host invocation.

The runner is self-contained: its non-negative integer helper is local, and it
imports no session-cost module. Its output is an observation record, not a
versioned durable ledger API.

Ticket fr-55af2f notes hold one operator-run successful host Q sample on CLI
0.167.0, with the observation semantics this runner keeps: configured
gpt-6.1-sol/high/openai, raw input 24995, cached input 0, cache write 0, output
120 (including reasoning 38), total 25115, server turn duration 5151 ms. The
answer passed the recorded leap-year rubric. The returned source was `vscode`
despite stdio transport. This is evidence for that recorded surface and
configuration only, not a representative baseline. Calls, executed model and
USD were unavailable.

A2 is fc-92ecfa under fc-63bffb. Its connected-child quality cohort cannot be
pooled with this root-stdio sample. Resume/native restart and Claude
measurements are outside this component. Follow the A2 ticket's cohort and
configuration requirements before collecting further samples; fixture tests
alone do not establish real model cost or quality.
