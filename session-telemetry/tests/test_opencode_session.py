"""OpenCode runner against a fixture CLI that speaks the published API shapes. Never the real CLI."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import opencode_session as oc

FAKE = Path(__file__).resolve().parent / "fake_opencode.py"
SID = "ses_fixture1"
PROMPT = "authorized prompt text"
M1 = {"id": "m1", "providerID": "p1"}
M2 = {"id": "m2", "providerID": "p2"}


def tk(inp=0, out=0, reasoning=0, read=0, write=0):
    return {"input": inp, "output": out, "reasoning": reasoning, "cache": {"read": read, "write": write}}


def flat(inp=0, out=0, reasoning=0, read=0, write=0):
    return {"input": inp, "output": out, "reasoning": reasoning, "cache_read": read, "cache_write": write}


def tool(tid, name="bash", status="completed", executed=True, time=None):
    return {"type": "tool", "id": tid, "name": name, "executed": executed,
            "state": {"status": status, "input": {"command": "SECRET_INPUT"},
                      "content": [{"type": "text", "text": "SECRET_OUTPUT"}]},
            "time": time or {"created": 1000, "ran": 1001, "completed": 1002}}


def text(said):
    return {"type": "text", "text": said}


def assistant(mid, tokens=None, cost=0.0, finish="stop", content=(), time=None, model=M1, **extra):
    message = {"id": mid, "type": "assistant", "agent": "build", "model": model,
               "time": time or {"created": 1000, "completed": 1001}, "finish": finish,
               "cost": cost, "content": list(content), **extra}
    if tokens is not None:
        message["tokens"] = tokens
    return message


def idle(mid="msg_idle", outcome="succeeded", **extra):
    return {"id": mid, "type": "idle", "time": {"created": 1010}, "outcome": outcome, **extra}


def info(sid, tokens, cost, **extra):
    return {"id": sid, "projectID": "prj_fixture", "agent": "build", "model": M1, "cost": cost,
            "tokens": tokens, "time": {"created": 1, "updated": 2}, "location": {"directory": "/fixture/work"},
            **extra}


class FixtureCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.state_path = Path(tmp.name) / "state.json"
        self.cwd = Path(tmp.name) / "work"
        self.cwd.mkdir()
        self.state = {"sessions": {}, "next_turn": {}}

    def seed(self, messages, tokens, cost, sid=SID, **extra):
        extra.setdefault("location", {"directory": os.path.realpath(self.cwd)})
        self.state["sessions"][sid] = {"info": info(sid, tokens, cost, **extra), "messages": messages}

    def turn(self, **scripted):
        self.state["next_turn"] = scripted

    def finish(self, *steps, idle_outcome="succeeded", **scripted):
        tail = [idle(outcome=idle_outcome)] if idle_outcome else []
        self.turn(messages=[*steps, *tail], **scripted)

    def measure(self, phase="fresh", sid=SID, prompt=PROMPT, timeout=30, command=None, **kwargs):
        self.state_path.write_text(json.dumps(self.state))
        command = command or [sys.executable, "-S", "-B", str(FAKE), str(self.state_path)]
        result = oc.measure(command, cwd=self.cwd, phase=phase, session_id=sid, prompt=prompt,
                            timeout=timeout, **kwargs)
        self.after = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}
        return result

    def runs(self):
        return [r["argv"] for r in self.after.get("runs", [])]

    def calls_of(self, operation):
        return [c for c in self.after["calls"] if c[:3] == ["api", "--standalone", operation]]


class TurnTests(FixtureCase):
    def test_fresh_turn_happy_path(self):
        a1 = assistant("msg_a1", tk(100, 20, 5, 60, 10), 0.25, "tool-calls",
                       [{"type": "reasoning", "text": "SECRET_REASONING"}, tool("tool_1")],
                       {"created": 1000, "firstToken": 1001, "streamed": 1002, "completed": 1003})
        a2 = assistant("msg_a2", tk(150, 30, 0, 80, 0), 0.5, "stop", [text("hel"), text("lo")],
                       {"created": 1004, "completed": 1006}, M2)
        stdout = [{"type": "step_start", "sessionID": SID}, {"type": "text", "part": {"sessionID": SID}},
                  {"type": "tool_use", "part": {"sessionID": "ses_other"}}, {"type": "text"},
                  {"type": "step_finish"}, {"no": "type"}, "plain progress line", ""]
        self.finish(a1, a2, add_tokens=tk(250, 50, 5, 140, 10), add_cost=0.75, stdout=stdout)
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual(r["phase"], "fresh_session_turn")
        self.assertEqual(r["surface"], "opencode_run_standalone")
        self.assertEqual(r["completion_evidence"], "idle_message")
        self.assertIsNone(r["session_totals_before"])
        self.assertEqual(r["session_totals_after"], {"tokens": flat(250, 50, 5, 140, 10), "cost_usd": 0.75})
        self.assertEqual(r["session_usage_delta"], r["session_totals_after"])
        self.assertEqual(r["step_usage_sum"], r["session_totals_after"])
        self.assertEqual(r["assistant_steps"], 2)
        self.assertEqual(r["steps"][0], {
            "id": "msg_a1", "agent": "build", "model": {"id": "m1", "providerID": "p1", "variant": None},
            "finish": "tool-calls", "tokens": flat(100, 20, 5, 60, 10), "cost_usd": 0.25,
            "time": {"created": 1000, "firstToken": 1001, "streamed": 1002, "completed": 1003},
            "error_type": None, "retry_attempt": None})
        self.assertEqual(r["steps"][1]["time"],
                         {"created": 1004, "firstToken": None, "streamed": None, "completed": 1006})
        self.assertEqual(r["step_span"], {"first_created": 1000, "last_completed": 1006})
        self.assertEqual(r["configuration"]["step_models"],
                         [{"id": "m1", "providerID": "p1", "variant": None},
                          {"id": "m2", "providerID": "p2", "variant": None}])
        self.assertEqual(r["agent_messages"], [{"id": "msg_a2", "text": "hello"}])
        config = b"config-sources: fixture\n"
        self.assertEqual(r["configuration"]["cli_version"], "opencode v0.0.0-fixture")
        self.assertEqual(r["configuration"]["paths"], {k: f"/fixture/{k}" for k in
                                                       ("config", "data", "db", "state", "cache")})
        self.assertEqual(r["configuration"]["config_sources_sha256"], hashlib.sha256(config).hexdigest())
        self.assertEqual(r["configuration"]["config_sources_bytes"], len(config))
        self.assertEqual(r["configuration"]["session_agent"], "build")
        self.assertEqual(r["configuration"]["location"], {"directory": os.path.realpath(self.cwd)})
        self.assertIs(r["configuration"]["location_is_cwd"], True)
        self.assertEqual(r["prompt_sha256"], hashlib.sha256(PROMPT.encode()).hexdigest())
        self.assertEqual(r["prompt_bytes"], len(PROMPT))
        self.assertIs(r["prompt_echoed"], True)
        self.assertEqual(r["user_messages"], 1)
        self.assertEqual(r["user_message_texts"], [{"id": "msg_user_000", "text_sha256": r["prompt_sha256"],
                                                    "text_bytes": len(PROMPT)}])
        self.assertEqual(r["idle_messages"], [{"id": "msg_idle", "outcome": "succeeded", "error_type": None}])
        printed = "".join((json.dumps(x) if isinstance(x, dict) else x) + "\n" for x in stdout)
        self.assertEqual(r["run_stream"], {
            "bytes": len(printed), "json_lines": 6, "other_lines": 1,
            "event_types": {"step_start": 1, "text": 2, "tool_use": 1, "step_finish": 1, "untyped": 1},
            "session_ids": [SID, "ses_other"]})
        self.assertEqual(r["process_exit_code"], 0)
        self.assertEqual(r["stderr_bytes"], len("fixture stderr\n"))
        self.assertEqual(r["stderr_sha256"], hashlib.sha256(b"fixture stderr\n").hexdigest())
        self.assertEqual(r["diagnostics"], {})
        self.assertEqual(r["requested"], {"cwd": str(self.cwd), "model": None, "agent": None})
        self.assertEqual(self.runs(), [["run", "--standalone", "--format", "json", "--session", SID, PROMPT]])
        self.assertFalse(any("--auto" in call for call in self.after["calls"]))
        self.assertEqual(self.calls_of("session.permission.list"), [])
        self.assertNotIn(PROMPT, json.dumps(r))

    def test_unattributed_session_usage_is_reported_not_added(self):
        step = assistant("msg_a1", tk(100, 20), 0.25)
        self.finish(step, add_tokens=tk(130, 25), add_cost=0.375)
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual(r["step_usage_sum"], {"tokens": flat(100, 20), "cost_usd": 0.25})
        self.assertEqual(r["session_usage_delta"], {"tokens": flat(130, 25), "cost_usd": 0.375})

    def test_resume_reports_only_the_new_turn(self):
        old = [{"id": "msg_u0", "type": "user", "time": {"created": 1}, "text": "earlier"},
               assistant("msg_old", tk(1000, 200), 1.0, content=[text("old"), tool("tool_old")]),
               {"id": "msg_skold", "type": "skill", "time": {}, "skill": "old-skill", "name": "Old", "text": "x"},
               idle("msg_idle_old")]
        self.seed(old, tk(1000, 200), 1.0)
        new = assistant("msg_new", tk(10, 2), 0.125, content=[text("new"), tool("tool_new")])
        skill = {"id": "msg_sknew", "type": "skill", "time": {}, "skill": "new-skill", "name": "New", "text": "x"}
        self.turn(messages=[skill, new, idle("msg_idle_new")], add_tokens=tk(10, 2), add_cost=0.125)
        r = self.measure("resume")
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual(r["phase"], "resumed_session_turn")
        self.assertEqual(r["session_totals_before"], {"tokens": flat(1000, 200), "cost_usd": 1.0})
        self.assertEqual(r["session_totals_after"], {"tokens": flat(1010, 202), "cost_usd": 1.125})
        self.assertEqual(r["session_usage_delta"], {"tokens": flat(10, 2), "cost_usd": 0.125})
        self.assertEqual(r["step_usage_sum"], r["session_usage_delta"])
        self.assertEqual([s["id"] for s in r["steps"]], ["msg_new"])
        self.assertEqual([m["id"] for m in r["agent_messages"]], ["msg_new"])
        self.assertEqual([t["id"] for t in r["tool_items"]], ["tool_new"])
        self.assertEqual([s["id"] for s in r["skills"]], ["msg_sknew"])
        self.assertEqual([i["id"] for i in r["idle_messages"]], ["msg_idle_new"])
        self.assertEqual(r["user_messages"], 1)
        self.assertEqual(len(self.calls_of("session.message.list")), 2)

    def test_model_and_agent_reach_the_run_argv(self):
        self.finish(assistant("msg_a1", tk(1, 1)), add_tokens=tk(1, 1))
        r = self.measure(model="anthropic/claude#high", agent="plan")
        self.assertEqual(self.runs(), [["run", "--standalone", "--format", "json", "--session", SID,
                                        "--model", "anthropic/claude#high", "--agent", "plan", PROMPT]])
        self.assertEqual(r["requested"]["model"], "anthropic/claude#high")
        self.assertEqual(r["requested"]["agent"], "plan")
        self.assertEqual(r["configuration"]["session_model"],
                         {"id": "claude", "providerID": "anthropic", "variant": "high"})
        self.assertEqual(r["configuration"]["session_agent"], "plan")

    def test_fresh_with_existing_session_never_runs(self):
        self.seed([], tk(5, 5), 0.5)
        self.finish(assistant("msg_a1", tk(1, 1)), add_tokens=tk(1, 1))
        r = self.measure("fresh")
        self.assertEqual(r["outcome"], "session_already_exists")
        self.assertEqual(self.runs(), [])
        self.assertIsNone(r["run_stream"])
        self.assertIsNone(r["process_exit_code"])
        self.assertIsNone(r["session_usage_delta"])
        self.assertIsNone(r["prompt_echoed"])

    def test_resume_with_unknown_session_never_runs(self):
        self.finish(assistant("msg_a1", tk(1, 1)), add_tokens=tk(1, 1))
        r = self.measure("resume")
        self.assertEqual(r["outcome"], "session_not_found")
        self.assertEqual(self.runs(), [])
        self.assertEqual(self.after["sessions"], {})

    def test_every_child_gets_the_fixture_as_cwd_and_pwd(self):
        self.finish(assistant("msg_a1", tk(1, 1)), add_tokens=tk(1, 1))
        with mock.patch.dict(os.environ, {"PWD": "/somewhere/else"}):
            r = self.measure()
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual(len(self.after["dirs"]), len(self.after["calls"]))
        for seen in self.after["dirs"]:
            self.assertEqual(seen, {"pwd": str(self.cwd), "cwd": os.path.realpath(self.cwd)})

    def test_session_located_outside_cwd_is_invalid_telemetry(self):
        self.finish(assistant("msg_a1", tk(5, 2), 0.25), add_tokens=tk(5, 2), add_cost=0.25,
                    set_info={"location": {"directory": "/somewhere/else"}})
        r = self.measure()
        self.assertEqual(r["outcome"], "invalid_telemetry")
        self.assertEqual(r["diagnostics"], {"location_not_cwd": 1})
        self.assertIs(r["configuration"]["location_is_cwd"], False)
        self.assertEqual(r["step_usage_sum"], {"tokens": flat(5, 2), "cost_usd": 0.25})

    def test_session_without_location_is_not_judged(self):
        self.finish(assistant("msg_a1", tk(1, 1)), add_tokens=tk(1, 1), set_info={"location": None})
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertIsNone(r["configuration"]["location_is_cwd"])

    def test_run_that_creates_no_session(self):
        self.turn(skip_create=True)
        r = self.measure()
        self.assertEqual(r["outcome"], "session_not_created")
        self.assertIsNone(r["session_totals_after"])
        self.assertIsNone(r["prompt_echoed"])


class PrivacyTests(FixtureCase):
    def test_only_metadata_survives_reduction(self):
        content = [{"type": "reasoning", "text": "SECRET_REASONING"}, text("visible"),
                   tool("tool_ok"), tool("tool_run", "read", "running", False, {"created": 5}),
                   tool("tool_err", "edit", "error", True)]
        skill = {"id": "msg_sk", "type": "skill", "time": {}, "skill": "skill-id", "name": "Skill Name",
                 "text": "SECRET_SKILL_TEXT"}
        body = "SECRET_SYSTEM_TEXT héllo"
        system = {"id": "msg_sys", "type": "system", "time": {}, "text": body, "description": "AGENTS.md"}
        synthetic = {"id": "msg_syn", "type": "synthetic", "time": {}, "text": "SECRET_SYNTHETIC"}
        switched = {"id": "msg_sw", "type": "model-switched", "time": {}, "to": "SECRET_MODEL"}
        err = idle("msg_idle2", "failed", error={"type": "ProviderError", "message": "SECRET_ERROR"})
        self.turn(messages=[system, synthetic, skill, switched,
                            assistant("msg_a1", tk(3, 3), content=content,
                                      error={"type": "ApiError", "message": "SECRET_ERROR"},
                                      retry={"attempt": 2, "at": 9, "error": {"message": "SECRET_ERROR"}}),
                            err], add_tokens=tk(3, 3), exit_code=1)
        r = self.measure()
        self.assertEqual(r["tool_items"], [
            {"id": "tool_ok", "message_id": "msg_a1", "name": "bash", "status": "completed", "executed": True,
             "time": {"created": 1000, "ran": 1001, "completed": 1002}},
            {"id": "tool_run", "message_id": "msg_a1", "name": "read", "status": "running", "executed": False,
             "time": {"created": 5, "ran": None, "completed": None}},
            {"id": "tool_err", "message_id": "msg_a1", "name": "edit", "status": "error", "executed": True,
             "time": {"created": 1000, "ran": 1001, "completed": 1002}}])
        self.assertEqual(r["skills"], [{"id": "msg_sk", "skill": "skill-id", "name": "Skill Name"}])
        self.assertEqual(r["context_messages"], [
            {"id": "msg_sys", "type": "system", "description": "AGENTS.md",
             "text_sha256": hashlib.sha256(body.encode()).hexdigest(), "text_bytes": len(body) + 1},
            {"id": "msg_syn", "type": "synthetic", "description": None,
             "text_sha256": hashlib.sha256(b"SECRET_SYNTHETIC").hexdigest(), "text_bytes": 16}])
        self.assertEqual(r["other_message_types"], {"model-switched": 1})
        self.assertEqual(r["steps"][0]["error_type"], "ApiError")
        self.assertEqual(r["steps"][0]["retry_attempt"], 2)
        self.assertEqual(r["idle_messages"][0]["error_type"], "ProviderError")
        self.assertEqual(r["agent_messages"], [{"id": "msg_a1", "text": "visible"}])
        self.assertNotIn("SECRET", json.dumps(r, ensure_ascii=False))
        self.assertNotIn(PROMPT, json.dumps(r))


class UsageClassTests(FixtureCase):
    def test_missing_required_token_fields_are_partial_not_zero(self):
        self.finish(assistant("msg_a1", {"input": 10}), add_tokens=tk(10, 0))
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_usage_partial")
        self.assertEqual(r["steps"][0]["tokens"], {"input": 10, "output": None, "reasoning": None,
                                                    "cache_read": None, "cache_write": None})
        self.assertIsNone(r["step_usage_sum"]["tokens"]["output"])

    def test_missing_optional_token_fields_still_counts(self):
        self.finish(assistant("msg_a1", {"input": 10, "output": 4}), add_tokens=tk(10, 4))
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertIsNone(r["step_usage_sum"]["tokens"]["reasoning"])
        self.assertEqual(r["step_usage_sum"]["tokens"]["input"], 10)

    def test_step_without_tokens_object_is_partial(self):
        self.finish(assistant("msg_a1"))
        self.assertEqual(self.measure()["outcome"], "completed_usage_partial")

    def test_all_zero_usage(self):
        self.finish(assistant("msg_a1", tk()))
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_zero_usage")
        self.assertEqual(r["step_usage_sum"]["tokens"], flat())

    def test_succeeded_without_assistant_message_is_unavailable(self):
        self.finish()
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_usage_unavailable")
        self.assertIsNone(r["step_usage_sum"])
        self.assertEqual(r["assistant_steps"], 0)

    def test_step_missing_cost_leaves_cost_unknown(self):
        message = assistant("msg_a1", tk(1, 1))
        del message["cost"]
        self.finish(message, add_tokens=tk(1, 1))
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertIsNone(r["step_usage_sum"]["cost_usd"])
        self.assertEqual(r["session_usage_delta"]["cost_usd"], 0)


class CompletionTests(FixtureCase):
    def test_idle_failed_and_interrupted_keep_observed_usage(self):
        for outcome, code in (("failed", 1), ("interrupted", 0)):
            with self.subTest(outcome=outcome):
                self.state["sessions"] = {}
                self.finish(assistant("msg_a1", tk(7, 3), 0.5, "error"), idle_outcome=outcome,
                            add_tokens=tk(7, 3), add_cost=0.5, exit_code=code)
                r = self.measure()
                self.assertEqual(r["outcome"], outcome)
                self.assertEqual(r["completion_evidence"], "idle_message")
                self.assertEqual(r["step_usage_sum"], {"tokens": flat(7, 3), "cost_usd": 0.5})
                self.assertEqual(r["session_usage_delta"], {"tokens": flat(7, 3), "cost_usd": 0.5})

    def test_idle_message_outranks_session_outcome(self):
        self.finish(assistant("msg_a1", tk(1, 1)), idle_outcome="failed", add_tokens=tk(1, 1),
                    set_info={"outcome": "succeeded"})
        r = self.measure()
        self.assertEqual((r["outcome"], r["completion_evidence"]), ("failed", "idle_message"))

    def test_falls_back_to_session_outcome(self):
        self.finish(assistant("msg_a1", tk(1, 1), finish="tool-calls"), idle_outcome=None,
                    add_tokens=tk(1, 1), set_info={"outcome": "succeeded"})
        r = self.measure()
        self.assertEqual((r["outcome"], r["completion_evidence"]), ("completed_with_usage", "session_outcome"))
        self.assertEqual(r["idle_messages"], [])

    def test_session_outcome_failed(self):
        self.finish(assistant("msg_a1", tk(1, 1)), idle_outcome=None, add_tokens=tk(1, 1),
                    set_info={"outcome": "failed"}, exit_code=1)
        r = self.measure()
        self.assertEqual((r["outcome"], r["completion_evidence"]), ("failed", "session_outcome"))

    def test_falls_back_to_final_step_finish(self):
        self.finish(assistant("msg_a1", tk(1, 1), finish="stop"), idle_outcome=None, add_tokens=tk(1, 1))
        r = self.measure()
        self.assertEqual((r["outcome"], r["completion_evidence"]), ("completed_with_usage", "final_step_finish"))

    def test_final_step_finish_needs_a_clean_exit_and_stop(self):
        cases = {"tool-calls": 0, "stop": 3}
        for finish, code in cases.items():
            with self.subTest(finish=finish, code=code):
                self.state["sessions"] = {}
                self.finish(assistant("msg_a1", tk(1, 1), finish=finish), idle_outcome=None,
                            add_tokens=tk(1, 1), exit_code=code)
                r = self.measure()
                if code == 0:
                    self.assertEqual((r["outcome"], r["completion_evidence"]), ("incomplete", None))
                else:
                    self.assertEqual(r["outcome"], "process_failed")

    def test_no_evidence_at_all_is_incomplete(self):
        self.finish(idle_outcome=None)
        r = self.measure()
        self.assertEqual((r["outcome"], r["completion_evidence"]), ("incomplete", None))

    def test_session_outcome_not_terminal_is_incomplete(self):
        self.finish(assistant("msg_a1", tk(1, 1)), idle_outcome=None, add_tokens=tk(1, 1),
                    set_info={"outcome": "running"})
        r = self.measure()
        self.assertEqual((r["outcome"], r["completion_evidence"]), ("incomplete", "session_outcome"))

    def test_nonzero_exit_with_succeeded_session_is_process_failed(self):
        self.finish(assistant("msg_a1", tk(4, 2)), add_tokens=tk(4, 2), exit_code=2)
        r = self.measure()
        self.assertEqual(r["outcome"], "process_failed")
        self.assertEqual(r["process_exit_code"], 2)
        self.assertEqual(r["step_usage_sum"]["tokens"], flat(4, 2))
        self.assertEqual(len(self.calls_of("session.permission.list")), 1)

    def test_pending_permission_request_is_interactive(self):
        self.state["permissions"] = [{"id": "per_1", "permission": "bash"}]
        self.finish(assistant("msg_a1", tk(4, 2), finish="tool-calls"), idle_outcome=None,
                    add_tokens=tk(4, 2), exit_code=1)
        r = self.measure()
        self.assertEqual(r["outcome"], "interactive_request_required")
        self.assertEqual(r["step_usage_sum"]["tokens"], flat(4, 2))
        self.assertNotIn("bash", json.dumps(r))

    def test_decreasing_session_totals_are_invalid_telemetry(self):
        self.seed([], tk(500, 100), 2.0)
        self.finish(assistant("msg_a1", tk(10, 2), 0.25), set_info={"tokens": tk(100, 10), "cost": 0.5})
        r = self.measure("resume")
        self.assertEqual(r["outcome"], "invalid_telemetry")
        self.assertEqual(r["diagnostics"], {"regressing_session_totals": 1})
        self.assertEqual(r["session_usage_delta"]["tokens"]["input"], -400)
        self.assertEqual(r["session_usage_delta"]["cost_usd"], -1.5)
        self.assertEqual(r["step_usage_sum"]["tokens"], flat(10, 2))


class TimeoutTests(FixtureCase):
    def test_timeout_kills_reaps_and_keeps_recorded_usage(self):
        self.finish(assistant("msg_a1", tk(9, 3), 0.5, "tool-calls"), idle_outcome=None,
                    add_tokens=tk(9, 3), add_cost=0.5, sleep=60)
        r = self.measure(timeout=1.0)
        self.assertEqual(r["outcome"], "timed_out")
        self.assertTrue(r["process_exit_code"] < 0)
        self.assertLess(r["observer_run_elapsed_s"], 30)
        pid = self.after["runs"][0]["pid"]
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)
        self.assertEqual(r["step_usage_sum"], {"tokens": flat(9, 3), "cost_usd": 0.5})
        self.assertEqual(r["session_usage_delta"], {"tokens": flat(9, 3), "cost_usd": 0.5})
        self.assertEqual(r["run_stream"]["bytes"], 0)

    def test_timeout_signal_is_sigterm(self):
        self.finish(sleep=60)
        r = self.measure(timeout=1.0)
        self.assertEqual(r["outcome"], "timed_out")
        self.assertEqual(r["process_exit_code"], -signal.SIGTERM)


class ApiFailureTests(FixtureCase):
    def override(self, operation, stdout, code=0):
        self.state.setdefault("api_override", {})[operation] = {"stdout": stdout, "code": code}

    def test_multi_page_listing_is_followed_to_the_end(self):
        steps = [assistant(f"msg_a{n}", tk(n, 1), finish="tool-calls") for n in (1, 2, 3)]
        self.finish(*steps, add_tokens=tk(6, 3))
        self.state["page_size"] = 2
        r = self.measure()
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual([s["id"] for s in r["steps"]], ["msg_a1", "msg_a2", "msg_a3"])
        self.assertEqual(r["step_usage_sum"]["tokens"]["input"], 6)
        pages = self.calls_of("session.message.list")
        self.assertEqual(len(pages), 3)
        self.assertIn("order=asc", pages[0])
        self.assertIn("cursor=2", pages[1])
        self.assertIn("cursor=4", pages[2])
        self.assertNotIn("order=asc", pages[1])

    def test_unbounded_paging_stops(self):
        self.finish(assistant("msg_a1", tk(1, 1)), add_tokens=tk(1, 1))
        self.state["endless"] = True
        r = self.measure()
        self.assertEqual(r["outcome"], "api_error")
        self.assertEqual(r["failure_detail"], {"operation": "session.message.list",
                                               "reason": "page_limit_exceeded"})
        self.assertEqual(len(self.calls_of("session.message.list")), oc.MAX_PAGES)

    def test_non_json_reply_is_api_error_after_the_run(self):
        self.finish(assistant("msg_a1", tk(1, 1)), add_tokens=tk(1, 1))
        self.override("session.message.list", "this is not json")
        r = self.measure()
        self.assertEqual(r["outcome"], "api_error")
        self.assertEqual(r["failure_detail"], {"operation": "session.message.list", "reason": "not_json"})
        self.assertEqual(len(self.runs()), 1)
        self.assertNotIn("this is not json", json.dumps(r))

    def test_reply_without_data_is_api_error(self):
        self.override("session.get", json.dumps({"other": 1}))
        r = self.measure()
        self.assertEqual(r["outcome"], "api_error")
        self.assertEqual(r["failure_detail"], {"operation": "session.get", "reason": "malformed"})
        self.assertEqual(self.runs(), [])

    def test_reply_with_wrong_data_type_is_api_error(self):
        self.override("session.get", json.dumps({"data": []}))
        r = self.measure()
        self.assertEqual((r["outcome"], r["failure_detail"]["reason"]), ("api_error", "malformed"))

    def test_server_error_tag_is_reported(self):
        self.override("session.get", json.dumps({"_tag": "Boom", "secret": "SECRET"}), code=1)
        r = self.measure()
        self.assertEqual(r["failure_detail"], {"operation": "session.get", "reason": "Boom"})
        self.assertNotIn("SECRET", json.dumps(r))

    def test_nonzero_exit_with_data_is_still_an_error(self):
        self.override("session.get", json.dumps({"data": {}}), code=1)
        r = self.measure()
        self.assertEqual(r["outcome"], "api_error")

    def test_missing_executable_is_launch_error(self):
        r = self.measure(command=["/nonexistent/opencode"])
        self.assertEqual(r["outcome"], "launch_error")
        self.assertEqual(r["diagnostics"], {"FileNotFoundError": 1})
        self.assertIsNone(r["run_stream"])
        self.assertEqual(r["steps"], [])


class HelperTests(unittest.TestCase):
    def test_tokens_flatten_and_never_invent_zero(self):
        self.assertEqual(oc.tokens(tk(1, 2, 3, 4, 5)), flat(1, 2, 3, 4, 5))
        self.assertEqual(oc.tokens({"input": 1}), {"input": 1, "output": None, "reasoning": None,
                                                    "cache_read": None, "cache_write": None})
        for bad in (None, "x", [], {"input": True, "output": -1, "cache": "x"}):
            self.assertEqual(oc.tokens(bad), dict.fromkeys(oc.TOKEN_FIELDS))

    def test_step_sum(self):
        self.assertIsNone(oc.step_sum([]))
        steps = [{"tokens": flat(1, 2, 3, 4, 5), "cost_usd": 0.5},
                 {"tokens": {**flat(10, 20, 30, 40, 50), "reasoning": None}, "cost_usd": 0.25}]
        got = oc.step_sum(steps)
        self.assertEqual(got["tokens"], {"input": 11, "output": 22, "reasoning": None,
                                         "cache_read": 44, "cache_write": 55})
        self.assertEqual(got["cost_usd"], 0.75)
        steps[1]["cost_usd"] = None
        self.assertIsNone(oc.step_sum(steps)["cost_usd"])

    def test_delta_keeps_decreases_and_unknowns(self):
        before = {"tokens": {**flat(10, 10, 10, 10, 10), "output": None}, "cost_usd": 1.0}
        after = {"tokens": flat(15, 5, 10, 11, 10), "cost_usd": None}
        got = oc.delta(before, after)
        self.assertEqual(got["tokens"], {"input": 5, "output": None, "reasoning": 0,
                                         "cache_read": 1, "cache_write": 0})
        self.assertIsNone(got["cost_usd"])
        self.assertEqual(oc.delta(after, before)["tokens"]["input"], -5)

    def test_reduce_messages_shapes(self):
        multi = assistant("msg_a", tk(1, 1), content=[text("a"), {"type": "text", "text": 5}, "junk", text("b"),
                                                       {"type": "tool", "id": "t"}])
        reduced = oc.reduce_messages([
            multi, {"id": "msg_u", "type": "user", "text": "hi"}, {"id": "msg_x"},
            {"id": "msg_y", "type": 7}, {"id": "msg_z", "type": "model-switched"},
            {"id": "msg_s", "type": "system"}, assistant("msg_b", content="notalist")], "hi")
        self.assertEqual(reduced["agent_messages"], [{"id": "msg_a", "text": "ab"}])
        self.assertEqual(reduced["tool_items"], [{"id": "t", "message_id": "msg_a", "name": None, "status": None,
                                                   "executed": None,
                                                   "time": {"created": None, "ran": None, "completed": None}}])
        self.assertTrue(reduced["prompt_echoed"])
        self.assertEqual(reduced["other_message_types"], {"untyped": 2, "model-switched": 1})
        self.assertEqual(reduced["context_messages"][0]["text_bytes"], 0)
        self.assertEqual(len(reduced["steps"]), 2)

    def test_reduce_messages_prompt_not_echoed(self):
        reduced = oc.reduce_messages([{"id": "m", "type": "user", "text": "other"}, {"id": "n", "type": "user"}], "hi")
        self.assertFalse(reduced["prompt_echoed"])
        self.assertEqual(reduced["user_messages"], 2)
        self.assertEqual(reduced["user_message_texts"], [
            {"id": "m", "text_sha256": hashlib.sha256(b"other").hexdigest(), "text_bytes": 5},
            {"id": "n", "text_sha256": hashlib.sha256(b"").hexdigest(), "text_bytes": 0}])

    def test_reduce_messages_prompt_echo_ignores_outer_whitespace(self):
        reduced = oc.reduce_messages([{"id": "m", "type": "user", "text": "\nhi \n"}], "hi")
        self.assertTrue(reduced["prompt_echoed"])

    def test_classify(self):
        def reduced(idle_outcomes=(), finishes=()):
            return {"idle": [{"outcome": o} for o in idle_outcomes], "steps": [{"finish": f} for f in finishes]}
        used = {"tokens": flat(1, 1)}
        ok = {"exit_code": 0}
        self.assertEqual(oc.classify("timed_out", {"exit_code": None}, reduced(), {}, None, {}), ("timed_out", None))
        self.assertEqual(oc.classify(None, ok, reduced(["failed"]), {}, used, {}), ("failed", "idle_message"))
        self.assertEqual(oc.classify(None, ok, reduced(["failed", "succeeded"]), {}, used, {}),
                         ("completed_with_usage", "idle_message"))
        self.assertEqual(oc.classify(None, {"exit_code": 2}, reduced(["succeeded"]), {}, used, {}),
                         ("process_failed", "idle_message"))
        self.assertEqual(oc.classify(None, {"exit_code": 2}, reduced(["failed"]), {}, used, {}),
                         ("failed", "idle_message"))
        self.assertEqual(oc.classify(None, ok, reduced(), {}, used, {}), ("incomplete", None))
        self.assertEqual(oc.classify(None, ok, reduced(["succeeded"]), {}, used, {"x": 1}),
                         ("invalid_telemetry", "idle_message"))
        self.assertEqual(oc.classify(None, ok, reduced(["succeeded"]), {}, None, {}),
                         ("completed_usage_unavailable", "idle_message"))
        self.assertEqual(oc.classify(None, ok, reduced(["succeeded"]), {}, {"tokens": flat(0, 0)}, {}),
                         ("completed_zero_usage", "idle_message"))
        self.assertEqual(oc.classify(None, ok, reduced(["succeeded"]), {}, {"tokens": flat(None, 0)}, {}),
                         ("completed_usage_partial", "idle_message"))
        self.assertEqual(oc.classify(None, ok, reduced(["succeeded"]), {}, {"tokens": flat(0, 0, 0, 3)}, {}),
                         ("completed_with_usage", "idle_message"))
        self.assertEqual(oc.classify(None, ok, reduced([], ["stop"]), {}, used, {}),
                         ("completed_with_usage", "final_step_finish"))
        self.assertEqual(oc.classify(None, ok, reduced(), {"outcome": "interrupted"}, used, {}),
                         ("interrupted", "session_outcome"))


class MainTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cwd = tmp.name

    def rejects(self, *argv):
        with mock.patch.object(oc, "measure", side_effect=AssertionError("must not measure")), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit) as caught:
                oc.main(list(argv))
        self.assertEqual(caught.exception.code, 2)
        return err.getvalue()

    def test_argument_validation(self):
        base = ["--cwd", self.cwd]
        self.rejects("--phase", "resume", *base, "go")
        self.rejects("--phase", "fresh", *base, "--session", "abc_1", "go")
        self.rejects("--phase", "resume", *base, "--session", "xses_1", "go")
        self.rejects("--phase", "fresh", *base, "--", "-dash")
        self.rejects("--phase", "fresh", *base, "   ")
        self.rejects("--phase", "fresh", "--cwd", self.cwd + "/missing", "go")
        for bad in ("0", "-1", "601", "nan"):
            with self.subTest(timeout=bad):
                self.rejects("--phase", "fresh", *base, f"--timeout={bad}", "go")
        self.rejects("--phase", "other", *base, "go")
        self.rejects(*base, "go")

    def test_validation_messages_name_the_problem(self):
        self.assertIn("resume needs the exact --session", self.rejects("--phase", "resume", "--cwd", self.cwd, "go"))

    def run_main(self, outcome, *argv):
        out = io.StringIO()
        with mock.patch.object(oc, "measure", return_value={"outcome": outcome}) as measure, \
                contextlib.redirect_stdout(out):
            code = oc.main(list(argv))
        return code, json.loads(out.getvalue()), measure.call_args

    def test_main_runs_with_the_real_command_and_exit_code(self):
        code, printed, call = self.run_main("completed_with_usage", "--phase", "fresh", "--cwd", self.cwd,
                                            "--model", "a/b", "--agent", "plan", "--timeout", "12.5", "go")
        self.assertEqual((code, printed), (0, {"outcome": "completed_with_usage"}))
        self.assertEqual(call.args, (["opencode"],))
        self.assertEqual(call.kwargs["cwd"], Path(self.cwd).resolve())
        self.assertEqual(call.kwargs["phase"], "fresh")
        self.assertTrue(call.kwargs["session_id"].startswith("ses_"))
        self.assertEqual((call.kwargs["model"], call.kwargs["agent"], call.kwargs["timeout"], call.kwargs["prompt"]),
                         ("a/b", "plan", 12.5, "go"))

    def test_main_nonzero_unless_completed_with_usage(self):
        code, _, call = self.run_main("completed_zero_usage", "--phase", "resume", "--cwd", self.cwd,
                                      "--session", "ses_given", "go")
        self.assertEqual(code, 1)
        self.assertEqual(call.kwargs["session_id"], "ses_given")


if __name__ == "__main__":
    unittest.main()
