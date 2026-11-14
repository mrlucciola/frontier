#!/usr/bin/python3
"""CLI contract suite: what the rewritten ticket CLI does that the old one did not.

Black-box: runs pm/tools/ticket as a subprocess and reads its output and exit
code. Imports nothing from pm/tools. Run:

    /usr/bin/python3 -B -m unittest discover -s pm/tests -p 'test_cli_contract.py'

A case whose verb has no file under pm/tools/verbs/ yet is skipped as
"unbuilt: <verb>"; the integration ticket removes those branches.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "tools")
TICKET_CLI = os.path.join(TOOLS, "ticket")
VERBS_DIR = os.path.join(TOOLS, "verbs")

KEPT = ("init", "create", "show", "list", "ready", "tree", "summary", "claim",
        "hold", "release", "close", "reopen", "note", "edit", "dep", "unlink",
        "reparent", "where", "stores", "history", "validate", "lint", "archive",
        "board", "overview")
DROPPED = ("upgrade", "adopt", "fix-labels", "notes-prune")

_REGISTRY = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
_REGISTRY.write('{"stores": []}\n')
_REGISTRY.close()
os.environ["PM_STORES_FILE"] = _REGISTRY.name
os.environ.pop("PM_UNBUILT_LOG", None)


def built(verb):
    return os.path.exists(os.path.join(VERBS_DIR, verb + ".py"))


def pm(cwd, *argv, env=None):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run([sys.executable, "-B", TICKET_CLI, *argv], cwd=cwd,
                          capture_output=True, text=True, env=e)


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.ok("init", "--prefix", "tt")

    def ok(self, *argv, env=None):
        r = pm(self.dir, *argv, env=env)
        self.assertEqual(r.returncode, 0, f"pm {' '.join(argv)}: {r.stderr}")
        return r.stdout.strip()

    @property
    def ticket_file(self):
        return os.path.join(self.dir, ".pm", "tickets.jsonl")

    def rows(self):
        with open(self.ticket_file) as f:
            return [json.loads(ln) for ln in f if ln.strip()]

    def write_rows(self, rows):
        with open(self.ticket_file, "w") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")


class DroppedVerbTest(Base):
    def test_dropped_verbs_exit_2(self):
        for verb in DROPPED:
            with self.subTest(verb=verb):
                self.assertEqual(pm(self.dir, verb).returncode, 2)


class NoTelemetryTest(unittest.TestCase):
    def test_no_file_written_under_home(self):
        with tempfile.TemporaryDirectory() as home, \
                tempfile.TemporaryDirectory() as work:
            env = {"HOME": home}
            e = dict(os.environ, HOME=home)
            e.pop("PM_TELEMETRY_DIR", None)
            for argv in (("init", "--prefix", "tt"), ("create", "a title")):
                r = subprocess.run([sys.executable, "-B", TICKET_CLI, *argv], cwd=work,
                                   capture_output=True, text=True, env=e)
                self.assertEqual(r.returncode, 0, r.stderr)
            tid = r.stdout.strip().split()[0]
            r = subprocess.run([sys.executable, "-B", TICKET_CLI, "show", tid], cwd=work,
                               capture_output=True, text=True, env=e)
            self.assertEqual(r.returncode, 0, r.stderr)
            found = []
            for root, dirs, files in os.walk(home):
                found += [os.path.join(root, n) for n in dirs + files]
            self.assertEqual(found, [], env)


class ShowFieldTest(Base):
    def test_fields(self):
        tid = self.ok("create", "field probe", "--label", "b", "--label", "a",
                      "--priority", "1")
        out = pm(self.dir, "show", tid, "--field", "title", "--field", "labels",
                 "--field", "assignee", "--field", "priority")
        self.assertEqual(out.returncode, 0, out.stderr)
        lines = out.stdout.split("\n")
        self.assertEqual(lines[0], "field probe")
        self.assertEqual(lines[1], ",".join(json.loads(self.ok("show", tid, "--json"))["labels"]))
        self.assertIn("a", lines[1])
        self.assertIn("b", lines[1])
        self.assertEqual(lines[2], "")
        self.assertEqual(lines[3], "1")

    def test_field_order_follows_arguments(self):
        tid = self.ok("create", "order probe")
        r = pm(self.dir, "show", tid, "--field", "status", "--field", "title")
        self.assertEqual(r.stdout.split("\n")[:2], ["open", "order probe"])

    def test_booleans_lowercase(self):
        epic, sub = self.compacted_pair()
        r = pm(self.dir, "show", sub, "--field", "compacted")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "true")

    def test_unknown_field_exits_1(self):
        tid = self.ok("create", "x")
        r = pm(self.dir, "show", tid, "--field", "nonesuch")
        self.assertEqual(r.returncode, 1)
        self.assertIn("pm: show: no field nonesuch", r.stderr)

    def test_field_with_json_exits_2(self):
        tid = self.ok("create", "x")
        self.assertEqual(pm(self.dir, "show", tid, "--field", "title", "--json").returncode, 2)

    def compacted_pair(self):
        return make_compacted(self)


def make_compacted(case):
    epic = case.ok("create", "the epic", "--kind", "epic")
    sub = "tt-cmp001"
    rows = case.rows()
    for r in rows:
        if r["id"] == epic:
            r["subtasks"] = [{"id": sub, "title": "folded task",
                              "closed": "2026-01-02T03:04:05Z", "reason": "done",
                              "note": "folded note"}]
    case.write_rows(rows)
    return epic, sub


class CompactedReadTest(Base):
    def test_json_and_text(self):
        epic, sub = make_compacted(self)
        obj = json.loads(self.ok("show", sub, "--json"))
        self.assertIs(obj["compacted"], True)
        self.assertEqual(obj["status"], "closed")
        self.assertIn(f"compacted into {epic} on close", self.ok("show", sub))
        self.assertIn("subtasks:", self.ok("show", epic))


MUTATORS = {
    "claim": lambda t: ["claim", t, "--as", "w"],
    "hold": lambda t: ["hold", t, "why"],
    "release": lambda t: ["release", t],
    "close": lambda t: ["close", t],
    "reopen": lambda t: ["reopen", t],
    "note": lambda t: ["note", t, "text"],
    "edit": lambda t: ["edit", t, "--title", "new"],
    "dep": lambda t: ["dep", t, "blocks", "tt-other"],
    "unlink": lambda t: ["unlink", t, "tt-other"],
    "reparent": lambda t: ["reparent", t, "--none"],
}


class RefusalTest(Base):
    def archive_fixture(self):
        tid = "tt-arc001"
        row = {"id": tid, "title": "old", "kind": "task", "status": "closed"}
        os.makedirs(os.path.join(self.dir, ".pm", "archive"))
        with open(os.path.join(self.dir, ".pm", "archive", "2025.jsonl"), "w") as f:
            f.write(json.dumps(row) + "\n")
        with open(os.path.join(self.dir, ".pm", "archive", "archive-index.jsonl"), "w") as f:
            f.write(json.dumps({"id": tid, "source": "self", "path": "2025.jsonl",
                                "meta": {}}) + "\n")
        return tid

    def test_compacted_refused(self):
        epic, sub = make_compacted(self)
        for verb, mk in MUTATORS.items():
            with self.subTest(verb=verb):
                if not built(verb):
                    self.skipTest(f"unbuilt: {verb}")
                r = pm(self.dir, *mk(sub))
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn(f"{sub} was compacted into {epic} when it closed", r.stderr)
                self.assertIn("it cannot be changed. File a new ticket.", r.stderr)

    def test_archived_refused(self):
        tid = self.archive_fixture()
        for verb, mk in MUTATORS.items():
            with self.subTest(verb=verb):
                if not built(verb):
                    self.skipTest(f"unbuilt: {verb}")
                r = pm(self.dir, *mk(tid))
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn(f"{tid} is archived; it cannot be changed. File a new ticket.",
                              r.stderr)


class ValidateHintTest(Base):
    def test_fix_hints_name_no_dropped_verb(self):
        if not built("validate"):
            self.skipTest("unbuilt: validate")
        self.ok("create", "unsorted", "--label", "b", "--label", "a")
        rows = self.rows()
        rows[0]["labels"] = ["b", "a", "B"]
        rows[0].pop("updated", None)
        self.write_rows(rows)
        r = pm(self.dir, "validate")
        text = r.stdout + r.stderr
        for verb in DROPPED:
            self.assertNotIn(verb, text)


PM_DISPATCHER = os.path.join(HERE, "..", "cli", "pm")


class DispatcherTest(unittest.TestCase):
    def run_pm(self, cwd, *argv):
        return subprocess.run(["/usr/bin/python3", "-B", PM_DISPATCHER, *argv],
                              cwd=cwd, capture_output=True, text=True)

    def test_view_accepts_only_board_and_overview(self):
        with tempfile.TemporaryDirectory() as work:
            self.assertEqual(self.run_pm(work, "ticket", "init", "--prefix", "tt").returncode, 0)
            before = os.listdir(os.path.join(work, ".pm"))
            r = self.run_pm(work, "view", "create", "x")
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertEqual(os.listdir(os.path.join(work, ".pm")), before)
            with open(os.path.join(work, ".pm", "tickets.jsonl")) as f:
                self.assertEqual(f.read(), "")

    def test_help_exits_0(self):
        with tempfile.TemporaryDirectory() as work:
            for argv in ((), ("-h",), ("--help",)):
                r = self.run_pm(work, *argv)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("usage: pm <family> <verb>", r.stdout)


class HistoryRefRemedyTest(unittest.TestCase):
    def test_named_store_prints_the_repo_remedy(self):
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as elsewhere:
            repo = os.path.realpath(repo)
            self.assertEqual(pm(repo, "init", "--prefix", "tt").returncode, 0)
            subprocess.run(["git", "-C", repo, "init", "-q", "-b", "main"], check=True)
            cfg = os.path.join(repo, ".pm", "config.json")
            with open(cfg) as f:
                config = json.load(f)
            config["history_ref"] = "pm-store"
            with open(cfg, "w") as f:
                json.dump(config, f)
            hook = os.path.join(repo, ".git", "hooks", "reference-transaction")
            with open(hook, "w") as f:
                f.write("#!/bin/sh\nif [ \"$1\" = prepared ] && cat | grep -q "
                        "refs/heads/pm-store; then echo 'ref refused' >&2; exit 1; fi\n")
            os.chmod(hook, 0o755)
            r = pm(elsewhere, "--store", repo, "create", "row survives")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(f"pm ticket history sync --repo {repo}", r.stderr)


@unittest.skipUnless(built("history"), "unbuilt: history")
class HistoryMarkerTest(unittest.TestCase):
    """The `.pm/history-pending` gitignore line and fault marker, driven by a
    marker the test writes (the interval that normally writes it is not built)."""

    MARKER_LINE = ".pm/history-pending"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = os.path.realpath(tmp.name)
        for argv in (("init", "-q", "-b", "main"), ("config", "user.name", "t"),
                     ("config", "user.email", "t@example.invalid"),
                     ("config", "commit.gpgsign", "false")):
            self.git(*argv)
        with open(os.path.join(self.repo, "README"), "w") as f:
            f.write("x\n")
        self.git("add", "README")
        self.git("commit", "-q", "-m", "seed")
        self.assertEqual(pm(self.repo, "init", "--prefix", "tt").returncode, 0)
        self.assertEqual(pm(self.repo, "create", "row").returncode, 0)
        self.git("add", ".gitignore", ".pm/config.json")
        self.git("commit", "-q", "-m", "track config")
        self.marker = os.path.join(self.repo, ".pm", "history-pending")

    def git(self, *argv):
        r = subprocess.run(["git", "-C", self.repo, *argv], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def hist(self, *argv):
        r = pm(self.repo, "history", *argv)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def ignored(self):
        with open(os.path.join(self.repo, ".gitignore")) as f:
            return f.read().splitlines()

    def fault_marker(self):
        with open(self.marker, "w") as f:
            f.write("some git fault\n")

    def test_enable_ignores_the_marker_and_disable_drops_line_and_file(self):
        self.hist("enable")
        self.assertIn(self.MARKER_LINE, self.ignored())
        self.assertIn(".pm/tickets.jsonl", self.ignored())
        self.fault_marker()
        self.assertEqual(self.git("status", "--porcelain", "--", self.MARKER_LINE), "")
        self.hist("disable")
        self.assertFalse(os.path.exists(self.marker))
        self.assertNotIn(self.MARKER_LINE, self.ignored())
        self.assertNotIn(".pm/tickets.jsonl", self.ignored())

    def test_restore_and_sync_clear_the_marker(self):
        self.hist("enable")
        self.fault_marker()
        self.hist("sync")
        self.assertFalse(os.path.exists(self.marker))
        self.fault_marker()
        os.remove(os.path.join(self.repo, ".pm", "tickets.jsonl"))
        self.assertEqual(self.hist("status"), "missing")
        self.hist("restore")
        self.assertFalse(os.path.exists(self.marker))
        self.assertEqual(self.hist("status"), "on")


class UnbuiltTest(Base):
    def test_unbuilt_verb_contract(self):
        missing = [v for v in KEPT if not built(v)]
        if not missing:
            self.skipTest("every kept verb is built")
        verb = missing[0]
        log = os.path.join(self.dir, "unbuilt.log")
        r = pm(self.dir, verb, env={"PM_UNBUILT_LOG": log})
        self.assertEqual(r.returncode, 70, r.stderr)
        self.assertIn(f"pm: '{verb}' is not built yet", r.stderr)
        with open(log) as f:
            self.assertIn(verb, f.read().split())


class ClaimReopenHoldTest(Base):
    ENV = {"PM_AGENT": "claude/w", "PM_SESSION_ID": "sess-1",
           "PM_HOLD_STATE_DIR": tempfile.mkdtemp()}

    def setUp(self):
        if not all(built(v) for v in ("claim", "hold", "release")):
            self.skipTest("unbuilt: claim/hold/release")
        super().setUp()

    def done_unmerged(self):
        tid = self.ok("create", "parked work")
        rows = self.rows()
        rows[0].update(status="done-unmerged", closed_by="agent:claude/x#00000000",
                       findings=["none"], findings_absent=True)
        self.write_rows(rows)
        return tid

    def test_claim_refuses_done_unmerged_without_reopen(self):
        tid = self.done_unmerged()
        r = pm(self.dir, "claim", tid, "--as", "w", env=self.ENV)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"pm: cannot claim a done-unmerged ticket; resume it with "
                      f"`pm ticket claim {tid} --as <name> --reopen`", r.stderr)

    def test_claim_reopen_takes_done_unmerged_back(self):
        tid = self.done_unmerged()
        out = self.ok("claim", tid, "--as", "w", "--reopen", env=self.ENV)
        self.assertTrue(out.startswith(f"{tid} claimed by agent:claude/w#"))
        row = self.rows()[0]
        self.assertEqual(row["status"], "claimed")
        for key in ("findings", "findings_absent", "closed_by"):
            self.assertNotIn(key, row)

    def test_claim_reopen_checks_readiness_as_if_open(self):
        tid = self.done_unmerged()
        blocker = self.ok("create", "the blocker")
        rows = self.rows()
        for r in rows:
            if r["id"] == blocker:
                r["edges"].append({"type": "blocks", "to": tid})
        self.write_rows(rows)
        r = pm(self.dir, "claim", tid, "--as", "w", "--reopen", env=self.ENV)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"pm: not ready — blocked by: {blocker}", r.stderr)

    def test_hold_on_unclaimed_names_the_verb_that_moves_it_on(self):
        tid = self.ok("create", "idle")
        r = pm(self.dir, "hold", tid, "why", env=self.ENV)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"pm: not claimed (status: open); `pm ticket claim {tid} --as "
                      "<name>` takes it", r.stderr)

    def test_hold_and_release_round_trip(self):
        tid = self.ok("create", "held work")
        self.ok("claim", tid, "--as", "w", env=self.ENV)
        self.assertEqual(self.ok("hold", tid, "waiting", env=self.ENV),
                         f"{tid} held: waiting")
        self.assertEqual(self.rows()[0]["hold"]["reason"], "waiting")
        self.assertEqual(self.ok("release", tid, env=self.ENV), f"{tid} released")
        row = self.rows()[0]
        self.assertNotIn("hold", row)
        self.assertEqual(row["released_by"].split("#")[0], "agent:claude/w")


class CloseReopenTest(Base):
    ENV = {"PM_AGENT": "claude/w", "PM_SESSION_ID": "sess-1"}

    def setUp(self):
        if not all(built(v) for v in ("close", "reopen")):
            self.skipTest("unbuilt: close/reopen")
        super().setUp()

    def test_direct_close_refused_while_worktree_exists(self):
        tid = self.ok("create", "wt work")
        os.makedirs(os.path.join(self.dir, ".worktrees", tid))
        r = pm(self.dir, "close", tid, "--findings", "none")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"pm: {tid} has a worktree at ", r.stderr)
        self.assertIn(f"run `wt finish {tid}` to merge and close", r.stderr)
        self.assertEqual(self.ok("close", tid, "--via", "wt", "--findings", "none"),
                         f"{tid} -> closed")

    def test_already_closed_refusal_precedes_worktree_refusal(self):
        tid = self.ok("create", "twice")
        self.ok("close", tid, "--findings", "none")
        os.makedirs(os.path.join(self.dir, ".worktrees", tid))
        r = pm(self.dir, "close", tid, "--findings", "none")
        self.assertIn(f"pm: already closed; `pm ticket reopen {tid}` reopens it", r.stderr)

    def test_close_unmerged_writes_park_note_and_closed_by(self):
        tid = self.ok("create", "parked")
        out = self.ok("close", tid, "--unmerged", "--note", "branch x", "--findings",
                      "none", env=self.ENV)
        self.assertEqual(out, f"{tid} -> done-unmerged")
        row = self.rows()[0]
        self.assertEqual(row["notes"][-1]["kind"], "park")
        self.assertTrue(row["closed_by"].startswith("agent:claude/w#"))
        self.assertEqual(row["findings"], ["none"])

    def test_close_without_findings_warns_then_phase_2_refuses(self):
        tid = self.ok("create", "unattested")
        r = pm(self.dir, "close", tid)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pm: no --findings:", r.stderr)
        self.assertTrue(self.rows()[0]["findings_absent"])
        tid2 = self.ok("create", "strict")
        cfg = os.path.join(self.dir, ".pm", "config.json")
        with open(cfg) as f:
            conf = json.load(f)
        conf["findings_required"] = True
        with open(cfg, "w") as f:
            json.dump(conf, f)
        r = pm(self.dir, "close", tid2)
        self.assertEqual(r.returncode, 1)
        self.assertIn("pm: no --findings:", r.stderr)
        r = pm(self.dir, "close", tid2, "--findings", "none")
        self.assertIn("needs a non-empty --note or an existing note", r.stderr)

    def test_close_is_all_or_nothing(self):
        a, b = self.ok("create", "a"), self.ok("create", "b")
        self.ok("close", b, "--findings", "none")
        r = pm(self.dir, "close", a, b, "--findings", "none")
        self.assertEqual(r.returncode, 1)
        self.assertEqual({x["id"]: x["status"] for x in self.rows()},
                         {a: "open", b: "closed"})

    def test_epic_with_open_children(self):
        epic = self.ok("create", "the epic", "--kind", "epic")
        child = self.ok("create", "kid", "--parent", epic)
        r = pm(self.dir, "close", epic, "--findings", "none")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"{epic} has open children:", r.stderr)
        self.ok("close", epic, "--detach", "--findings", "none")
        rows = {x["id"]: x for x in self.rows()}
        self.assertIsNone(rows[child]["parent"])
        self.assertEqual(rows[child]["notes"][-1]["kind"], "edit-trail")

    def test_findings_unknown_id_refused(self):
        tid = self.ok("create", "x")
        r = pm(self.dir, "close", tid, "--findings", "tt-nope00")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--findings", r.stderr)

    def test_deploy_check_exit_4_and_override(self):
        tid = self.ok("create", "tool", "--label", "tooling")
        bindir = os.path.join(self.dir, "bin")
        os.makedirs(bindir)
        deploy = os.path.join(bindir, "deploy")
        with open(deploy, "w") as f:
            f.write("#!/bin/sh\necho stale\nexit 1\n")
        os.chmod(deploy, 0o755)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        def git(*a):
            r = subprocess.run(["git", "-C", self.dir, *a], capture_output=True,
                               text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
        git("init", "-q", "-b", "main")
        git("add", "bin/deploy")
        git("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
            "commit", "-q", "-m", f"{tid}: add deploy")
        r = pm(self.dir, "close", tid, "--findings", "none")
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn("pm: nothing closed.", r.stderr)
        self.assertEqual(self.rows()[0]["status"], "open")
        self.ok("close", tid, "--findings", "none", "--no-deploy-check", "why")
        self.assertEqual(self.rows()[0]["notes"][-1],
                         {**self.rows()[0]["notes"][-1], "kind": "finding",
                          "text": "deploy check skipped: why"})

    def test_reopen_clears_attribution_and_refuses_claimed(self):
        tid = self.ok("create", "r")
        self.ok("close", tid, "--findings", "none", env=self.ENV)
        self.assertEqual(self.ok("reopen", tid), f"{tid} reopened")
        row = self.rows()[0]
        for key in ("findings", "findings_absent", "closed_by", "hold"):
            self.assertNotIn(key, row)
        r = pm(self.dir, "reopen", tid)
        self.assertIn(f"pm: already open; `pm ticket claim {tid} --as <name>` takes it",
                      r.stderr)
        self.ok("claim", tid, "--as", "w")
        r = pm(self.dir, "reopen", tid)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"{tid} is claimed by ", r.stderr)
        self.assertIn(f"`pm ticket release {tid}` first, then reopen", r.stderr)


if __name__ == "__main__":
    unittest.main()
