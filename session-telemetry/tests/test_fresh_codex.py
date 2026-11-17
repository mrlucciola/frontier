"""Schema-shaped fresh streams only. No authentication or session-log reads."""
import copy
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fresh_codex as fc


CONFIG = {
    "thread": {"id": "fresh", "ephemeral": True, "parentThreadId": None,
               "cliVersion": "fixture", "source": "appServer"},
    "model": "fixture-model", "modelProvider": "openai", "reasoningEffort": "high",
    "approvalPolicy": "on-request", "sandbox": {"type": "workspaceWrite"},
    "instructionSources": ["/fixture/AGENTS.md"],
}


def usage(inp=100, cached=60, out=20, reasoning=5):
    return {"inputTokens": inp, "cachedInputTokens": cached, "outputTokens": out,
            "reasoningOutputTokens": reasoning, "totalTokens": inp + out}


def event(method, **params):
    return {"method": method, "params": {"threadId": "fresh", "turnId": "turn", **params}}


def snapshot(total=None):
    total = usage() if total is None else total
    return event("thread/tokenUsage/updated", tokenUsage={"total": total, "last": total})


def terminal(status="completed", items=None):
    return event("turn/completed", turn={"id": "turn", "status": status,
                 "startedAt": 1000, "completedAt": 1002, "durationMs": 1800,
                 "items": items or [], "error": None})


def gone(pid, wait=5):
    """True once `pid` no longer exists; an orphan's reaping by init can lag its death."""
    deadline = time.monotonic() + wait
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        if time.monotonic() > deadline:
            return False
        time.sleep(0.05)


def observer(*events):
    o = fc.Observation()
    o.configure(copy.deepcopy(CONFIG))
    o.turn_id = "turn"
    for message in events:
        o.feed(message)
    return o.result()


class ObservationTests(unittest.TestCase):
    def test_cumulative_snapshot_not_sum_or_call_count(self):
        first = snapshot(usage(40, 20, 10, 1))
        final = snapshot()
        r = observer(first, first, final, final, terminal(), terminal())
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual(r["usage_snapshot"]["total"]["inputTokens"], 100)
        self.assertEqual(r["usage_snapshot"]["total"]["cachedInputTokens"], 60)
        self.assertEqual(r["usage_snapshot"]["total"]["outputTokens"], 20)
        self.assertEqual(r["usage_snapshot"]["total"]["reasoningOutputTokens"], 5)
        self.assertIsNone(r["usage_snapshot"]["total"]["cacheWriteInputTokens"])
        self.assertIsNone(r["model_calls"])
        self.assertIsNone(r["executed_model"])
        self.assertEqual(r["duplicate_snapshots_or_items"], 3)
        self.assertEqual(r["server_turn"]["durationMs"], 1800)

    def test_no_usage_zero_and_partial_are_distinct(self):
        self.assertEqual(observer(terminal())["outcome"], "completed_usage_unavailable")
        self.assertIsNone(observer(terminal())["usage_snapshot"])
        zero = snapshot(usage(0, 0, 0, 0))
        self.assertEqual(observer(zero, terminal())["outcome"], "completed_zero_usage")
        partial = usage()
        del partial["outputTokens"]
        r = observer(snapshot(partial), terminal())
        self.assertEqual(r["outcome"], "completed_usage_partial")
        self.assertIsNone(r["usage_snapshot"]["total"]["outputTokens"])

    def test_failed_or_interrupted_keeps_usage_never_free_success(self):
        for status in ("failed", "interrupted"):
            for u in (usage(), usage(0, 0, 0, 0)):
                r = observer(snapshot(u), terminal(status))
                self.assertEqual(r["outcome"], status)
                self.assertEqual(r["usage_snapshot"]["total"]["inputTokens"], u["inputTokens"])

    def test_foreign_thread_or_turn_does_not_contaminate(self):
        r = observer(event("thread/tokenUsage/updated", threadId="other", tokenUsage={"total": usage(999)}),
                     event("turn/completed", turnId="other", turn={"id": "other", "status": "failed"}),
                     snapshot(), terminal())
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual(r["usage_snapshot"]["total"]["inputTokens"], 100)

    def test_invalid_regressing_or_conflicting_evidence_cannot_qualify(self):
        cases = [
            [snapshot(), snapshot(usage(90)), terminal()],
            [snapshot(usage(cached=101)), terminal()],
            [snapshot(usage(reasoning=21)), terminal()],
            [snapshot({**usage(), "totalTokens": True}), terminal()],
            [snapshot(), terminal(), terminal("failed")],
            [event("thread/tokenUsage/updated", tokenUsage=None), terminal()],
            [snapshot(), event("turn/completed", turn={"id": "turn", "status": "completed", "error": "bad shape"})],
            [snapshot(), event("turn/completed", turn={"id": "turn", "status": "completed", "durationMs": -1})],
        ]
        for events in cases:
            with self.subTest(events=events):
                r = observer(*events)
                self.assertIn(r["outcome"], ("invalid_telemetry", "completed_usage_partial"))

    def test_item_dedupe_retry_semantics_and_reroute(self):
        tool = {"id": "c1", "type": "commandExecution", "status": "completed",
                "durationMs": 50, "command": "secret command", "aggregatedOutput": "private output"}
        answer = {"id": "a1", "type": "agentMessage", "text": "Answer", "phase": "final_answer"}
        retry = event("error", willRetry=True, error={"message": "not retained"})
        route = event("model/rerouted", fromModel="a", toModel="b", reason="capacity")
        r = observer(event("item/completed", item=tool), event("item/completed", item=answer),
                     retry, retry, route, route, snapshot(), terminal(items=[tool, answer]))
        self.assertEqual(r["outcome"], "completed_with_usage")
        self.assertEqual(len(r["tool_items"]), 1)
        self.assertEqual(len(r["agent_messages"]), 1)
        self.assertEqual(r["retry_notice_receipts"], 2)  # receipts lack deduplication identity
        self.assertEqual(len(r["model_reroutes"]), 1)
        self.assertNotIn("secret command", json.dumps(r))
        self.assertNotIn("private output", json.dumps(r))


