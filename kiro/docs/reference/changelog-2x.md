<!-- pinned-copy source: https://kiro.dev/changelog/cli (pages 1-5) + per-release pages /changelog/cli/<ver>/ | fetched: 2026-11-16 | pinned for: kiro-cli 2.x (work machine runs 2.17; surface differences with current online docs are expected) -->

# Kiro CLI changelog — 2.x series, condensed for kiro-cli 2.x integration work

Hand-condensed from the official CLI changelog on 2026-11-16. One section per
minor release; patches are listed with dates only where their notes live in
collapsed accordion sections that did not render through the fetch (marked
"notes collapsed"). Detail is fullest around 2.17 (the work-machine version):
full v2-relevant bullets for 2.15.0–2.20.2; one-liners elsewhere. Selection
filter: agents, steering, skills, hooks, toolsSettings/permissions, headless.
UI/model/pricing churn is skipped or mentioned in passing only.

Source index: https://kiro.dev/changelog/cli/ (pagination /page/2/ … /page/5/
cover 3.x down to 2.0; 1.x history is on /page/6/).

## The work-machine baseline: 2.15.0 → 2.20.2

### 2.15.0 — 2026-07-27 — "MCP OAuth, Auto Mode, and Custom Instructions"

Source: https://kiro.dev/changelog/cli/2-15/

- Headless/automation: new `--instructions` flag passes custom instructions to
  a headless session.
