"""Measure one explicitly authorized OpenCode turn in a fresh or resumed session.

The turn runs through `opencode run --standalone`; the observation is then read
back for that one session through `opencode api`. No log, transcript-file or
database reads. This is a standalone observation, never a session-cost ledger
row, and a resumed turn never re-reports what the session held before it.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

SURFACE = "opencode_run_standalone"
PHASES = {"fresh": "fresh_session_turn", "resume": "resumed_session_turn"}
TOKEN_FIELDS = ("input", "output", "reasoning", "cache_read", "cache_write")
REQUIRED_TOKENS = ("input", "output")
STEP_TIMES = ("created", "firstToken", "streamed", "completed")
PATH_KEYS = ("config", "data", "db", "state", "cache")
PAGE_LIMIT = 100
MAX_PAGES = 50
API_TIMEOUT = 60
MAX_TIMEOUT = 600


class ApiError(Exception):
    """A read-back request failed; `detail` is the operation and server tag only."""

    def __init__(self, operation, reason):
        super().__init__(f"{operation}: {reason}")
        self.detail = {"operation": operation, "reason": reason}


def number(value):
    """A non-negative number, or None when absent or not a number."""
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0 else None


def tokens(info):
    """Flatten a TokenUsage object. Missing fields stay None, never zero."""
    info = info if isinstance(info, dict) else {}
    cache = info.get("cache") if isinstance(info.get("cache"), dict) else {}
    return {"input": number(info.get("input")), "output": number(info.get("output")),
            "reasoning": number(info.get("reasoning")),
            "cache_read": number(cache.get("read")), "cache_write": number(cache.get("write"))}


def totals(session):
    """The session's cumulative provider totals, as reported."""
    return {"tokens": tokens(session.get("tokens")), "cost_usd": number(session.get("cost"))}


def text_digest(text):
    data = text.encode() if isinstance(text, str) else b""
    return hashlib.sha256(data).hexdigest(), len(data)


class Client:
    """The installed CLI. `command` is replaced only by fixture tests."""

    def __init__(self, command, cwd):
        self.command = list(command)
        self.cwd = cwd

    def output(self, *args):
        done = subprocess.run([*self.command, *args], cwd=self.cwd, stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=API_TIMEOUT)
        return done.returncode, done.stdout, done.stderr

    def api(self, operation, **params):
        """One read-only request. Returns the body, or None for an unknown session."""
        argv = ["api", "--standalone", operation]
        for key, value in params.items():
            argv += ["--param", f"{key}={value}"]
        try:
            code, out, err = self.output(*argv)
        except subprocess.TimeoutExpired:
            raise ApiError(operation, "timed_out") from None
        body = None
        for line in (out.strip(), *err.splitlines()):
            try:
                body = json.loads(line)
            except ValueError:
                continue
            break
        if not isinstance(body, dict):
            raise ApiError(operation, "not_json")
        if body.get("_tag") == "SessionNotFoundError":
            return None
        if code != 0 or "data" not in body:
            raise ApiError(operation, str(body.get("_tag") or "malformed"))
        return body


def session_info(client, session_id):
    body = client.api("session.get", sessionID=session_id)
    if body is None:
        return None
    if not isinstance(body["data"], dict):
        raise ApiError("session.get", "malformed")
    return body["data"]


def session_messages(client, session_id):
    """Every projected message of this one session, oldest first."""
    found, seen = [], set()
    params = {"order": "asc", "limit": PAGE_LIMIT}
    for _ in range(MAX_PAGES):
        body = client.api("session.message.list", sessionID=session_id, **params)
        if body is None:
            raise ApiError("session.message.list", "SessionNotFoundError")
        if not isinstance(body["data"], list):
            raise ApiError("session.message.list", "malformed")
        for message in body["data"]:
            if isinstance(message, dict) and isinstance(message.get("id"), str) and message["id"] not in seen:
                seen.add(message["id"])
                found.append(message)
        cursor = body.get("cursor")
        following = cursor.get("next") if isinstance(cursor, dict) else None
        if not following:
            return found
        params = {"cursor": following, "limit": PAGE_LIMIT}
    raise ApiError("session.message.list", "page_limit_exceeded")


