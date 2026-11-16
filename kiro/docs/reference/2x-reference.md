<!-- pinned-copy source: https://kiro.dev/docs/cli/2x-reference.md | fetched: 2026-11-16 | pinned for: kiro-cli 2.x (work machine runs 2.17; surface differences with current online docs are expected) -->

# CLI 2.x reference

> Reference documentation for Kiro CLI 2.x hooks, agent config, and formats that changed in V3

This page documents CLI 2.x behavior for users who haven't yet migrated to V3. For the current format, see the [Hooks](https://kiro.dev/docs/hooks.md) documentation.

## Hooks

In CLI 2.x, hooks were embedded directly in the agent configuration file rather than in standalone files.

### Format

```json
{
  "hooks": {
    "agentSpawn": [{ "command": "echo 'starting'" }],
    "preToolUse": [{ "command": "npm run lint", "matcher": "fs_write" }]
  }
}
```

Each trigger name maps to an array of Hook definitions. Each definition has:

| Field | Description |
|-------|-------------|
| `command` | Shell command to execute |
| `matcher` | Tool-name selector for `preToolUse` and `postToolUse`; exact names, aliases, and supported wildcard patterns |

### Available triggers

| Trigger | Fires when | `matcher` matches |
|---------|-----------|-------------------|
| `agentSpawn` | Agent is activated | Not evaluated |
| `userPromptSubmit` | User submits a prompt | Not evaluated |
| `preToolUse` | Before a tool executes | Tool name |
| `postToolUse` | After a tool executes | Tool name |
| `stop` | The assistant finishes responding | Not evaluated |

### Hook communication

Hooks receive context as JSON via STDIN and communicate results through exit codes:

- **Exit code 0**: Hook succeeded. STDOUT is captured.
- **Exit code 2**: (preToolUse only) Block tool execution. STDERR is returned to the agent.
- **Other exit codes**: Hook failed. STDERR is shown as a warning.

### What changed in V3

- Legacy embedded object Hooks can be upgraded to current array definitions; use standalone `.kiro/hooks/*.json` files for profile-independent automation
- Trigger names changed to PascalCase (for example, `agentSpawn` → `SessionStart`)
- CLI V3 supports `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, and `Stop`, plus file triggers for agent-made changes and task triggers around spec execution
- Standalone Hook files use the versioned `v1` schema and support command or agent actions
- `Stop` command Hooks can return `` to continue the session

For the full migration guide, see [Hooks migration](https://kiro.dev/docs/cli/v3/hooks-migration.md).

## Permissions and tool trust

In CLI 2.x, tool permissions were managed through CLI flags, slash commands, and per-tool settings in agent config. In V3, per-tool settings are replaced by structured `permissions.yaml` files; the flags and slash commands remain as session-scoped overrides.

### CLI flags

```bash
kiro-cli --trust-all-tools
kiro-cli --trust-tools shell,write
```

### Slash commands

| Command | Description |
|---------|-------------|
| `/tools` | Show current permission status for all tools |
| `/tools trust <tool>` | Trust a specific tool for the session |
| `/tools untrust <tool>` | Revert a tool to per-request confirmation |
| `/tools trust-all` | Trust all tools (equivalent to `/acceptall`) |
| `/tools reset` | Reset all runtime permissions to defaults |

### Per-tool settings in agent config (`toolsSettings`)

```json
{
  "toolsSettings": {
    "shell": {
      "allowedCommands": ["git *", "npm *"],
      "deniedCommands": ["rm -rf *", "sudo *"]
    },
    "read": {
      "allowedPaths": ["src/**"],
      "deniedPaths": ["*.env"]
    }
  }
}
```

| Setting | Description |
|---------|-------------|
| `allowedCommands` | Regex patterns for auto-approved shell commands |
| `deniedCommands` | Regex patterns for blocked shell commands |
| `allowedPaths` | Gitignore-style glob patterns for auto-approved file paths |
| `deniedPaths` | Gitignore-style glob patterns for blocked file paths |
| `autoAllowReadonly` | Auto-approve read-only shell commands (e.g., `git status`) |
| `denyByDefault` | Block all tools unless explicitly allowed |

### Shell command trust levels (interactive)

When the agent requested a shell command, a tiered picker appeared:

```text
Press (↑↓) to navigate (⏎) to select scope
> Full command          → git pull --rebase
  Partial command       → git pull *
  Base command          → git *
  Entire Tool           → *
