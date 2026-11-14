/**
 * pm for OpenCode: maps OpenCode's events to `pm hook <event>`.
 *
 * Session start (first prompt) and every later pm or wt bash call refresh one keyed
 * instruction entry from `pm hook session-start`. On session idle it runs
 * `pm hook stop`; exit 2 delivers pm's stderr as a synthetic turn, once, because
 * every later call passes stop_hook_active. pm decides everything: no ticket
 * parsing here. Agents in `skipAgents` get nothing. Any error leaves OpenCode
 * untouched.
 */
import { Plugin } from "@opencode/plugin"
import { execFile } from "node:child_process"

const ENTRY_KEY = "pm"

type Result = { code: number; out: string; err: string }

function pmHook(pm: string, event: string, input: Record<string, unknown>): Promise<Result> {
  return new Promise((resolve) => {
    const child = execFile(
      pm,
      ["hook", event],
      { cwd: String(input.cwd ?? process.cwd()), timeout: 4000 },
      (error: any, stdout, stderr) => {
        const code = error ? (typeof error.code === "number" ? error.code : 1) : 0
        resolve({ code, out: String(stdout).trim(), err: String(stderr).trim() })
      },
    )
    child.stdin?.end(JSON.stringify(input))
  })
}

export default Plugin.define({
  id: "pm",
  async setup(ctx) {
    const opts = (ctx.options ?? {}) as Record<string, unknown>
    const pm =
      typeof opts.pm === "string" ? opts.pm : process.env.PM_BIN || `${process.env.HOME}/.local/bin/pm`
    const skipAgents: string[] = Array.isArray(opts.skipAgents) ? (opts.skipAgents as string[]) : []

    const started = new Set<string>()
    const watching = new Set<string>()

    async function where(sessionID: string): Promise<string | undefined> {
      const info: any = await ctx.session.get({ sessionID })
      const agent: string = info?.agent ?? info?.agentID ?? ""
      if (skipAgents.includes(agent)) return undefined
      return info?.directory ?? info?.path ?? ctx.location.directory
    }

    async function refresh(sessionID: string, cwd: string) {
      const r = await pmHook(pm, "session-start", { cwd, session_id: sessionID })
      if (r.code === 0 && r.out) {
        await ctx.session.instructions.entry.put({ sessionID, key: ENTRY_KEY, value: r.out })
      }
    }

    async function watch(sessionID: string, cwd: string) {
      if (watching.has(sessionID)) return
      watching.add(sessionID)
      let active = false
      try {
        for (;;) {
          await ctx.session.wait({ sessionID })
          const r = await pmHook(pm, "stop", { cwd, session_id: sessionID, stop_hook_active: active })
          if (r.code === 2 && r.err) {
            active = true
            await ctx.session.synthetic({ sessionID, text: `[pm] ${r.err}` })
          }
        }
      } catch {
        /* session gone or wait unsupported */
      } finally {
        watching.delete(sessionID)
      }
    }

    await ctx.session.hook("prompt", async (ev) => {
      try {
        const sid = ev.sessionID
        if (started.has(sid)) return
        started.add(sid)
        const cwd = await where(sid)
        if (!cwd) return
        await refresh(sid, cwd)
        void watch(sid, cwd)
      } catch {
        /* fail open */
      }
    })

    await ctx.tool.hook("execute.after", async (ev: any) => {
      try {
        if (ev?.tool !== "bash" || ev?.status !== "completed") return
        const cmd: string = ev?.input?.command ?? ""
        if (!/(^|[;&| ])(pm|wt)( |$)/.test(cmd)) return
        const sid: string | undefined = ev?.sessionID
        if (!sid || !started.has(sid)) return
        const cwd = await where(sid)
        if (cwd) await refresh(sid, cwd)
      } catch {
        /* fail open */
      }
    })
  },
})
