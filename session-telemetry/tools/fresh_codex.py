"""Measure one explicitly authorized fresh Codex app-server turn, without log reads.

This is a standalone observation, never a session-cost ledger row. Only the
new ephemeral thread is consumed. Model calls cannot be counted from cumulative
token snapshots: identical consecutive calls need not change `last`.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time

def int_field(obj, key):
    """obj[key] as a non-negative int, or None when absent or not an int."""
    v = obj.get(key) if isinstance(obj, dict) else None
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


TOKEN_FIELDS = ("inputTokens", "cachedInputTokens", "cacheWriteInputTokens",
                "outputTokens", "reasoningOutputTokens", "totalTokens")
REQUIRED_TOKENS = set(TOKEN_FIELDS) - {"cacheWriteInputTokens"}
TOOL_TYPES = {"commandExecution", "fileChange", "mcpToolCall", "dynamicToolCall",
              "collabToolCall", "webSearch", "imageView"}


class Observation:
    """One fresh thread/turn. Keep snapshots; never add interim/final totals."""

    def __init__(self):
        self.thread_id = self.turn_id = None
        self.configuration = {}
        self.usage = None
        self.turn = None
        self.items = {}
        self.reroutes = []
        self.retry_notices = 0
        self.duplicates = 0
        self.diagnostics = Counter()

    def configure(self, result):
        if not isinstance(result, dict) or not isinstance(result.get("thread"), dict):
            raise ValueError("malformed thread response")
        thread = result.get("thread", {})
        self.thread_id = thread.get("id")
        self.configuration = {k: result.get(k) for k in (
            "model", "modelProvider", "reasoningEffort", "serviceTier", "cwd",
            "sandbox", "approvalPolicy", "approvalsReviewer", "instructionSources")}
        self.configuration.update({k: thread.get(k) for k in (
            "ephemeral", "cliVersion", "source", "parentThreadId")})
        if not isinstance(self.thread_id, str) or thread.get("ephemeral") is not True:
            raise ValueError("fresh ephemeral thread not confirmed")
        if thread.get("parentThreadId") is not None:
            raise ValueError("unexpected child thread")

    def feed(self, message):
        p = message.get("params", {})
        if not isinstance(p, dict) or p.get("threadId") != self.thread_id:
            return
        nested_turn = p.get("turn")
        event_turn = p.get("turnId") or (nested_turn.get("id") if isinstance(nested_turn, dict) else None)
        if self.turn_id is None or event_turn != self.turn_id:
            return
        method = message.get("method")
        if method == "thread/tokenUsage/updated":
            u = p.get("tokenUsage")
            if not isinstance(u, dict) or not isinstance(u.get("total"), dict):
                self.diagnostics["malformed_usage"] += 1
                return
            # Missing fields remain None, including cache-write (even though the
            # protocol schema has a default). No absent field becomes free usage.
            snapshot = {part: {k: int_field(u.get(part), k) for k in TOKEN_FIELDS}
                        for part in ("total", "last")}
            if snapshot == self.usage:
                self.duplicates += 1
                return
            if self.usage is not None and any(
                snapshot["total"][k] is not None and self.usage["total"][k] is not None
                and snapshot["total"][k] < self.usage["total"][k] for k in TOKEN_FIELDS
            ):
                self.diagnostics["regressing_usage"] += 1
            self.usage = snapshot
            total = snapshot["total"]
            if any(total[k] is None for k in REQUIRED_TOKENS):
                self.diagnostics["partial_usage"] += 1
            i, c, o, r, t = (total[k] for k in (
                "inputTokens", "cachedInputTokens", "outputTokens", "reasoningOutputTokens", "totalTokens"))
            if ((i is not None and c is not None and c > i)
                    or (o is not None and r is not None and r > o)
                    or (None not in (i, o, t) and i + o != t)):
                self.diagnostics["inconsistent_usage"] += 1
        elif method == "turn/completed":
            turn = p.get("turn", {})
            if not isinstance(turn, dict):
                raise ValueError("malformed terminal turn")
            terminal = {k: turn.get(k) for k in ("status", "startedAt", "completedAt", "durationMs")}
            for key in ("startedAt", "completedAt", "durationMs"):
                if terminal[key] is not None and int_field(turn, key) is None:
                    self.diagnostics["malformed_timing"] += 1
                    terminal[key] = None
            error = turn.get("error")
            if error is not None and not isinstance(error, dict):
                self.diagnostics["malformed_turn_error"] += 1
            terminal["error_info"] = error.get("codexErrorInfo") if isinstance(error, dict) else None
            if self.turn == terminal:
                self.duplicates += 1
            elif self.turn is not None:
                self.diagnostics["conflicting_terminal"] += 1
            else:
                self.turn = terminal
            for item in turn.get("items", []):
                self._item(item)
        elif method == "item/completed":
            self._item(p.get("item", {}))
        elif method == "error" and p.get("willRetry") is True:
            # These notifications have no event identity. Count receipts,
            # including any retransmission; never label them inference calls.
            self.retry_notices += 1
        elif method == "model/rerouted":
            route = {k: p.get(k) for k in ("fromModel", "toModel", "reason")}
            if route not in self.reroutes:
                self.reroutes.append(route)

    def _item(self, item):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            return
        # Do not retain commands, arguments, tool results or reasoning content.
        value = {k: item.get(k) for k in ("type", "status", "durationMs")}
        if item.get("type") == "agentMessage":
            value.update(text=item.get("text"), phase=item.get("phase"))
        previous = self.items.get(item["id"])
        if previous == value:
            self.duplicates += 1
        elif previous is not None:
            self.diagnostics["conflicting_item"] += 1
        else:
            self.items[item["id"]] = value

    def result(self, failure=None):
        total = self.usage["total"] if self.usage is not None else None
        status = (self.turn or {}).get("status")
        if failure:
            outcome = failure
        elif status != "completed":
            outcome = status if status in ("failed", "interrupted") else "incomplete"
        elif any(k != "partial_usage" for k in self.diagnostics):
            outcome = "invalid_telemetry"
        elif total is None:
            outcome = "completed_usage_unavailable"
        elif any(total[k] is None for k in REQUIRED_TOKENS):
            outcome = "completed_usage_partial"
        elif total["inputTokens"] == total["outputTokens"] == 0:
            outcome = "completed_zero_usage"
        else:
            outcome = "completed_with_usage"
        return {
            "surface": "codex_app_server_stdio", "phase": "fresh_ephemeral_turn",
            "outcome": outcome, "thread_id": self.thread_id, "turn_id": self.turn_id,
            "configuration": self.configuration, "executed_model": None,
            "model_reroutes": self.reroutes, "usage_snapshot": self.usage,
            "model_calls": None, "retry_notice_receipts": self.retry_notices,
            "server_turn": self.turn,
            "tool_items": [{"id": k, **v} for k, v in self.items.items() if v["type"] in TOOL_TYPES],
            "agent_messages": [{"id": k, **v} for k, v in self.items.items() if v["type"] == "agentMessage"],
            "duplicate_snapshots_or_items": self.duplicates,
            "diagnostics": dict(self.diagnostics),
        }


def measure(command, *, cwd, model, effort, prompt, timeout=180):
    """Drive only initialize/thread-start/turn-start (+ own interrupt on failure).

    `command` is injected only for fixture subprocess tests. The CLI always uses
    the installed `codex app-server`, inheriting authentication and policy.
    """
    observation = Observation()
    started = time.monotonic()
    deadline = started + timeout
    stderr_hash = hashlib.sha256()
    stderr_bytes = 0
    stdout_bytes = 0
    pending = []
    replies = {}
    buffer = b""
    failure = None
    turn_requested = None
    process = None
    selector = selectors.DefaultSelector()

    def send(message):
        process.stdin.write((json.dumps(message) + "\n").encode())
        process.stdin.flush()

    def stop_input(interrupt=False):
        if not process.stdin.closed:
            try:
                if interrupt and observation.thread_id and observation.turn_id:
                    send({"id": 3, "method": "turn/interrupt", "params": {
                        "threadId": observation.thread_id, "turnId": observation.turn_id}})
            finally:
                try:
                    process.stdin.close()
                except OSError:
                    pass  # a failed/closed server still needs its local pipe closed

    try:
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        send({"id": 0, "method": "initialize", "params": {
            "clientInfo": {"name": "frontier_fresh_telemetry", "version": "0.1.0"}}})
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = failure or ("shutdown_timeout" if observation.turn else "timed_out")
                stop_input(interrupt=True)
                break
            for key, _ in selector.select(min(remaining, 0.1)):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == "stderr":
                    stderr_bytes += len(chunk)
                    stderr_hash.update(chunk)
                    continue
                stdout_bytes += len(chunk)
                if stdout_bytes > 32 * 1024 * 1024:
                    failure = "stream_limit_exceeded"
                    stop_input(interrupt=True)
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    if not isinstance(msg, dict):
                        raise ValueError("protocol message is not an object")
                    if "id" in msg and "method" in msg:
                        failure = "interactive_request_required"
                        stop_input(interrupt=True)
                    elif "id" in msg:
                        if msg["id"] in replies:
                            if replies[msg["id"]] != msg:
                                raise ValueError("conflicting RPC response")
                            observation.duplicates += 1
                            continue
                        replies[msg["id"]] = msg
                        if "error" in msg:
                            failure = "rpc_error"
                            stop_input(interrupt=True)
                        elif msg["id"] == 0:
                            send({"method": "initialized", "params": {}})
                            send({"id": 1, "method": "thread/start", "params": {
                                "cwd": str(cwd), "model": model, "ephemeral": True,
                                "config": {"model_reasoning_effort": effort}}})
                        elif msg["id"] == 1:
                            observation.configure(msg["result"])
                            turn_requested = time.monotonic()
                            send({"id": 2, "method": "turn/start", "params": {
                                "threadId": observation.thread_id,
                                "input": [{"type": "text", "text": prompt}]}})
                        elif msg["id"] == 2:
                            observation.turn_id = msg["result"]["turn"]["id"]
                            if not isinstance(observation.turn_id, str):
                                raise ValueError("missing turn id")
                            for event in pending:
                                observation.feed(event)
                            pending.clear()
                    elif observation.turn_id is not None:
                        observation.feed(msg)
                    elif observation.thread_id is not None:
                        pending.append(msg)
                    if observation.turn is not None or failure:
                        # Closing input requests normal app-server shutdown. Drain
                        # stdout so usage delivered after turn/completed is retained.
                        stop_input()
                        deadline = min(deadline, time.monotonic() + 5)
        if buffer.strip():
            failure = failure or "truncated_stream"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        failure = "launch_error" if process is None else "protocol_error"
        observation.diagnostics[type(exc).__name__] += 1
    finally:
        selector.close()
        if process is not None:
            try:
                stop_input(interrupt=observation.turn is None)
            except (OSError, ValueError):
                pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Signal the server's whole group while its unreaped leader still
                # holds the group ID, so children it started do not outlive it.
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(process.pid, sig)
                    except OSError:
                        pass  # already gone; wait() below still reaps it
                    try:
                        process.wait(timeout=2)
                        break
                    except subprocess.TimeoutExpired:
                        continue
                if process.poll() is None:
                    process.kill()
                    process.wait()
            process.stdout.close()
            process.stderr.close()
    if process is not None and process.returncode != 0:
        failure = failure or "process_failed"
    result = observation.result(failure)
    result.update({
        "requested": {"cwd": str(cwd), "model": model, "reasoning_effort": effort},
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "process_exit_code": process.returncode if process is not None else None,
        "observer_process_elapsed_s": time.monotonic() - started,
        "observer_turn_request_to_exit_s": time.monotonic() - turn_requested if turn_requested else None,
        "stderr_bytes": stderr_bytes, "stderr_sha256": stderr_hash.hexdigest(),
    })
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, required=True, help="explicit disposable task fixture")
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True, choices=("none", "minimal", "low", "medium", "high", "xhigh", "max"))
    parser.add_argument("--timeout", type=float, default=180, help="process observation limit, 0 < seconds <= 180")
    parser.add_argument("prompt", help="inline authorized test prompt; never a prompt filename")
    args = parser.parse_args(argv)
    if not args.cwd.is_dir() or not 0 < args.timeout <= 180:
        parser.error("--cwd must exist and --timeout must be > 0 and <= 180")
    result = measure(["codex", "app-server"], cwd=args.cwd.resolve(), model=args.model,
                     effort=args.effort, prompt=args.prompt, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["outcome"] == "completed_with_usage" else 1


if __name__ == "__main__":
    raise SystemExit(main())