```

Trusted patterns persisted for the session and were stored as regex in `allowedCommands`.

### Read and write path trust levels (interactive)

When the agent needed to access a file outside the working directory:

```text
Press (↑↓) to navigate (⏎) to select scope
> Specific paths       → ~/.config/app/settings.json
  Complete directory   → ~/.config/app
  Entire Tool          → *
```

### What changed in V3

- `toolsSettings` replaced by `permissions.yaml` with `capability`/`match`/`effect` rules
- `--trust-all-tools` still works as a session-scope override but `permissions.yaml` is preferred
- Shell-command regexes move to permission globs; existing file-path rules remain gitignore-style glob patterns
- Separate per-tool deny was independent; now deny-always-wins across all scopes
- `autoAllowReadonly` converts through `/upgrade-agent` to a read-only-shell policy unless `denyByDefault` also applies; review the generated rules
- `denyByDefault` removed — use `exclude` patterns instead
- The `/tools` panel, `/tools trust-all`, and the approval picker remain available for session-level management

For the full migration guide, see [Permissions migration](https://kiro.dev/docs/cli/v3/permissions.md).

## Compaction

CLI 2.x compaction forks a new session that contains the compacted context:

- Run `/compact` manually, or let compaction trigger when the context window overflows.
- Resume the original CLI 2.x session with `/chat resume` when needed.
- Configure retention with `compaction.excludeMessages` and `compaction.excludeContextWindowPercent`.

CLI V3 instead records the compaction summary as a checkpoint marker within the same session. On reload, V3 loads that summary rather than replaying the full earlier history or creating a separate session. See [Compaction](https://kiro.dev/docs/compaction.md).

## Custom agent config

In CLI 2.x, agent configs were JSON-only with embedded `toolsSettings` and `hooks`.

### Built-in names

CLI 2.x custom agent configs can use built-in names such as `kiro_default` or `kiro_planner`. The V2 loader does not reject these configs as reserved-name conflicts. For current built-in agents and their roles, see [Built-in agents](https://kiro.dev/docs/custom-agents/built-in.md).

### Format

`.kiro/agents/my-agent.json`:

```json
{
  "name": "my-agent",
  "description": "A development agent",
  "prompt": "file://resources/MY_PROMPT.md",
  "model": "claude-sonnet-4.6",
  "tools": ["fs_read", "fs_write", "execute_bash", "grep", "glob", "code"],
  "toolsSettings": {
    "execute_bash": {
      "allowedCommands": ["^git status$", "^cargo build[^&;]*$"],
      "deniedCommands": ["^rm -rf"],
      "denyByDefault": false
    },
    "fs_read": {
      "allowedPaths": ["src/**", "docs/**"],
      "deniedPaths": [".env", "secrets/**"]
    },
    "fs_write": {
      "allowedPaths": ["src/**"],
      "deniedPaths": ["*.lock"]
    }
  },
  "resources": ["file://AGENTS.md"],
  "hooks": {
    "agentSpawn": [{ "command": "git status", "description": "Add git context" }]
  },
  "welcomeMessage": "Hello! How can I help?"
}
```

### What changed in V3

- **Markdown format** added (`.md` files with YAML frontmatter + body as system prompt)
- **`toolsSettings` removed** — replaced by `permissions` field with capability-based rules
- **`hooks` shape changed** — `/upgrade-agent` converts the object form to a profile-scoped array. Use standalone `.kiro/hooks/*.json` files for profile-independent or cross-surface automation.
- **New fields**: `excludedTools`, `includeMcpJson`, `includePowers`, `permissions`, `welcomeMessage`
- **Tags system** — tool names simplified to short categories (`read`, `write`, `shell`, `web`, `@mcp`, `@builtin`, `*`)
- **`resources` field** now supports `skill://` URIs in addition to `file://`

For the current format reference, see [Custom agents](https://kiro.dev/docs/custom-agents.md).
