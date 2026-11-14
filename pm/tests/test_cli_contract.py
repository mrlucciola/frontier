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


if __name__ == "__main__":
    unittest.main()
