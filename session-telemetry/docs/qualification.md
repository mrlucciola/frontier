# Adoption provenance and qualification

Read this when evaluating measurement evidence or planning a baseline. The
[usage guide](../README.md) covers invocation and the [observation contract](observations.md)
defines output semantics.

Historical readers, session-cost ledger schemas, and compare remain in Frontier
under fr-87c29f. This component has no import or runtime dependency on that repository.
Synthetic fixtures validate runner behavior. Real measurements require a successful
authorized host invocation.

Adopted from Frontier fr-55af2f commit
`7206911c0a9eaea4a0e4315769338d0f8eefd2fd`, limited to the fresh runner and its
tests/docs. The existing non-negative integer helper is local to the runner;
no historical session-cost module was copied. Existing consumers need no
migration; output retains the prototype's observation semantics. This is not
a versioned durable ledger API.

Ticket fr-55af2f notes preserve an operator-run successful host Q sample using
the prototype with CLI 0.167.0: configured gpt-6.1-sol/high/openai, raw input
24995, cached input 0, cache write 0, output 120 (including reasoning 38), total
25115, server turn duration 5151 ms. The answer passed the recorded leap-year
rubric. The returned source was `vscode` despite stdio transport. These are
provenance for that recorded surface/configuration, not a new destination run
or a representative baseline. Calls, executed model and USD were unavailable.

A2 remains fc-92ecfa under fc-63bffb. Its existing connected-child quality
cohort cannot be pooled with this root-stdio sample. Resume/native restart
and Claude measurements are outside this component. Follow the A2 ticket's
cohort and configuration requirements before collecting further samples;
fixture tests alone do not establish real model cost or quality.