def run_turn(client, argv, timeout):
    """Run the turn to exit. Never answers a prompt and never auto-approves."""
    started = time.monotonic()
    process = subprocess.Popen([*client.command, *argv], cwd=client.cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        out = err = b""
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except OSError:
                pass  # already gone; communicate() below still reaps it
            try:
                out, err = process.communicate(timeout=5)
                break
            except subprocess.TimeoutExpired:
                continue
        if process.poll() is None:
            process.kill()
            out, err = process.communicate()
    # The stream's event schema is not published; keep counts, never contents.
    stream = {"bytes": len(out), "json_lines": 0, "other_lines": 0, "event_types": Counter()}
    for line in out.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            stream["other_lines"] += 1
            continue
        stream["json_lines"] += 1
        kind = event.get("type") if isinstance(event, dict) else None
        stream["event_types"][kind if isinstance(kind, str) else "untyped"] += 1
    stream["event_types"] = dict(stream["event_types"])
    return {"timed_out": timed_out, "exit_code": process.returncode, "stream": stream,
            "elapsed_s": time.monotonic() - started,
            "stderr_bytes": len(err), "stderr_sha256": hashlib.sha256(err).hexdigest()}


def reduce_messages(messages, prompt):
    """Reduce the phase's new messages. Tool input/output and reasoning are discarded."""
    reduced = {"steps": [], "agent_messages": [], "tool_items": [], "skills": [],
               "context_messages": [], "idle": [], "user_messages": 0, "prompt_echoed": False,
               "other_message_types": Counter()}
    for message in messages:
        kind = message.get("type")
        if kind == "assistant":
            model = message.get("model") if isinstance(message.get("model"), dict) else {}
            times = message.get("time") if isinstance(message.get("time"), dict) else {}
            error = message.get("error") if isinstance(message.get("error"), dict) else {}
            retry = message.get("retry") if isinstance(message.get("retry"), dict) else {}
            reduced["steps"].append({
                "id": message["id"], "agent": message.get("agent"),
                "model": {k: model.get(k) for k in ("id", "providerID", "variant")},
                "finish": message.get("finish"), "tokens": tokens(message.get("tokens")),
                "cost_usd": number(message.get("cost")),
                "time": {k: number(times.get(k)) for k in STEP_TIMES},
                "error_type": error.get("type"), "retry_attempt": retry.get("attempt")})
            content = message.get("content") if isinstance(message.get("content"), list) else []
            said = [part.get("text") for part in content
                    if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str)]
            if said:
                reduced["agent_messages"].append({"id": message["id"], "text": "".join(said)})
            for part in content:
                if isinstance(part, dict) and part.get("type") == "tool":
                    state = part.get("state") if isinstance(part.get("state"), dict) else {}
                    times = part.get("time") if isinstance(part.get("time"), dict) else {}
                    reduced["tool_items"].append({
                        "id": part.get("id"), "message_id": message["id"], "name": part.get("name"),
                        "status": state.get("status"), "executed": part.get("executed"),
                        "time": {k: number(times.get(k)) for k in ("created", "ran", "completed")}})
        elif kind == "skill":
            reduced["skills"].append({k: message.get(k) for k in ("id", "skill", "name")})
        elif kind in ("system", "synthetic"):
            digest, size = text_digest(message.get("text"))
            reduced["context_messages"].append({
                "id": message["id"], "type": kind, "description": message.get("description"),
                "text_sha256": digest, "text_bytes": size})
        elif kind == "idle":
            error = message.get("error") if isinstance(message.get("error"), dict) else {}
            reduced["idle"].append({"id": message["id"], "outcome": message.get("outcome"),
                                    "error_type": error.get("type")})
        elif kind == "user":
            reduced["user_messages"] += 1
            reduced["prompt_echoed"] = reduced["prompt_echoed"] or message.get("text") == prompt
        else:
            reduced["other_message_types"][kind if isinstance(kind, str) else "untyped"] += 1
    reduced["other_message_types"] = dict(reduced["other_message_types"])
    return reduced


