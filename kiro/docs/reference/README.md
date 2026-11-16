# kiro/docs/reference — pinned kiro 2.x reference (batch 0)

Verbatim snapshots of official Kiro documentation, pinned on 2026-11-16 to
spec kiro-cli 2.17 integration work offline. The work machine runs kiro-cli
**2.17**; kiro.dev now documents the 3.x era, so differences between these
pages and the live site are expected and are findings, not errors. Batch 0
covers the agent-config surface: custom agents, steering, skills, hooks,
configuration scopes, headless mode, and the 2.x changelog.

## Conventions

- Each pinned file's first line is a header comment:
  `<!-- pinned-copy source: <url> | fetched: <date> | pinned for: kiro-cli 2.x (...) -->`
  followed by the page content verbatim. Site nav/footer chrome and the
  injected "Documentation Index" blockquote were stripped; all technical
  content, tables, and "what changed in V3" sections were kept.
- `changelog-2x.md` is the exception: hand-condensed, not verbatim, with a
  source URL per release.
- Where the source pages use product tabs (IDE / CLI / Web, or CLI V3 /
  CLI 2.x legacy), the fetched markdown flattens them in document order.
  Attribute a path or flag to the CLI 2.x tab before relying on it.

## Files

| File | Governs for kiro-cli 2.x work | Source |
| --- | --- | --- |
| [2x-reference.md](2x-reference.md) | CLI 2.x reference landing: command/surface index incl. hook Stop-command behavior | https://kiro.dev/docs/cli/2x-reference.md |
| [agent-harness.md](agent-harness.md) | Agent loop/harness behavior (described from the 3.x era — diff against 2.17) | https://kiro.dev/docs/cli/agent-harness.md |
| [headless.md](headless.md) | Non-interactive mode: flags, `KIRO_API_KEY`, trust flags, CI usage | https://kiro.dev/docs/cli/headless.md |
| [configuration-scopes.md](configuration-scopes.md) | Config file scopes/precedence (global `~/.kiro/` vs project `.kiro/`, settings.json layers) | https://kiro.dev/docs/configuration.md |
| [custom-agents.md](custom-agents.md) | Custom agent definitions: location, `extends`, includes, activation | https://kiro.dev/docs/custom-agents.md |
| [custom-agents-configuration-reference.md](custom-agents-configuration-reference.md) | Full agent JSON schema: tools, toolsSettings, MCP servers, resources | https://kiro.dev/docs/custom-agents/configuration-reference.md |
| [custom-agents-examples.md](custom-agents-examples.md) | Worked agent config examples | https://kiro.dev/docs/custom-agents/examples.md |
| [skills.md](skills.md) | Skills: layout, SKILL.md format, invocation, global/project dirs | https://kiro.dev/docs/skills.md |
| [steering.md](steering.md) | Steering: file layout, inclusion modes, AGENTS.md relationship | https://kiro.dev/docs/steering.md |
| [changelog-2x.md](changelog-2x.md) | Condensed 2.0 → 2.37.2 release history with per-release URLs; detail fullest at 2.15–2.20; provenance one-liners elsewhere | https://kiro.dev/changelog/cli/ (pages 1–5 + per-release pages) |

## Open questions (what the fetched pages actually say)

1. **Exact global skills directory in 2.x.** skills.md (current, V3-era
   wording) says CLI global skills live in `~/.kiro/skills/`; changelog 2.1
   introduces project skills `.kiro/skills/` as slash commands, and 2.3.0's
   `KIRO_HOME` relocates "global ... skills", implying a global skills dir
   existed by 2.3 — but no fetched page pins the path for a 2.17 v2
   runtime. Verify against the 2.17 binary.
2. **AGENTS.md inheritance at 2.17.** Automatic AGENTS.md steering (root
   `AGENTS.md` loaded at session start, nested files discovered on read,
   `chat.automaticAgentsInclusion`) landed in **2.18.0** — one week *after*
   2.17.0, so 2.17 predates it. What 2.17 *does* have, from 2.7.0: custom
   agents that `extends` the built-in default inherit default resources
   (steering files, skills, AGENTS.md), with `chat.disableInheritingDefaultResources`
   (2.10.0) as opt-out. steering.md itself only describes the V3 behavior
   plus flattened V1/V2 caveats.
3. **Hooks in the 2.17 v2 runtime.** Changelog 2.13.0 introduces hooks as "a
   V3-only feature" (`kiro:` prefix, global hooks in `~/.kiro/hooks/` with
   `includeInGlobalSession`); 2.15.0 adds `user_prompt` to hooks without
   naming a runtime. Whether hooks fire at all in 2.17's v2 runtime is
   unresolved from these pages — verify on the machine.
4. **No runtime-switch flags at 2.17.** `--v2`/`--v3` were added in the
   2.21.4 patch. On 2.17 the V3 runtime, if present at all, is reached via
   `kiro-cli v3` / `--experimental-features v3` (2.8.0 early access).
   agent-harness.md describes the 3.x harness — treat everything in it as a
   hypothesis at 2.17.
5. **steering.md inclusion modes at V1/V2.** The flattened tabs show
   partial support for older runtimes (noted around `always`); the exact
   V2 support matrix for `fileMatch`/`manual` is not cleanly recoverable
   from the flattened page — cross-check changelog 2.16.0
   (`chat.steeringMode`) and the 2x-reference page.
6. **Rendering artifacts.** 2x-reference.md's Stop-hook sentence contains an
   empty inline-code span ("Hooks can return `` to continue the session") —
   artifact of the source render. Changelog Improvements/Fixes accordions
   did not render (see "Extraction limitations" in changelog-2x.md), so
   patch-release bodies for 2.15.x–2.20.x are uncaptured, and 2.11.0/2.12.0
   entries are uncondensed.