# Real local pipe transport fixture. It verifies the outbound protocol and
# ephemeral/no-policy-override boundary, then emits controlled responses. It
# never invokes Codex, reads transcripts, or requires network/authentication.
SERVER = r'''
import json, subprocess, sys, time
scenario = sys.argv[1]
config = json.loads(sys.argv[2])
events = json.loads(sys.argv[3])
def read():
    return json.loads(sys.stdin.readline())
def emit(value):
    print(json.dumps(value), flush=True)
assert read()['method'] == 'initialize'
emit({'id':0, 'result':{'userAgent':'fixture'}})
assert read()['method'] == 'initialized'
start = read()
assert start['method'] == 'thread/start'
assert set(start['params']) == {'cwd','model','ephemeral','config'}
assert start['params']['ephemeral'] is True
assert start['params']['config'] == {'model_reasoning_effort':'high'}
if scenario == 'rpc_error':
    emit({'id':1, 'error':{'code':-1, 'message':'not retained'}})
    sys.exit(0)
emit({'id':1, 'result':config})
request = read()
assert request['method'] == 'turn/start'
assert request['params']['threadId'] == 'fresh'
assert request['params']['input'] == [{'type':'text','text':'test prompt'}]
if scenario == 'timeout':
    emit({'id':2, 'result':{'turn':{'id':'turn'}}})
    stop = read()
    assert stop['method'] == 'turn/interrupt'
    sys.exit(0)
if scenario == 'stuck_tool':
    # A tool command still running while the server ignores shutdown.
    emit({'id':2, 'result':{'turn':{'id':'turn'}}})
    tool = subprocess.Popen(['sleep', '60'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    open('tool.pid', 'w').write(str(tool.pid))
    while True:
        time.sleep(1)
if scenario == 'early':
    for e in events:
        emit(e)
emit({'id':2, 'result':{'turn':{'id':'turn'}}})
if scenario == 'duplicate_rpc':
    emit({'id':1, 'result':config})
if scenario == 'interactive':
    emit({'id':'approval', 'method':'item/commandExecution/requestApproval',
          'params':{'threadId':'fresh', 'turnId':'turn'}})
elif scenario == 'malformed':
    print('not JSON', flush=True)
elif scenario == 'truncated':
    sys.stdout.write('{"method":'); sys.stdout.flush()
    sys.exit(0)
elif scenario != 'early':
    for i,e in enumerate(events):
        if scenario == 'late' and i == 1:
            time.sleep(0.05)
        emit(e)
if scenario == 'nonzero':
    sys.exit(2)
# Drain until EOF; the runner must close its own input on terminal/failure.
for line in sys.stdin:
    assert json.loads(line)['method'] == 'turn/interrupt'
'''