def step_sum(steps):
    """Per-field sum over this phase's steps; a field any step lacks stays None."""
    if not steps:
        return None
    summed = {}
    for field in TOKEN_FIELDS:
        values = [step["tokens"][field] for step in steps]
        summed[field] = None if None in values else sum(values)
    costs = [step["cost_usd"] for step in steps]
    return {"tokens": summed, "cost_usd": None if None in costs else sum(costs)}


def delta(before, after):
    """after - before per field. None when either side is missing; a decrease is kept negative."""
    def sub(a, b):
        return None if a is None or b is None else a - b
    return {"tokens": {k: sub(after["tokens"][k], before["tokens"][k]) for k in TOKEN_FIELDS},
            "cost_usd": sub(after["cost_usd"], before["cost_usd"])}


def classify(failure, run, reduced, session, phase_usage, diagnostics):
    """Outcome plus the evidence that the turn reached a terminal state."""
    if failure:
        return failure, None
    reported = [entry["outcome"] for entry in reduced["idle"]]
    if reported:
        outcome, evidence = reported[-1], "idle_message"
    elif session.get("outcome") is not None:
        outcome, evidence = session.get("outcome"), "session_outcome"
    elif run["exit_code"] == 0 and reduced["steps"] and reduced["steps"][-1]["finish"] == "stop":
        outcome, evidence = "succeeded", "final_step_finish"
    else:
        outcome, evidence = None, None
    if outcome in ("failed", "interrupted"):
        return outcome, evidence
    if run["exit_code"] != 0:
        return "process_failed", evidence
    if outcome != "succeeded":
        return "incomplete", evidence
    if diagnostics:
        return "invalid_telemetry", evidence
    if phase_usage is None:
        return "completed_usage_unavailable", evidence
    used = phase_usage["tokens"]
    if any(used[k] is None for k in REQUIRED_TOKENS):
        return "completed_usage_partial", evidence
    if not any(used[k] for k in TOKEN_FIELDS):
        return "completed_zero_usage", evidence
    return "completed_with_usage", evidence


def host_configuration(client):
    """Version and resolved paths. Config sources are hashed, never printed."""
    configuration = {"cli_version": None, "paths": None,
                     "config_sources_sha256": None, "config_sources_bytes": None}
    code, out, _ = client.output("--version")
    if code == 0:
        configuration["cli_version"] = out.decode(errors="replace").strip() or None
    code, out, _ = client.output("debug", "paths")
    if code == 0:
        rows = dict(line.split(None, 1) for line in out.decode(errors="replace").splitlines()
                    if len(line.split(None, 1)) == 2)
        configuration["paths"] = {k: rows.get(k) for k in PATH_KEYS}
    code, out, _ = client.output("debug", "config")
    if code == 0:
        configuration["config_sources_sha256"] = hashlib.sha256(out).hexdigest()
        configuration["config_sources_bytes"] = len(out)
    return configuration


