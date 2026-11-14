"""board and overview, driven through the CLI as a subprocess."""
import collections
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

PM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKET = os.path.join(PM, "tools", "ticket")
PM_CLI = os.path.join(PM, "cli", "pm")
ID = re.compile(r"\btt-[0-9a-f]{6,11}\b")


def sh(cwd, argv, expect=0):
    r = subprocess.run([sys.executable, *argv], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == expect, f"{argv} -> {r.returncode}: {r.stderr}"
    return r.stdout


class ViewCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = os.path.realpath(self._tmp.name)
        self.made = set()
        self.ticket("init", "--prefix", "tt")

    def ticket(self, *args):
        return sh(self.dir, [TICKET, *args]).strip()

    def make(self, title, *extra):
        tid = self.ticket("create", title, *extra)
        self.made.add(tid)
        return tid

    def block(self, blocker, blocked):
        """`dep <blocker> blocks <blocked>`, written to the store while dep is unbuilt."""
        path = os.path.join(self.dir, ".pm", "tickets.jsonl")
        with open(path) as f:
            rows = [json.loads(line) for line in f if line.strip()]
        for row in rows:
            if row["id"] == blocker:
                row["edges"].append({"type": "blocks", "to": blocked})
        with open(path, "w") as f:
            f.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))

    def board(self, *args):
        return sh(self.dir, [PM_CLI, "view", "board", *args])

    def overview(self, *args):
        return sh(self.dir, [PM_CLI, "view", "overview", *args])


class BoardTest(ViewCase):
    def test_status_sections_in_lifecycle_order(self):
        a = self.make("open one")
        b = self.make("claimed one")
        self.ticket("claim", b, "--as", "agent")
        c = self.make("unmerged one")
        self.ticket("close", c, "--unmerged")
        d = self.make("closed one")
        self.ticket("close", d)
        out = self.board("--include-closed")
        for tid in (a, b, c, d):
            self.assertIn(tid, out)
        self.assertLess(out.index("OPEN"), out.index("CLAIMED"))
        self.assertLess(out.index("CLAIMED"), out.index("DONE-UNMERGED"))
        self.assertLess(out.index("DONE-UNMERGED"), out.index("CLOSED"))

    def test_priority_sections_skip_empties(self):
        for p in ("0", "2", "4"):
            self.make("t" + p, "--priority", p)
        out = self.board("--group-by", "priority")
        self.assertNotIn("P1", out)
        self.assertNotIn("P3", out)
        self.assertLess(out.index("P0"), out.index("P2"))
        self.assertLess(out.index("P2"), out.index("P4"))

    def test_epic_nests_children_then_orphans(self):
        epic = self.make("the epic", "--kind", "epic")
        child = self.make("child", "--parent", epic)
        loose = self.make("loose task")
        out = self.board("--group-by", "epic")
        lines = out.splitlines()
        epic_line = next(l for l in lines if epic in l and l.strip().startswith("tt-"))
        child_line = next(l for l in lines if child in l)
        loose_line = next(l for l in lines if loose in l)
        self.assertGreater(len(child_line) - len(child_line.lstrip(" ")),
                           len(epic_line) - len(epic_line.lstrip(" ")))
        self.assertEqual(loose_line.lstrip(" "), loose_line)
        self.assertLess(out.index(child), out.index("ORPHANS"))
        self.assertGreater(out.index(loose), out.index("ORPHANS"))

    def test_semaphores_first_and_marked(self):
        flagged = self.make("flagged", "--priority", "3", "--label", "semaphore")
        ordinary = self.make("ordinary", "--priority", "1")
        out = self.board()
        self.assertLess(out.index(flagged), out.index(ordinary))
        self.assertIn("SEM", next(l for l in out.splitlines() if flagged in l))
        self.assertNotIn("SEM", next(l for l in out.splitlines() if ordinary in l))

    def test_blocked_vs_ready(self):
        blocker = self.make("blocker")
        blocked = self.make("blocked")
        self.block(blocker, blocked)
        lines = self.board().splitlines()
        blocker_line = next(l for l in lines if blocker in l)
        blocked_line = next(l for l in lines if blocked in l)
        self.assertIn("READY", blocker_line)
        self.assertNotIn("BLOCKED", blocker_line)
        self.assertIn("BLOCKED", blocked_line)
        self.assertNotIn("READY", blocked_line)

    def test_empty_store_says_nothing_to_show(self):
        for gb in ("status", "priority", "epic"):
            self.assertIn("nothing to show", self.board("--group-by", gb))

    def test_color_flag(self):
        self.make("sem", "--priority", "0")
        self.assertNotIn("\x1b", self.board())
        self.assertIn("\x1b", self.board("--color"))

    def test_ticket_and_view_entries_match(self):
        self.make("solo")
        self.assertEqual(self.board(), sh(self.dir, [TICKET, "board"]))

    def test_bad_group_by_is_usage_error(self):
        sh(self.dir, [PM_CLI, "view", "board", "--group-by", "bogus"], expect=2)

    def test_ids_reconcile_one_to_one_in_every_grouping(self):
        epic = self.make("epic", "--kind", "epic")
        c1 = self.make("child one", "--parent", epic)
        c2 = self.make("child two", "--parent", epic)
        self.block(c1, c2)
        self.make("sem", "--priority", "0")
        claimed = self.make("claimed ticket")
        self.ticket("claim", claimed, "--as", "agent-x")
        self.make("orphan ticket")
        closed = self.make("closed ticket")
        self.ticket("close", closed)
        expected = set(self.made)
        for gb in ("status", "priority", "epic"):
            found = ID.findall(self.board("--group-by", gb))
            self.assertEqual(set(found), expected - {closed}, gb)
            self.assertNotIn(closed, found)
            for tid, n in collections.Counter(found).items():
                self.assertEqual(n, 1, f"{tid} x{n} in {gb}")