class TransportTests(unittest.TestCase):
    def run_fixture(self, scenario="normal", events=None, config=None, timeout=3):
        command = [sys.executable, "-u", "-c", SERVER, scenario,
                   json.dumps(CONFIG if config is None else config),
                   json.dumps([snapshot(), terminal()] if events is None else events)]
        with tempfile.TemporaryDirectory() as cwd:
            return fc.measure(command, cwd=Path(cwd), model="fixture-model", effort="high",
                              prompt="test prompt", timeout=timeout)

    def test_success_early_and_late_usage_and_duplicate_rpc(self):
        for scenario in ("normal", "early", "late", "duplicate_rpc"):
            with self.subTest(scenario=scenario):
                # Usage can follow terminal, including before turn/start response.
                r = self.run_fixture(scenario, events=[terminal(), snapshot(), snapshot()])
                self.assertEqual(r["outcome"], "completed_with_usage")
                self.assertEqual(r["process_exit_code"], 0)
                self.assertEqual(r["server_turn"]["durationMs"], 1800)
                self.assertGreater(r["observer_process_elapsed_s"], 0)

    def test_protocol_failures_and_interactive_request_fail_closed(self):
        for scenario, outcome in (("rpc_error", "rpc_error"), ("interactive", "interactive_request_required"),
                                  ("malformed", "protocol_error"), ("truncated", "truncated_stream"),
                                  ("nonzero", "process_failed")):
            with self.subTest(scenario=scenario):
                self.assertEqual(self.run_fixture(scenario)["outcome"], outcome)

    def test_timeout_interrupts_only_new_turn(self):
        r = self.run_fixture("timeout", timeout=0.25)
        self.assertEqual(r["outcome"], "timed_out")
        self.assertEqual(r["process_exit_code"], 0)
        self.assertIsNone(r["usage_snapshot"])

    def test_cleanup_ends_the_server_process_group(self):
        with tempfile.TemporaryDirectory() as cwd:
            command = [sys.executable, "-u", "-c", SERVER, "stuck_tool", json.dumps(CONFIG), "[]"]
            r = fc.measure(command, cwd=Path(cwd), model="fixture-model", effort="high",
                           prompt="test prompt", timeout=0.5)
            tool = int((Path(cwd) / "tool.pid").read_text())
        self.addCleanup(lambda: gone(tool, 0) or os.kill(tool, signal.SIGKILL))
        self.assertEqual(r["outcome"], "timed_out")
        self.assertEqual(r["process_exit_code"], -signal.SIGTERM)
        self.assertTrue(gone(tool))

    def test_persisted_or_child_thread_is_rejected_before_turn(self):
        for field, value in (("ephemeral", False), ("parentThreadId", "parent")):
            config = copy.deepcopy(CONFIG)
            config["thread"][field] = value
            self.assertEqual(self.run_fixture(config=config)["outcome"], "protocol_error")

    def test_launch_failure_is_not_zero_cost(self):
        r = fc.measure(["/nonexistent/fr-55af2f"], cwd=Path("/private/tmp"),
                       model="fixture-model", effort="high", prompt="test", timeout=1)
        self.assertEqual(r["outcome"], "launch_error")
        self.assertIsNone(r["usage_snapshot"])
        self.assertIsNone(r["process_exit_code"])


if __name__ == "__main__":
    unittest.main()