- Permissions: **Auto Mode** — AI classifier evaluates tool calls against the
  conversation context and auto-approves low-risk ones; fewer approval
  prompts. Enabled via the `chat.autoMode` setting; `--no-auto-mode` flag
  opts out for one session. Classifier audit trail via `/auto-mode`.
  (https://kiro.dev/docs/cli/chat/permissions/)
- MCP: trust levels `low` / `normal` for MCP tool approval policy; automatic
  re-authentication when OAuth tokens expire; `mcp auth status` / `mcp auth
  revoke` subcommands.
- Hooks: hook scripts receive the current user prompt (environment variable
  `user_prompt`, stdin JSON field `userPrompt`); `/hooks` lists managed
  hooks. (Hooks were introduced 2.13.0 as a V3-runtime feature — see 2.13.0
  below — the 2.15 entry does not state the runtime.)
- Patches: 2.15.1 (2026-07-28), 2.15.2 (2026-07-29) — notes collapsed
  (https://kiro.dev/changelog/cli/2-15/#patch-2-15-1, #patch-2-15-2).

### 2.16.0 — 2026-07-31 — "Steering Recognition, Model Picker Tabs, and Quick MCP Toggles"

Source: https://kiro.dev/changelog/cli/2-16/

- Steering: the agent now proactively references relevant steering files when
  they match the conversation. Configure via `/settings autonomy` levels or
  the `chat.steeringMode` setting. (https://kiro.dev/docs/cli/custom-agents/steering/#steering-modes)
- MCP: `/mcp enable <server>` / `/mcp disable <server>` without editing
  config files.
- Patches: 2.16.1 (2026-08-04), 2.16.2 (2026-08-06) — notes collapsed
  (https://kiro.dev/changelog/cli/2-16/#patch-2-16-1, #patch-2-16-2).

### 2.17.0 — 2026-08-11 — "Cloud Sessions Preview and Smarter Command Menus"

Source: https://kiro.dev/changelog/cli/2-17/

- Nothing in this release changes the local agent/steering/skills/hooks/
  permission surface — the 2.17 local runtime behaves as of 2.16.0.
- Cloud Sessions (preview): `/cloud start`, `/cloud status`, `/cloud
  stop`, `/cloud list`, `/cloud code`; opt-in (`chat.cloudSessions.enabled`).
  Local sessions never push conversation content; only explicit `/cloud
  start` shares metadata.
- Slash-command menu: compact layout, fuzzy matching, recency sorting.
- Add-on model credits; `/usage` per-model breakdown.
- `/terminal-config` sets up Shift+Enter from the chat prompt.
- Patches: none listed.

### 2.18.0 — 2026-08-14 — "AGENTS.md Steering, Smarter Context, Cloud Session Enhancements"

Source: https://kiro.dev/changelog/cli/2-18/

- **AGENTS.md as steering** (CLI 2.x feature; the 3.0 entry later marks
  "automatic AGENTS.md loading" as V2-only, deprecated in the V3 runtime):
  nested `AGENTS.md` files are recognized as steering and loaded on demand as
  the agent reads files in those directories; a **root `AGENTS.md` is loaded
  at session start**; existing steering controls apply (`inclusion: always|
  fileMatch|manual`, file-match patterns, glob ignore patterns).
  `chat.automaticAgentsInclusion` disables automatic loading.
  **One week newer than the work machine's 2.17 — do not rely on automatic
  AGENTS.md steering at 2.17.**
- Skills: skill definition changes take effect without restarting the session
  (hot-reload; add new skills immediately, edit a loaded skill and it's
  re-read next invocation).
- MCP: config hot-reload (edits to `mcp.json`/`.mcp.json` detected while
  running) plus `mcp reload` command.
- `/context` shows token usage breakdown by category with file details.
- Patch: 2.18.1 (2026-08-14) — notes collapsed
  (https://kiro.dev/changelog/cli/2-18/#patch-2-18-1).

### 2.19.0 — 2026-08-19 — "Faster Sessions, Subagent Control, Smarter Autopilot"

Source: https://kiro.dev/changelog/cli/2-19/

- Autopilot: once a plan is approved, repetitive follow-up tool calls are
  auto-approved; full control returns at plan completion, exit plan mode, or
  a task-blocking issue. (https://kiro.dev/docs/cli/autopilot/)
- Subagents: org admins can centrally allow/block specific subagents
  (governance); `chat.enabledSubagents` restricts which subagents load for a
  chat.
- Background subagents: pipeline stages run in parallel, monitored via
  `Ctrl+G` and the `/tasks` view.
- Performance: faster session startup; lower memory (400 MB+ on Windows).
- Patches: 2.19.1 (2026-08-21), 2.19.2 (2026-08-25) — notes collapsed
  (https://kiro.dev/changelog/cli/2-19/#patch-2-19-1, #patch-2-19-2).

### 2.20.0 — 2026-08-26 — "Prompt History, Subagent Status, Sign-in Anywhere"

Source: https://kiro.dev/changelog/cli/2-20/

- `/subagents` command: check, enable, disable, and manage subagents from the
  prompt; agent definitions can disable built-in subagents.
- Prompt history search across all projects.
- Sign in from devices without a local browser (paste a URL + code) —
  relevant to headless/remote environments.
- Patches: 2.20.1 (2026-08-28), 2.20.2 (2026-08-31) — notes collapsed
  (https://kiro.dev/changelog/cli/2-20/#patch-2-20-1, #patch-2-20-2).

## After the work machine (2.21 → 2.37) — surface drift to diff against 2.17

One-liners; full entries at the URLs. Items most relevant to the
agents/steering/skills/hooks/toolsSettings/headless surface are expanded.

| Version | Date | Title / v2-surface note | Source |
| --- | --- | --- | --- |
| 2.21.0 | 2026-09-04 | Small Models, MCP Apps, Vim Mode. **2.21.4 patch adds the `--v2` / `--v3` runtime-selection flags** ("kiro-cli chat --v2 forces the previous runtime") — a 2.17 binary has neither flag. | https://kiro.dev/changelog/cli/2-21/ |
| 2.22.0 | 2026-09-11 | Plan, Focus, Review. | https://kiro.dev/changelog/cli/2-22/ |
| 2.23.0 | 2026-09-14 | Power Model Pack. | https://kiro.dev/changelog/cli/2-23/ |
| 2.24.0 | 2026-09-16 | Web Chat and Session Sharing. | https://kiro.dev/changelog/cli/2-24/ |
| 2.25.0 | 2026-09-18 | Prompt Improvements. | https://kiro.dev/changelog/cli/2-25/ |
| 2.26.0 | 2026-09-21 | Web and Mobile GA; `/resume`, `/rename`. | https://kiro.dev/changelog/cli/2-26/ |
| 2.27.0 | 2026-09-23 | Hooks, Power Model Pack, and /model Tabs (hooks surface work — expand against 2.17 hooks behavior). | https://kiro.dev/changelog/cli/2-27/ |
| 2.28.0 | 2026-09-25 | AskUserQuestion, MCP Sampling, /feedback Reporting. | https://kiro.dev/changelog/cli/2-28/ |
| 2.29.0 | 2026-09-28 | Kiro-Driven Development Preview. | https://kiro.dev/changelog/cli/2-29/ |
| 2.30.0 | 2026-10-02 | Kiro Auto. | https://kiro.dev/changelog/cli/2-30/ |
| 2.31.0 | 2026-10-06 | OS-Level Sandboxing, **Saved Headless Settings**, 1-Hour Shell Commands — headless surface changes after 2.17. | https://kiro.dev/changelog/cli/2-31/ |
| 2.32.0 | 2026-10-08 | Session Recap. | https://kiro.dev/changelog/cli/2-32/ |
| 2.33.0 | 2026-10-13 | **Prompt as First Message** — headless invocation surface. | https://kiro.dev/changelog/cli/2-33/ |
| 2.34.0 | 2026-10-15 | OpenAI-Compatible API Keys — auth/headless. | https://kiro.dev/changelog/cli/2-34/ |
| 2.35.0 | 2026-10-19 | MCP Apps Preview, Worktree Support, Dynamic Workflow Preview. | https://kiro.dev/changelog/cli/2-35/ |
| 2.36.0 | 2026-10-21 | /goal, Model Browser, Org Model Picker. | https://kiro.dev/changelog/cli/2-36/ |
| 2.37.0 | 2026-10-26 | Model Param Tuning. Latest 2.x patch line: 2.37.2 (2026-11-13). | https://kiro.dev/changelog/cli/2-37/ |

## Before 2.15 (2.0 → 2.14) — provenance of what 2.17 already has

| Version | Date | Title / v2-surface note | Source |
| --- | --- | --- | --- |
| 2.0 | 2026-04-13 | Windows Support, **Headless Mode** (`--no-interactive`, `KIRO_API_KEY`, `--trust-all-tools` / `--trust-tools`; Pro/Pro+/Power API keys), Terminal UI as default (`--classic` to revert). Patch 2.0.1 (04-16). | https://kiro.dev/changelog/cli/2-0/ |
| 2.1 | 2026-04-24 | Real-time shell streaming; Tool Search (`toolSearch.enabled`); **skills in `.kiro/skills/` become `/skill-name` slash commands**; device-flow auth; RHEL support. Patch 2.1.1 (04-24). | https://kiro.dev/changelog/cli/2-1/ |
| 2.2.0 | 2026-04-27 | Adaptive thinking across turns. Patch 2.2.1 (05-04). | https://kiro.dev/changelog/cli/2-2/ |
| 2.3.0 | 2026-05-12 | `oauth.clientId` for MCP servers; **`KIRO_HOME` env var relocates global agents, prompts, skills, steering, settings, and sessions**; configurable V2 TUI keybindings; agent side channels (`$AGENT_DISPLAY_OUT`, `$AGENT_CONTEXT_OUT`). | https://kiro.dev/changelog/cli/2-3/ |
| 2.4.0 | 2026-05-20 | `/rewind`, `/effort`, unified `/settings`. Patches 2.4.1 (05-21), 2.4.2 (05-26). | https://kiro.dev/changelog/cli/2-4/ |
| 2.5.0 | 2026-05-29 | Thinking display; subagent review loops; `/settings display`. Patch 2.5.1 (06-01). | https://kiro.dev/changelog/cli/2-5/ |
| 2.6.0 | 2026-06-05 | Improved plan mode, prompt caching, session archives. Patches 2.6.1 (06-08), 2.6.2 (06-09). | https://kiro.dev/changelog/cli/2-6/ |
| 2.7.0 | 2026-06-10 | MCP Apps (preview); **custom agents inherit default resources (steering files, skills, AGENTS.md) when `extends` includes the built-in default agent**. Patch 2.7.1 (06-11). | https://kiro.dev/changelog/cli/2-7/ |
| 2.8.0 | 2026-06-16 | **V3 agent runtime early access** (`kiro-cli v3` / `kiro-cli chat --experimental-features v3`) — 2.x remains the v2 line. Patch 2.8.1 (06-17). | https://kiro.dev/changelog/cli/2-8/ |
| 2.9.0 | 2026-06-19 | 1M Context Window. | https://kiro.dev/changelog/cli/2-9/ |
| 2.10.0 | 2026-06-23 | MCP fine-grained policies for enterprise (allow MCP without broad file access); V3 progressive tool disclosure; **`chat.disableInheritingDefaultResources`** opts out of the 2.7.0 inheritance. Patch 2.10.1 (06-24). | https://kiro.dev/changelog/cli/2-10/ |
| 2.11.0 | 2026-06-26 | Web and Mobile Remote (remote chat/capture). Not condensed (fetch truncated; low 2.x-surface relevance). | https://kiro.dev/changelog/cli/2-11/ |
| 2.12.0 | ~2026-06-26..30 (date not captured) | Not condensed — body did not render in the captured page. | https://kiro.dev/changelog/cli/2-12/ |
| 2.13.0 | 2026-06-30 | **Hooks: "prompts, shell commands, and agents that run on specific events" — explicitly "a V3-only feature" at introduction, `kiro:` prefix for native hooks; global hooks in `~/.kiro/hooks/` with `includeInGlobalSession` flag** (managed hooks always included). Also checkpoints; three-way merge; `kiro-cli doctor`; `/help v3` vs `/help v2`. (https://kiro.dev/docs/cli/hooks/) | https://kiro.dev/changelog/cli/2-13/ |
| 2.14.0 | 2026-07-13 | `/upgrade-agent` converts existing agent configs to a superior format automatically. | https://kiro.dev/changelog/cli/2-14/ |

## Extraction limitations (recorded honestly)

- On changelog pages the **Improvements** and **Fixes** accordion sections do
  not render through markdown fetch — they are collapsed client-side.
  Patch-release notes (2.15.1/.2, 2.16.1/.2, 2.18.1, 2.19.1/.2, 2.20.1/.2,
  and the patch lines of 2.0–2.14) were therefore not captured beyond titles
  and dates; some patch anchor links are known.
- The 2.12.0 entry body and exact date were not captured (page truncation).
- The 2.11.0 entry was captured only through its section headings
  (Remote Chat, Remote Capture).
