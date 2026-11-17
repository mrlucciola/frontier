# Implementation decisions and limits

This file records where the implementation is narrower than the specification.

| Area | Implemented decision | Reason / consequence |
| --- | --- | --- |
| Incremental index | Full bounded content-hash discovery on demand; packets cached by fingerprints | Avoid timestamp-only staleness. Warm matches reduce uncertainty but do not yet avoid rereading files. No speed/token saving claim. |
| Retrieval | Deterministic lexical/path ranking; import/declaration text is searchable without a dedicated symbol graph | Reliable cross-language baseline; dedicated structural extraction and semantic clone detection remain unimplemented. |
| Evidence continuations | Omitted-result counts plus explicit narrower/targeted reads | No continuation handles to persist or invalidate. A partial packet never claims exhaustive coverage. |
| Scope roots | One explicit work root per invocation; optional relative source roots | No automatic cross-repo crawling or external-path grants. Additional workspaces use separate calls. |
| Observation collection | Explicit observe commands; current matching observations are included in discovery, stale/unread ones excluded | No transcript capture, background model, automatic policy promotion, or passive omniscience. |
| State schema | Version 1 supported; other versions refused | No invented migrations. A future schema change needs a tested migration. |
| Commands/checks | Explicit invocation-level argv and authorization reference; no executable repo config | Narrow authority boundary; no implicit execution of commands read from documentation. |
| Worktree scheduling | Guarded helpers plus batch waves and agent ownership contract | No distributed scheduler or cross-computer locks. |
| Write-surface declarations | Concrete relative paths/directories, normalized and compared case-insensitively; globs refused | Conservative macOS collision handling; no incomplete glob-intersection claim. |
| Telemetry | Command results and explicit summary exports; no persistent generic event stream | Reduce retained user data and write overhead. Pilot metrics are collected explicitly. |
| Retention | Explicit prune/purge commands | No background jobs or silent removal of checkpoints. |
| UI/runtime integration | Native skills plus optional global block; no `opencode.json` rewrite | Coexists with personalized installations; current loaded model context cannot be retracted. |
| Skill delivery | Skills live in the checkout; `deploy.sh` links them | The checkout is the only copy (R13). |
| Qualification | Automated mechanics and limited explicit-skill fresh-agent exercises | Not full implicit-routing evaluation, paired cost study, macOS verification, or production certification. |

These limits preserve standalone functionality and core scope. Retrieval quality for large repositories, broad implicit activation, and correction-cost benefits remain empirical pilot questions. CWF is a deployable candidate, not a claim that all acceptance scenarios have been behaviorally qualified.
