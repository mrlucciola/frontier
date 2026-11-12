# Platform assumptions and verification

Official documentation checked during this build (2026-11-07):

- https://learn.chatgpt.com/docs/build-skills — native metadata-first disclosure, user skills under `~/.agents/skills`, symlink support, and duplicate names not automatically merged. CWF uses namespaced native skill directories and checks collisions.
- https://learn.chatgpt.com/docs/agent-configuration/agents-md — global guidance is read from CODEX_HOME; a nonempty AGENTS.override.md takes precedence over AGENTS.md. CWF detects the effective global file for its optional owned block.
- https://learn.chatgpt.com/docs/config-file/config-basic — personal and project settings have their own precedence/trust. CWF does not replace or reformat Codex config.toml.

These are documented assumptions, not live-client qualification. Current documentation may differ from the installed Codex/extension version. Native plugin distribution is a documented option; this pilot deliberately uses a reviewed local ZIP installer to support the requested per-computer rollout without a marketplace/service dependency.

CWF does not depend on lifecycle hooks or special APIs. Model selection of a skill remains probabilistic; a short global instruction is guidance, not enforcement. CLI, IDE, custom homes, managed installations, and skill-list truncation must be checked on each pilot environment. Doctor reports live visibility/behavior as NOT_TESTED rather than inferring it from file existence.