def measure(command, *, cwd, phase, session_id, prompt, model=None, agent=None, timeout=180):
    """One turn in `session_id`: a session that must not exist (fresh) or must exist (resume)."""
    client = Client(command, cwd)
    diagnostics = Counter()
    failure = failure_detail = run = None
    before = after = None
    known = set()
    new_messages = []
    session = {}
    configuration = {}
    try:
        configuration = host_configuration(client)
        existing = session_info(client, session_id)
        if phase == "fresh" and existing is not None:
            failure = "session_already_exists"
        elif phase == "resume" and existing is None:
            failure = "session_not_found"
        elif existing is not None:
            before = totals(existing)
            known = {message["id"] for message in session_messages(client, session_id)}
        if failure is None:
            argv = ["run", "--standalone", "--format", "json", "--session", session_id]
            if model:
                argv += ["--model", model]
            if agent:
                argv += ["--agent", agent]
            run = run_turn(client, [*argv, prompt], timeout)
            if run["timed_out"]:
                failure = "timed_out"
            session = session_info(client, session_id)
            if session is None:
                session = {}
                failure = failure or "session_not_created"
            else:
                after = totals(session)
                new_messages = [m for m in session_messages(client, session_id) if m["id"] not in known]
            if run["exit_code"] != 0 and after is not None:
                pending = client.api("session.permission.list", sessionID=session_id)
                if pending and isinstance(pending["data"], list) and pending["data"]:
                    failure = "interactive_request_required"
    except ApiError as exc:
        failure, failure_detail = "api_error", exc.detail
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        failure = "launch_error"
        diagnostics[type(exc).__name__] += 1

    reduced = reduce_messages(new_messages, prompt)
    phase_usage = step_sum(reduced["steps"])
    session_delta = None
    if after is not None:
        zero = {"tokens": dict.fromkeys(TOKEN_FIELDS, 0), "cost_usd": 0}
        session_delta = delta(before or zero, after)
        if any(v is not None and v < 0 for v in (*session_delta["tokens"].values(), session_delta["cost_usd"])):
            diagnostics["regressing_session_totals"] += 1
    outcome, evidence = classify(failure, run or {"exit_code": None}, reduced, session, phase_usage, diagnostics)

    created = [s["time"]["created"] for s in reduced["steps"] if s["time"]["created"] is not None]
    completed = [s["time"]["completed"] for s in reduced["steps"] if s["time"]["completed"] is not None]
    models = []
    for step in reduced["steps"]:
        if step["model"] not in models:
            models.append(step["model"])
    configuration.update({"session_agent": session.get("agent"), "session_model": session.get("model"),
                          "location": session.get("location"), "step_models": models})
    return {
        "surface": SURFACE, "phase": PHASES[phase], "outcome": outcome,
        "completion_evidence": evidence, "failure_detail": failure_detail, "session_id": session_id,
        "requested": {"cwd": str(cwd), "model": model, "agent": agent},
        "configuration": configuration,
        "session_totals_before": before, "session_totals_after": after,
        "session_usage_delta": session_delta, "step_usage_sum": phase_usage,
        "assistant_steps": len(reduced["steps"]), "steps": reduced["steps"],
        "step_span": {"first_created": min(created) if created else None,
                      "last_completed": max(completed) if completed else None},
        "tool_items": reduced["tool_items"], "skills": reduced["skills"],
        "context_messages": reduced["context_messages"], "agent_messages": reduced["agent_messages"],
        "idle_messages": reduced["idle"], "user_messages": reduced["user_messages"],
        "prompt_echoed": reduced["prompt_echoed"] if after is not None else None,
        "other_message_types": reduced["other_message_types"],
        "run_stream": run["stream"] if run else None,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "process_exit_code": run["exit_code"] if run else None,
        "run_timed_out": run["timed_out"] if run else None,
        "observer_run_elapsed_s": run["elapsed_s"] if run else None,
        "stderr_bytes": run["stderr_bytes"] if run else None,
        "stderr_sha256": run["stderr_sha256"] if run else None,
        "diagnostics": dict(diagnostics),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=sorted(PHASES))
    parser.add_argument("--cwd", type=Path, required=True, help="explicit disposable task fixture")
    parser.add_argument("--session", help="exact session ID; required for resume, generated for fresh")
    parser.add_argument("--model", help="provider/model#variant; omitted means the host default")
    parser.add_argument("--agent")
    parser.add_argument("--timeout", type=float, default=180,
                        help=f"turn observation limit, 0 < seconds <= {MAX_TIMEOUT}")
    parser.add_argument("prompt", help="inline authorized test prompt; never a prompt filename")
    args = parser.parse_args(argv)
    if not args.cwd.is_dir() or not 0 < args.timeout <= MAX_TIMEOUT:
        parser.error(f"--cwd must exist and --timeout must be > 0 and <= {MAX_TIMEOUT}")
    if args.phase == "resume" and not args.session:
        parser.error("--phase resume needs the exact --session ID")
    if args.session is not None and not args.session.startswith("ses"):
        parser.error("--session must be an OpenCode session ID (starts with ses)")
    if not args.prompt.strip() or args.prompt.startswith("-"):
        parser.error("prompt must be non-empty and must not start with '-'")
    result = measure(["opencode"], cwd=args.cwd.resolve(), phase=args.phase,
                     session_id=args.session or "ses_" + uuid.uuid4().hex, prompt=args.prompt,
                     model=args.model, agent=args.agent, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["outcome"] == "completed_with_usage" else 1


if __name__ == "__main__":
    raise SystemExit(main())