class OverviewTest(ViewCase):
    def test_header_warns_generated(self):
        self.make("solo")
        text = self.overview()
        self.assertIn("GENERATED", text)
        self.assertIn("do not hand-edit", text)
        self.assertIn("scripts/overview.py", text)
        self.assertIn(self.dir, text)

    def test_sections_only_when_non_empty(self):
        ready = self.make("ready task")
        text = self.overview()
        self.assertIn("## Ready", text)
        for absent in ("## Semaphores", "## In flight", "## Done, unmerged", "## Epics"):
            self.assertNotIn(absent, text)
        self.make("sem", "--priority", "0")
        self.assertIn("## Semaphores", self.overview())
        self.ticket("claim", ready, "--as", "alice")
        self.assertIn("## In flight", self.overview())
        unmerged = self.make("unmerged work")
        self.ticket("close", unmerged, "--unmerged")
        self.assertIn("## Done, unmerged", self.overview())
        epic = self.make("an epic", "--kind", "epic")
        self.make("epic child", "--parent", epic)
        self.assertIn("## Epics", self.overview())

    def test_semaphore_both_routes(self):
        a = self.make("critical", "--priority", "0")
        b = self.make("flagged", "--label", "semaphore")
        self.make("ordinary")
        section = self.overview().split("## Semaphores", 1)[1].split("## ", 1)[0]
        self.assertIn(a, section)
        self.assertIn(b, section)

    def test_epic_nesting_and_orphans(self):
        epic = self.make("the epic", "--kind", "epic")
        c1 = self.make("child open", "--parent", epic)
        c2 = self.make("child claimed", "--parent", epic)
        self.ticket("claim", c2, "--as", "bob")
        loose = self.make("loose task")
        text = self.overview()
        epics = text.split("## Epics", 1)[1].split("## Orphans", 1)[0]
        for tid in (epic, c1, c2):
            self.assertIn(f"`{tid}`", epics)
        self.assertIn("open children: 2", epics)
        self.assertNotIn("not in scope", epics)
        orphans = text.split("## Orphans", 1)[1]
        self.assertIn(f"`{loose}`", orphans)
        self.assertNotIn(f"`{c1}`", orphans)

    def test_closed_children_counted_not_named(self):
        epic = self.make("the epic", "--kind", "epic")
        live = self.make("live child", "--parent", epic)
        dead = self.make("dead child", "--parent", epic)
        self.ticket("close", dead)
        text = self.overview()
        self.assertIn(f"`{live}`", text)
        self.assertNotIn(dead, text)
        self.assertIn("(+1 not in scope)", text)

    def test_blocked_ticket_shows_blockers(self):
        blocker = self.make("blocker")
        blocked = self.make("blocked")
        self.block(blocker, blocked)
        orphans = self.overview().split("## Orphans", 1)[1]
        line = next(l for l in orphans.splitlines() if blocked in l)
        self.assertIn(f"blocked by `{blocker}`", line)

    def test_out_writes_file(self):
        self.make("solo")
        path = os.path.join(self.dir, "out.md")
        self.assertEqual(self.overview("--out", path), f"wrote {path}\n")
        with open(path) as f:
            self.assertIn("# Ticket store overview", f.read())

    def test_include_closed(self):
        t = self.make("done soon")
        self.ticket("close", t)
        self.assertNotIn(t, self.overview())
        self.assertIn("include_closed=`True`", self.overview("--include-closed"))

    def test_ids_reconcile_with_store(self):
        epic = self.make("the epic", "--kind", "epic")
        self.make("epic child", "--parent", epic)
        c2 = self.make("claimed child", "--parent", epic)
        self.ticket("claim", c2, "--as", "carol")
        blocker = self.make("blocker")
        blocked = self.make("blocked")
        self.block(blocker, blocked)
        self.make("sem", "--priority", "0")
        expected = set(self.made)
        rendered = set(re.findall(r"`(tt-[0-9a-f]+)`", self.overview()))
        self.assertEqual(rendered, expected)


if __name__ == "__main__":
    unittest.main()
