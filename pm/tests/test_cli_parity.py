#!/usr/bin/python3
"""CLI parity suite: the behavior the rewritten ticket CLI must keep.

Copied from ~/frontier/runtime-tools/pm/ticket/tests/test_ticket_cli.py and trimmed
to the kept verbs (pm/docs/cut-list.md lists every removed, changed and skipped
test). Run it through run_parity.py, which names the CLI under test:

    /usr/bin/python3 -B pm/tests/run_parity.py --cli <path to ticket CLI>

Runs the real CLI as a subprocess (same surface agents use). Each test gets a
fresh store in a temp dir. Stdlib only.
"""
import fcntl
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

_CLI_OVERRIDE = os.environ.get("PM_CLI_UNDER_TEST")
# cwd-relative to THIS process's own cwd (not each subprocess call's cwd,
# which varies per test -- see `run()` below), resolved once at import time
# so every later subprocess call still finds it regardless of its own cwd.
TICKET_CLI = (os.path.abspath(_CLI_OVERRIDE) if _CLI_OVERRIDE else
      os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "ticket"))

# This file drives the CLI as a subprocess and does not import ticket_core,
# so the v1/v2 on-disk layouts are named here as their own constants (mirrors
# ticket_core.V1_STORE_DIR/STORE_DIR_NAMES[0] and TICKET_FILENAME_V1/V2).
V1_STORE_DIR = ".backlog"
V1_TICKET_FILE = "issues.jsonl"
# cl-200715: `pm ticket init` now writes a fresh spec_version 2 store.
V2_STORE_DIR = ".pm"
V2_TICKET_FILE = "tickets.jsonl"
V2_TICKET_PATH = V2_STORE_DIR + "/" + V2_TICKET_FILE

# Every subprocess inherits an empty registry, so no test reads the source or
# deployed runtime-tools/pm/stores.json or any real store.
_EMPTY_REGISTRY = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
_EMPTY_REGISTRY.write('{"stores": []}\n')
_EMPTY_REGISTRY.close()
os.environ["PM_STORES_FILE"] = _EMPTY_REGISTRY.name
# No test run writes the live pm telemetry log (fr-1e5041); the telemetry
# test below points one call at its own temp dir.
os.environ["PM_TELEMETRY_DIR"] = "-"


DEFERRED = unittest.skip("deferred feature, not in the rewrite yet: pm/docs/cut-list.md")


def run(cwd, *argv, expect=0):
    r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=cwd,
                       capture_output=True, text=True)
    assert r.returncode == expect, f"pm ticket {' '.join(argv)}: rc={r.returncode}\n{r.stderr}"
    return r.stdout.strip()


class TicketCliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        run(self.store, "init", "--prefix", "tt")

    def make(self, title, *extra):
        return run(self.store, "create", title, *extra)

    def ready_ids(self):
        return [t["id"] for t in json.loads(run(self.store, "ready", "--json"))]

    # --- agent-facing tooling at scale (cl-b4c148, cl-4e8683) ---

    def test_id_capture_without_shell_substitution(self):
        path = os.path.join(self.store, "newid.txt")
        tid = self.make("captured", "--id-file", path)
        with open(path) as f:
            self.assertEqual(f.read().strip(), tid)

    def test_create_can_claim_in_the_same_call(self):
        tid = self.make("create and claim", "--claim-as", "agent-a")
        t = json.loads(run(self.store, "show", tid, "--json"))
        self.assertEqual(t["status"], "claimed")
        # v2 assignee identity (ADR Q7) wraps the name as
        # 'agent:<provider>/agent-a#<tok>' or 'human:agent-a' depending on
        # the test env -- cl-200715 no longer gets a bare 'agent-a#<tok>'.
        self.assertIn("agent-a", t["assignee"])
        self.assertNotIn(tid, self.ready_ids())

    def test_create_refuses_to_claim_an_epic(self):
        """--claim-as goes through the same veto as `claim`, so the write path
        cannot produce the claimed epic that `pm ticket lint` reports as drift."""
        r = subprocess.run(
            [sys.executable, TICKET_CLI, "create", "an epic", "--kind", "epic",
             "--claim-as", "agent-a"],
            cwd=self.store, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("epics aggregate work and cannot be claimed", r.stderr)
        self.assertEqual(json.loads(run(self.store, "list", "--json")), [])
        run(self.store, "lint")

    def test_bulk_close_release_reopen_and_claim(self):
        a, b, c = self.make("a"), self.make("b"), self.make("c")
        run(self.store, "claim", a, b, "--as", "agent-a")
        for tid in (a, b):
            self.assertEqual(
                json.loads(run(self.store, "show", tid, "--json"))["status"], "claimed")
        run(self.store, "release", a, b)
        run(self.store, "close", a, b, c)
        for tid in (a, b, c):
            self.assertEqual(
                json.loads(run(self.store, "show", tid, "--json"))["status"], "closed")
        run(self.store, "reopen", a, b, c)
        self.assertEqual(sorted(self.ready_ids()), sorted([a, b, c]))

    def test_bulk_is_all_or_nothing(self):
        ok, closed = self.make("ok"), self.make("closed")
        run(self.store, "close", closed)
        # one bad id in the batch must leave the whole batch unapplied
        run(self.store, "close", ok, closed, expect=1)
        self.assertEqual(
            json.loads(run(self.store, "show", ok, "--json"))["status"], "open")
        run(self.store, "claim", ok, "tt-nope", "--as", "a", expect=1)
        self.assertEqual(
            json.loads(run(self.store, "show", ok, "--json"))["status"], "open")

    def test_reparent_moves_between_epics_and_detaches(self):
        e1 = self.make("epic one", "--kind", "epic")
        e2 = self.make("epic two", "--kind", "epic")
        t = self.make("task", "--parent", e1)
        run(self.store, "reparent", t, e2)
        self.assertEqual(json.loads(run(self.store, "show", t, "--json"))["parent"], e2)
        run(self.store, "reparent", t, "--none")
        self.assertIsNone(json.loads(run(self.store, "show", t, "--json"))["parent"])

    def test_reparent_refuses_non_epic_self_and_cycles(self):
        e1 = self.make("epic one", "--kind", "epic")
        e2 = self.make("epic two", "--kind", "epic")
        task = self.make("plain task")
        run(self.store, "reparent", e2, e1)          # e2 under e1
        run(self.store, "reparent", e1, e2, expect=1)  # would cycle
        run(self.store, "reparent", e1, e1, expect=1)  # self
        run(self.store, "reparent", task, e1)
        run(self.store, "reparent", e1, task, expect=1)  # not an epic
        run(self.store, "reparent", task, expect=1)      # no target, no --none
        # both a target and --none contradict each other: refuse, don't pick
        run(self.store, "reparent", task, e1, "--none", expect=1)
        self.assertEqual(
            json.loads(run(self.store, "show", task, "--json"))["parent"], e1)

    def test_bulk_verbs_dedupe_repeated_ids(self):
        """A repeated id is one ticket: one transition, one note."""
        t = self.make("dupe")
        out = run(self.store, "close", t, t, "--note", "once")
        self.assertEqual(out.splitlines(), [f"{t} -> closed"])
        self.assertEqual(
            [n["text"] for n in json.loads(run(self.store, "show", t, "--json"))["notes"]],
            ["once"])
        run(self.store, "reopen", t, t)
        run(self.store, "claim", t, t, "--as", "agent-a")
        self.assertEqual(
            json.loads(run(self.store, "show", t, "--json"))["status"], "claimed")

    def test_close_epic_with_open_child_fails_and_names_it(self):
        epic = self.make("epic", "--kind", "epic")
        child = self.make("open child", "--parent", epic)
        r = subprocess.run([sys.executable, TICKET_CLI, "close", epic],
                            cwd=self.store, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn(child, r.stderr)
        self.assertEqual(
            json.loads(run(self.store, "show", epic, "--json"))["status"], "open")

    def test_close_epic_detach_closes_and_detaches_child(self):
        epic = self.make("epic", "--kind", "epic")
        child = self.make("open child", "--parent", epic)
        run(self.store, "close", epic, "--detach")
        self.assertEqual(
            json.loads(run(self.store, "show", epic, "--json"))["status"], "closed")
        c = json.loads(run(self.store, "show", child, "--json"))
        self.assertIsNone(c["parent"])
        self.assertIn("detached from " + epic, c["notes"][-1]["text"])

    def test_close_epic_force_closes_with_child_still_parented(self):
        epic = self.make("epic", "--kind", "epic")
        child = self.make("open child", "--parent", epic)
        run(self.store, "close", epic, "--force")
        self.assertEqual(
            json.loads(run(self.store, "show", epic, "--json"))["status"], "closed")
        self.assertEqual(
            json.loads(run(self.store, "show", child, "--json"))["parent"], epic)
        self.assertEqual(
            json.loads(run(self.store, "show", child, "--json"))["status"], "open")

    def test_lint_clean_store_and_detected_drift(self):
        """`lint` is now an alias of `validate` (spec/v1 SPEC.md section 5)."""
        epic = self.make("epic", "--kind", "epic")
        self.make("child", "--parent", epic)
        self.assertIn("OK spec_version=2", run(self.store, "lint"))
        # hand-damage the store the way a bad merge would
        path = os.path.join(self.store, V2_STORE_DIR, V2_TICKET_FILE)
        with open(path) as f:
            rows = [json.loads(x) for x in f if x.strip()]
        rows[1]["edges"] = [{"type": "blocks", "to": "tt-ghost"}]
        rows[1]["parent"] = "tt-missing"
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        out = run(self.store, "lint", expect=1)
        self.assertIn("tt-ghost", out)
        self.assertIn("tt-missing", out)
        problems = json.loads(run(self.store, "lint", "--json", expect=1))["problems"]
        self.assertTrue(any("does not exist" in p["message"] for p in problems))

    def test_lint_warns_on_stale_body_paths_and_never_fails(self):
        """fr-67554d: lint = validate's output and exit code, plus one
        `WARN stale-path <id> <path>` per missing repo path an open body cites.
        fr-d98ada: `~/` and `/Users|/home` absolute paths are checked too;
        other absolute roots, URLs, `.tmp/` and `.worktrees/` are not."""
        os.makedirs(os.path.join(self.store, "docs"))
        with open(os.path.join(self.store, "docs", "real.md"), "w") as f:
            f.write("x\n")
        home_real = os.path.expanduser("~")
        repo = os.path.realpath(self.store)
        stale = self.make("stale", "--body",
                          "See docs/real.md:3 and docs/gone.md:10-12.\n"
                          "Then add docs/planned.md for the new thing.\n"
                          f"Home: ~/no-such-dir-fr-d98ada/x.md and {home_real}/also-missing-fr-d98ada.md "
                          f"but {home_real} itself and {repo}/docs/real.md exist.\n"
                          "Not ours: https://example.com/docs/web.md, "
                          "/abs/docs/x.md, /dev/null, nodir/x.md, .tmp/scratch.py, "
                          f"{repo}/.worktrees/tt-1/docs/gone.md")
        os.makedirs(os.path.join(self.store, ".tmp"), exist_ok=True)
        self.make("codex row", "--label", "worker:codex", "--body", "docs/codex.md")
        done = self.make("closed row", "--body", "docs/closed.md")
        run(self.store, "close", done)
        out = run(self.store, "lint")
        self.assertEqual(out.splitlines()[0], run(self.store, "validate"))
        expected = [f"WARN stale-path {stale} docs/gone.md",
                    f"WARN stale-path {stale} ~/no-such-dir-fr-d98ada/x.md",
                    f"WARN stale-path {stale} {home_real}/also-missing-fr-d98ada.md"]
        self.assertEqual(out.splitlines()[1:], expected)
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store, "lint", "--json"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(json.loads(r.stdout)["ok"])
        self.assertEqual(r.stderr.strip().splitlines(), expected)
        self.assertNotIn("WARN", run(self.store, "validate"))

    def test_lint_flags_local_dump_paths_even_when_they_exist(self):
        """fr-d98ada: a body that points at the repo's .local/ dump gets one
        `WARN local-path` per path, existing or not, planned line or not;
        ~/.local (the deploy root) is an ordinary absolute path."""
        os.makedirs(os.path.join(self.store, ".local", "ws-resources"))
        with open(os.path.join(self.store, ".local", "ws-resources", "paper.md"), "w") as f:
            f.write("x\n")
        # the repo root as pm resolves it (TMPDIR may be a symlink)
        repo = os.path.realpath(self.store)
        tid = self.make("dump", "--body",
                        "Read .local/ws-resources/paper.md and .local/ws-resources/gone.md.\n"
                        f"Add {repo}/.local/ws-resources/new.md later.\n"
                        "Deployed at ~/.local/libexec/pm/cli/pm (fine if it exists).")
        out = run(self.store, "lint").splitlines()[1:]
        self.assertEqual(out[:3], [f"WARN local-path {tid} .local/ws-resources/paper.md",
                                   f"WARN local-path {tid} .local/ws-resources/gone.md",
                                   f"WARN local-path {tid} {repo}/.local/ws-resources/new.md"])
        self.assertTrue(all(line.startswith("WARN stale-path") for line in out[3:]), out)
        self.assertNotIn(".local/libexec/pm/cli/pm", " ".join(out[:3]))

    def test_ready_scope_and_limit(self):
        """fr-7bea4a: --scope <epic> keeps the epic's subtree, --scope <label>
        keeps rows carrying it, --limit cuts the lowest-priority tail, a scope
        that is neither is a refusal, and --json keeps its shape."""
        epic = self.make("epic", "--kind", "epic")
        sub = self.make("sub-epic", "--kind", "epic", "--parent", epic)
        a = self.make("a", "--parent", epic, "--priority", "1")
        b = self.make("b", "--parent", sub, "--priority", "3", "--label", "tag")
        c = self.make("c", "--priority", "2", "--label", "tag")
        d = self.make("d blocked", "--parent", epic)
        run(self.store, "dep", a, "blocks", d)
        self.assertEqual([t["id"] for t in json.loads(run(self.store, "ready", "--json", "--scope", epic))], [a, b])
        self.assertEqual([t["id"] for t in json.loads(run(self.store, "ready", "--json", "--scope", f"tt/{epic}"))], [a, b])
        self.assertEqual([t["id"] for t in json.loads(run(self.store, "ready", "--json", "--scope", "tag"))], [c, b])
        self.assertEqual([t["id"] for t in json.loads(run(self.store, "ready", "--json", "--limit", "2"))], [a, c])
        one = run(self.store, "ready", "--scope", epic, "--limit", "1").splitlines()
        self.assertEqual(len(one), 1)
        self.assertTrue(one[0].startswith(f"{a}  P1  open"), one)
        r = subprocess.run([sys.executable, TICKET_CLI, "ready", "--scope", "nope"],
                           cwd=self.store, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("neither a ticket id", r.stderr)
        r = subprocess.run([sys.executable, TICKET_CLI, "ready", "--limit", "0"],
                           cwd=self.store, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        # default output unchanged: every ready row, no cap
        self.assertEqual(len(run(self.store, "ready").splitlines()), 3)

    def test_show_notes_cap_and_parent_title(self):
        """fr-7bea4a: --notes N prints the last N notes plus one omitted line;
        the parent line carries the epic's title; --json is untouched."""
        epic = self.make("the epic title", "--kind", "epic")
        tid = self.make("child", "--parent", epic)
        for i in range(4):
            run(self.store, "note", tid, f"note {i}")
        full = run(self.store, "show", tid)
        self.assertIn(f"parent: {epic}  the epic title", full)
        self.assertEqual(sum(1 for l in full.splitlines() if l.startswith("note ")), 4)
        capped = run(self.store, "show", tid, "--notes", "2").splitlines()
        self.assertIn(f"(2 earlier notes omitted; pm ticket show {tid} prints all 4)", capped)
        self.assertEqual([l for l in capped if l.startswith("note ")][-2:],
                         [l for l in full.splitlines() if l.startswith("note ")][-2:])
        self.assertEqual(len([l for l in capped if l.startswith("note ")]), 2)
        none = run(self.store, "show", tid, "--notes", "0")
        self.assertNotIn("\nnote ", none)
        self.assertIn("(4 earlier notes omitted", none)
        # more than there are: nothing omitted, no omitted line
        self.assertNotIn("omitted", run(self.store, "show", tid, "--notes", "9"))
        obj = json.loads(run(self.store, "show", tid, "--json", "--notes", "1"))
        self.assertEqual(len(obj["notes"]), 4)
        self.assertEqual(obj["parent"], epic)

    def test_create_show_roundtrip(self):
        tid = self.make("first ticket", "--priority", "1", "--label", "infra")
        self.assertTrue(tid.startswith("tt-"))
        t = json.loads(run(self.store, "show", tid, "--json"))
        self.assertEqual(t["title"], "first ticket")
        self.assertEqual(t["priority"], 1)
        self.assertEqual(t["labels"], ["infra"])
        self.assertEqual(t["status"], "open")
        self.assertTrue(t["ready"])

    def test_create_priority_accepts_p_prefix(self):
        """fr-cce547: `--priority P4` works the same as `--priority 4`."""
        tid = self.make("p-prefixed", "--priority", "P4")
        self.assertEqual(
            json.loads(run(self.store, "show", tid, "--json"))["priority"], 4)
        tid2 = self.make("p-prefixed lowercase", "--priority", "p0")
        self.assertEqual(
            json.loads(run(self.store, "show", tid2, "--json"))["priority"], 0)

    def test_edit_priority_and_body_preserves_ticket_and_records_history(self):
        """fr-e7c33a: mutable fields change without refiling the ticket."""
        tid = self.make("editable", "--priority", "3", "--body", "old body")
        peer = self.make("peer")
        run(self.store, "dep", tid, "related", peer)
        run(self.store, "note", tid, "existing note")
        before = json.loads(run(self.store, "show", tid, "--json"))

        run(self.store, "edit", tid, "--priority", "P1", "--body", "new body")
        after = json.loads(run(self.store, "show", tid, "--json"))

        self.assertEqual(after["id"], before["id"])
        self.assertEqual(after["edges"], before["edges"])
        self.assertEqual(after["priority"], 1)
        self.assertEqual(after["body"], "new body")
        self.assertEqual(after["notes"][:1], before["notes"])
        self.assertEqual(
            [n["text"] for n in after["notes"][1:]],
            ["edit history: priority was P3",
             'edit history: body was "old body"'])
        self.assertTrue(all(n["ts"] for n in after["notes"][1:]))
        self.assertIn("OK spec_version=2", run(self.store, "lint"))

    def test_edit_accepts_numeric_priority_and_clears_body(self):
        tid = self.make("editable", "--priority", "1", "--body", "remove me")
        run(self.store, "edit", tid, "--priority", "4", "--body", "")
        edited = json.loads(run(self.store, "show", tid, "--json"))
        self.assertEqual(edited["priority"], 4)
        self.assertEqual(edited["body"], "")

    def test_edit_combined_fields_are_atomic_on_invalid_title(self):
        tid = self.make("unchanged", "--priority", "2", "--body", "before")
        before = json.loads(run(self.store, "show", tid, "--json"))
        run(self.store, "edit", tid, "--priority", "P0", "--body", "after",
            "--title", "", expect=1)
        self.assertEqual(json.loads(run(self.store, "show", tid, "--json")), before)

    def test_edit_append_body_to_nonempty_body_records_history(self):
        tid = self.make("appendable", "--body", "line one")
        run(self.store, "edit", tid, "--append-body", "line two")
        after = json.loads(run(self.store, "show", tid, "--json"))
        self.assertEqual(after["body"], "line one\nline two")
        self.assertEqual([n["text"] for n in after["notes"]],
                         ['edit history: body was "line one"'])
        run(self.store, "edit", tid, "--append-body", "line three\n")
        after = json.loads(run(self.store, "show", tid, "--json"))
        self.assertEqual(after["body"], "line one\nline two\nline three")
        self.assertIn("OK spec_version=2", run(self.store, "lint"))

    def test_edit_append_body_no_double_newline_when_body_ends_with_one(self):
        tid = self.make("appendable", "--body", "line one\n")
        run(self.store, "edit", tid, "--append-body", "line two")
        self.assertEqual(
            json.loads(run(self.store, "show", tid, "--json"))["body"],
            "line one\nline two")

    def test_edit_append_body_to_empty_body_has_no_leading_blank_line(self):
        tid = self.make("appendable")
        run(self.store, "edit", tid, "--append-body", "first")
        self.assertEqual(
            json.loads(run(self.store, "show", tid, "--json"))["body"], "first")

    def test_edit_append_body_with_body_is_refused_and_writes_nothing(self):
        tid = self.make("appendable", "--body", "keep")
        before = json.loads(run(self.store, "show", tid, "--json"))
        run(self.store, "edit", tid, "--append-body", "x", "--body", "y", expect=1)
        self.assertEqual(json.loads(run(self.store, "show", tid, "--json")), before)

    def test_edit_append_body_empty_is_refused(self):
        tid = self.make("appendable", "--body", "keep")
        before = json.loads(run(self.store, "show", tid, "--json"))
        run(self.store, "edit", tid, "--append-body", "", expect=1)
        self.assertEqual(json.loads(run(self.store, "show", tid, "--json")), before)

    def test_edit_append_body_combines_with_priority(self):
        tid = self.make("appendable", "--priority", "3", "--body", "a")
        run(self.store, "edit", tid, "--priority", "P1", "--append-body", "b")
        after = json.loads(run(self.store, "show", tid, "--json"))
        self.assertEqual(after["priority"], 1)
        self.assertEqual(after["body"], "a\nb")
        self.assertEqual([n["text"] for n in after["notes"]],
                         ["edit history: priority was P3",
                          'edit history: body was "a"'])

    def test_create_refuses_title_over_limit_and_writes_nothing(self):
        before = run(self.store, "list", "--json")
        run(self.store, "create", "x" * 201, expect=1)
        self.assertEqual(run(self.store, "list", "--json"), before)

    def test_create_accepts_title_at_limit(self):
        tid = self.make("x" * 200)
        self.assertEqual(len(json.loads(run(self.store, "show", tid, "--json"))["title"]), 200)

    def test_create_refuses_empty_title(self):
        run(self.store, "create", "", expect=1)

    def test_edit_refuses_title_over_limit_and_row_unchanged(self):
        tid = self.make("unchanged")
        before = json.loads(run(self.store, "show", tid, "--json"))
        run(self.store, "edit", tid, "--title", "x" * 201, expect=1)
        self.assertEqual(json.loads(run(self.store, "show", tid, "--json")), before)

    def test_edit_accepts_title_at_limit(self):
        tid = self.make("short")
        run(self.store, "edit", tid, "--title", "y" * 200)
        self.assertEqual(json.loads(run(self.store, "show", tid, "--json"))["title"], "y" * 200)

    def test_close_reason_is_an_alias_for_note(self):
        """fr-cce547: `close --reason` records the same note `--note` would."""
        tid = self.make("close with reason")
        run(self.store, "close", tid, "--reason", "reason text")
        self.assertEqual(
            [n["text"] for n in json.loads(run(self.store, "show", tid, "--json"))["notes"]],
            ["reason text"])

    def test_list_accepts_trailing_repo(self):
        """fr-cce547: `pm ticket list --repo X` (verb-first) resolves the
        same store as `pm ticket --repo X list` (global-first)."""
        tid = self.make("trailing repo")
        out = run(".", "list", "--repo", self.store)
        self.assertIn(tid, out)

    def test_blocks_gates_ready_until_closed(self):
        blocker = self.make("blocker")
        blocked = self.make("blocked")
        run(self.store, "dep", blocker, "blocks", blocked)
        self.assertIn(blocker, self.ready_ids())
        self.assertNotIn(blocked, self.ready_ids())
        # done-unmerged must still block
        run(self.store, "close", blocker, "--unmerged")
        self.assertNotIn(blocked, self.ready_ids())
        run(self.store, "close", blocker)
        self.assertIn(blocked, self.ready_ids())

    def test_claim_lifecycle(self):
        tid = self.make("work")
        run(self.store, "claim", tid, "--as", "agent-a")
        run(self.store, "claim", tid, "--as", "agent-b", expect=1)  # double-claim
        self.assertNotIn(tid, self.ready_ids())
        run(self.store, "release", tid)
        run(self.store, "claim", tid, "--as", "agent-b")
        run(self.store, "close", tid)

    def test_claim_blocked_needs_force(self):
        blocker = self.make("blocker")
        blocked = self.make("blocked")
        run(self.store, "dep", blocker, "blocks", blocked)
        run(self.store, "claim", blocked, "--as", "a", expect=1)
        run(self.store, "claim", blocked, "--as", "a", "--force")

    def test_cycle_refused(self):
        a, b, c = self.make("a"), self.make("b"), self.make("c")
        run(self.store, "dep", a, "blocks", b)
        run(self.store, "dep", b, "blocks", c)
        run(self.store, "dep", c, "blocks", a, expect=1)
        run(self.store, "dep", a, "blocks", a, expect=1)

    def test_epic_parent_and_tree(self):
        epic = self.make("the epic", "--kind", "epic")
        t1 = self.make("child 1", "--parent", epic)
        t2 = self.make("child 2", "--parent", epic)
        run(self.store, "dep", t1, "blocks", t2)
        # epics never appear in ready, cannot be claimed, cannot parent onto a task
        self.assertNotIn(epic, self.ready_ids())
        run(self.store, "claim", epic, "--as", "a", expect=1)
        run(self.store, "create", "bad parent", "--parent", t1, expect=1)
        tree = json.loads(run(self.store, "tree", epic, "--json"))
        self.assertEqual(set(tree["subtree"]), {t1, t2})
        tree = json.loads(run(self.store, "tree", t1, "--json"))
        self.assertEqual(tree["impacts"], [t2])

    def test_discovered_from_and_notes(self):
        origin = self.make("origin work")
        found = self.make("found while working", "--discovered-from", origin)
        t = json.loads(run(self.store, "show", found, "--json"))
        self.assertIn({"type": "discovered-from", "to": origin}, t["edges"])
        run(self.store, "note", found, "handoff: branch pm-pilot, worktree .worktrees/x")
        t = json.loads(run(self.store, "show", found, "--json"))
        self.assertIn("handoff", t["notes"][0]["text"])

    def test_summary_surfaces_semaphores_and_unmerged(self):
        sem = self.make("CRITICAL repo-wide gate", "--priority", "0",
                        "--label", "semaphore")
        gated = self.make("phase-2 work")
        run(self.store, "dep", sem, "blocks", gated)
        done = self.make("optimistic work")
        run(self.store, "close", done, "--unmerged", "--note", "parked on branch x")
        s = json.loads(run(self.store, "summary", "--json"))
        self.assertEqual([t["id"] for t in s["semaphores"]], [sem])
        self.assertEqual([t["id"] for t in s["unmerged"]], [done])
        self.assertNotIn(gated, [t["id"] for t in s["ready"]])

    # --- in-flight holds (fr-d088b2) ---

    def hrun(self, *argv, expect=0, state=None, session="sess-1"):
        """run() with a private hold-state dir and a pinned session id."""
        env = dict(os.environ, PM_SESSION_ID=session, PM_AGENT="claude/test",
                   PM_HOLD_STATE_DIR=state or os.path.join(self.store, "hold-state"))
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=self.store,
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, expect,
                         f"pm ticket {' '.join(argv)}: rc={r.returncode}\n{r.stderr}")
        return r.stdout.strip() if expect == 0 else r.stderr.strip()

    def show(self, tid):
        return json.loads(self.hrun("show", tid, "--json"))

    def test_claim_hold_stores_marker_and_validates(self):
        import hashlib
        tid = self.make("gate")
        self.hrun("claim", tid, "--as", "agent-a", "--hold", "trip in flight")
        t = self.show(tid)
        self.assertEqual(t["status"], "claimed")
        self.assertEqual(t["hold"]["reason"], "trip in flight")
        self.assertEqual(t["hold"]["token"],
                         hashlib.sha256(b"sess-1").hexdigest()[:8])
        self.assertIn("held", self.hrun("summary"))
        self.hrun("validate")

    def test_claim_without_hold_has_no_hold_key(self):
        tid = self.make("plain")
        self.hrun("claim", tid, "--as", "agent-a")
        self.assertNotIn("hold", self.show(tid))

    def test_hold_verb_marks_existing_claim_and_clears(self):
        tid = self.make("gate")
        self.hrun("claim", tid, "--as", "agent-a")
        self.hrun("hold", tid, "waiting on hardware")
        self.assertEqual(self.show(tid)["hold"]["reason"], "waiting on hardware")
        self.hrun("hold", tid, "--clear")
        self.assertNotIn("hold", self.show(tid))
        self.hrun("hold", tid, "--clear", expect=1)

    def test_hold_refuses_unclaimed_foreign_and_reasonless(self):
        tid = self.make("gate")
        self.hrun("hold", tid, "why", expect=1)
        self.hrun("claim", tid, "--as", "agent-a")
        err = self.hrun("hold", tid, "why", expect=1, session="sess-2")
        self.assertIn("not by this session", err)
        self.hrun("hold", tid, expect=1)
        self.hrun("claim", self.make("x"), "--as", "a", "--hold", "  ", expect=1)

    def test_release_close_and_reopen_clear_the_hold(self):
        a, b, c = self.make("a"), self.make("b"), self.make("c")
        self.hrun("claim", a, b, c, "--as", "agent-a", "--hold", "in flight")
        self.hrun("release", a)
        self.hrun("close", b)
        self.hrun("close", c, "--unmerged", "--note", "parked")
        for tid in (a, b, c):
            self.assertNotIn("hold", self.show(tid))
        self.hrun("validate")

    # --- closed_by / released_by (fr-253a2d) ---

    def actor(self, session="sess-1"):
        import hashlib
        return f"agent:claude/test#{hashlib.sha256(session.encode()).hexdigest()[:8]}"

    def test_close_records_closed_by_with_the_claim_identity(self):
        tid = self.make("c")
        self.hrun("claim", tid, "--as", "test")
        claimed = self.show(tid)["assignee"]
        self.hrun("close", tid)
        t = self.show(tid)
        self.assertEqual(t["closed_by"], self.actor())
        self.assertEqual(t["closed_by"], claimed)
        self.assertNotIn("released_by", t)
        self.assertIn(f"closed_by: {self.actor()}", self.hrun("show", tid))
        self.hrun("validate")

    def test_close_session_flag_overrides_env(self):
        tid = self.make("c")
        self.hrun("close", tid, "--session", "sess-9")
        self.assertEqual(self.show(tid)["closed_by"], self.actor("sess-9"))

    def test_close_unmerged_records_closed_by(self):
        tid = self.make("u")
        self.hrun("close", tid, "--unmerged", "--note", "parked")
        t = self.show(tid)
        self.assertEqual((t["status"], t["closed_by"]), ("done-unmerged", self.actor()))
        self.hrun("validate")

    def test_bulk_close_sets_closed_by_on_each_row(self):
        a, b = self.make("a"), self.make("b")
        self.hrun("close", a, b)
        for tid in (a, b):
            self.assertEqual(self.show(tid)["closed_by"], self.actor())

    def test_release_records_released_by_and_claim_close_reopen_clear_it(self):
        a, b = self.make("a"), self.make("b")
        self.hrun("claim", a, b, "--as", "test")
        self.hrun("release", a, b)
        for tid in (a, b):
            t = self.show(tid)
            self.assertEqual((t["status"], t["released_by"]), ("open", self.actor()))
            self.assertNotIn("closed_by", t)
        self.hrun("validate")
        self.hrun("claim", a, "--as", "test")
        self.assertNotIn("released_by", self.show(a))
        self.hrun("close", b)
        t = self.show(b)
        self.assertNotIn("released_by", t)
        self.assertIn("closed_by", t)
        self.hrun("reopen", b)
        t = self.show(b)
        self.assertNotIn("closed_by", t)
        self.assertNotIn("released_by", t)
        self.hrun("claim", b, "--as", "test")
        self.hrun("release", b)
        self.hrun("close", b)
        self.assertNotIn("released_by", self.show(b))

    def test_release_clears_closed_by_and_reopen_clears_it(self):
        tid = self.make("r")
        self.hrun("close", tid)
        self.assertIn("closed_by", self.show(tid))
        self.hrun("reopen", tid)
        self.assertNotIn("closed_by", self.show(tid))
        self.hrun("validate")

    def test_no_session_token_writes_no_key_and_old_rows_validate(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("PM_SESSION_ID", "CLAUDE_CODE_SESSION_ID")}
        old = self.make("old row")
        tid = self.make("anon")
        r = subprocess.run([sys.executable, TICKET_CLI, "close", tid],
                           cwd=self.store, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("closed_by", json.loads(run(self.store, "show", tid, "--json")))
        self.assertNotIn("closed_by", json.loads(run(self.store, "show", old, "--json")))
        self.assertIn("OK", run(self.store, "validate"))

    def test_summary_lists_stale_holds_only_when_session_is_gone(self):
        tid = self.make("gate")
        live = os.path.join(self.store, "state-live")
        self.hrun("claim", tid, "--as", "agent-a", "--hold", "trip", state=live)
        out = self.hrun("summary", state=live)
        self.assertNotIn("stale holds", out)
        gone = os.path.join(self.store, "state-gone")
        out = self.hrun("summary", state=gone)
        self.assertIn("stale holds", out)
        self.assertIn(tid, out.split("stale holds", 1)[1])

    # --- close --findings (fr-05e45a) ---

    def fail(self, *argv):
        r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=self.store,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        return r.stderr

    def test_close_without_findings_leaves_field_absent(self):
        tid = self.make("no attestation")
        run(self.store, "close", tid)
        self.assertNotIn("findings", self.show(tid))

    def test_close_findings_none(self):
        tid = self.make("clean")
        run(self.store, "close", tid, "--findings", "none")
        t = self.show(tid)
        self.assertEqual((t["status"], t["findings"]), ("closed", ["none"]))
        run(self.store, "lint")

    def test_close_findings_valid_ids(self):
        a, b, tid = self.make("a"), self.make("b"), self.make("work")
        run(self.store, "close", tid, "--findings", f"{a},{b},{a}")
        self.assertEqual(self.show(tid)["findings"], [a, b])

    def test_close_findings_unknown_id_writes_nothing(self):
        a, tid = self.make("a"), self.make("work")
        err = self.fail("close", tid, "--findings", f"{a},tt-ffffff")
        self.assertIn("tt-ffffff", err)
        t = self.show(tid)
        self.assertEqual(t["status"], "open")
        self.assertNotIn("findings", t)

    def test_close_findings_cross_store_id_refused(self):
        tid = self.make("work")
        for ref in ("cl/cl-a21900", "cl-a21900"):
            err = self.fail("close", tid, "--findings", ref)
            self.assertIn("no registered store owns prefix 'cl'", err)
        self.assertEqual(self.show(tid)["status"], "open")

    def test_close_findings_none_cannot_mix(self):
        a, tid = self.make("a"), self.make("work")
        self.fail("close", tid, "--findings", f"none,{a}")
        self.fail("close", tid, "--findings", "")
        self.assertEqual(self.show(tid)["status"], "open")

    def test_close_unmerged_with_findings_and_reopen_clears(self):
        a, tid = self.make("a"), self.make("work")
        run(self.store, "close", tid, "--unmerged", "--findings", a, "--note", "parked")
        t = self.show(tid)
        self.assertEqual((t["status"], t["findings"]), ("done-unmerged", [a]))
        run(self.store, "reopen", tid)
        self.assertNotIn("findings", self.show(tid))

    # --- findings_required, phase 1 warn / phase 2 refuse (fr-7e1d26) ---

    def require_findings(self):
        path = os.path.join(self.store, V2_STORE_DIR, "config.json")
        with open(path) as f:
            cfg = json.load(f)
        cfg["findings_required"] = True
        with open(path, "w") as f:
            json.dump(cfg, f)

    def test_phase1_close_without_findings_warns_and_records_absence(self):
        tid = self.make("warned")
        r = subprocess.run([sys.executable, TICKET_CLI, "close", tid], cwd=self.store,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no --findings: this close attests nothing", r.stderr)
        t = self.show(tid)
        self.assertEqual((t["status"], t["findings_absent"]), ("closed", True))
        run(self.store, "lint")
        run(self.store, "reopen", tid)
        self.assertNotIn("findings_absent", self.show(tid))

    def test_phase1_close_with_findings_is_silent(self):
        tid = self.make("attested")
        r = subprocess.run([sys.executable, TICKET_CLI, "close", tid, "--findings", "none"],
                           cwd=self.store, capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertNotIn("findings_absent", self.show(tid))

    def test_phase2_close_without_findings_refuses_and_writes_nothing(self):
        self.require_findings()
        tid = self.make("refused")
        for extra in ((), ("--unmerged",)):
            err = self.fail("close", tid, *extra)
            self.assertIn("pass --findings none or the ids", err)
        self.assertEqual(self.show(tid)["status"], "open")
        run(self.store, "lint")

    def test_phase2_findings_none_needs_a_note(self):
        self.require_findings()
        tid, noted = self.make("bare none"), self.make("noted")
        err = self.fail("close", tid, "--findings", "none")
        self.assertIn("not a default", err)
        self.assertEqual(self.show(tid)["status"], "open")
        run(self.store, "close", tid, "--findings", "none", "--note", "nothing left over")
        self.assertEqual(self.show(tid)["findings"], ["none"])
        run(self.store, "note", noted, "scope was the whole ticket")
        run(self.store, "close", noted, "--findings", "none")
        self.assertEqual(self.show(noted)["findings"], ["none"])

    def test_phase2_findings_ids_close_without_a_note(self):
        self.require_findings()
        a, tid = self.make("a"), self.make("work")
        run(self.store, "close", tid, "--findings", a)
        self.assertEqual(self.show(tid)["findings"], [a])

    def test_missing_store_and_bad_ids(self):
        with tempfile.TemporaryDirectory() as bare:
            run(bare, "ready", expect=1)
            run(bare, "init", "--prefix", "tt")
            run(bare, "show", "tt-nope", expect=1)
            run(bare, "dep", "tt-nope", "blocks", "tt-nada", expect=1)

    def test_init_store_flag_targets_given_root_not_cwd_store(self):
        for flag in ("--store", "--repo"):
            with tempfile.TemporaryDirectory() as tgt:
                out = run(self.store, flag, tgt, "init", "--prefix", "zz")
                self.assertIn(os.path.join(tgt, V2_STORE_DIR), out)
                self.assertTrue(os.path.isfile(os.path.join(tgt, V2_STORE_DIR, V2_TICKET_FILE)))
                with open(os.path.join(self.store, V2_STORE_DIR, "config.json")) as f:
                    self.assertEqual(json.load(f)["prefix"], "tt")
                r = subprocess.run([sys.executable, TICKET_CLI, flag, tgt, "init",
                                    "--prefix", "yy"], cwd=self.store,
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 1)
                self.assertIn(os.path.join(tgt, V2_STORE_DIR), r.stderr)
                self.assertNotIn(os.path.join(self.store, V2_STORE_DIR), r.stderr)

    def test_init_cwd_form_still_works(self):
        with tempfile.TemporaryDirectory() as bare:
            run(bare, "init", "--prefix", "zz")
            self.assertTrue(os.path.isdir(os.path.join(bare, V2_STORE_DIR)))

    def test_jsonl_is_one_line_per_ticket(self):
        for i in range(3):
            self.make(f"ticket {i}")
        path = os.path.join(self.store, V2_STORE_DIR, V2_TICKET_FILE)
        with open(path) as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertTrue(json.loads(line)["id"].startswith("tt-"))


def base_row(**overrides):
    row = {
        "id": "tt-aaaaaa", "title": "a title", "body": "", "kind": "task",
        "status": "open", "priority": 2, "assignee": None, "parent": None,
        "labels": [], "edges": [], "notes": [], "closure_reason": None,
        "created": "2026-01-01T00:00:00Z", "updated": "2026-01-01T00:00:00Z",
    }
    row.update(overrides)
    return row


class ValidateTest(unittest.TestCase):
    """spec/v2: schema_check, Store.validate (I-01..I-19), `pm ticket validate` /
    `pm ticket upgrade` contracts (spec/v2/SPEC.md; spec/v1 SPEC.md sections 5,
    7, 8 for the invariant numbering). `setUp` now gives a fresh spec_version 2
    store (`.pm/tickets.jsonl`, cl-200715); the upgrade/rename tests below
    build their own explicit v1 fixture via `_make_v1_store()`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        run(self.store, "init", "--prefix", "tt")

    def issues_path(self):
        """Row-file path for whatever `config.json` under `.pm/` currently
        declares (ticket_core.ticket_filename: v2+ -> tickets.jsonl, else
        issues.jsonl) -- some tests overwrite `config.json` in place to
        simulate a v0/v1 config without moving the store out of `.pm/`."""
        try:
            with open(self.config_path()) as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            cfg = {}
        sv = cfg.get("spec_version")
        fname = V2_TICKET_FILE if isinstance(sv, int) and sv >= 2 else V1_TICKET_FILE
        return os.path.join(self.store, V2_STORE_DIR, fname)

    def config_path(self):
        return os.path.join(self.store, V2_STORE_DIR, "config.json")

    def write_rows(self, rows):
        # `init` always leaves `tickets.jsonl` (cl-200715); a test that
        # overwrites `config.json` to simulate a v0/v1 config and then
        # writes `issues.jsonl` must not leave that v2 file behind as a
        # stray store entry.
        other = V2_TICKET_FILE if self.issues_path().endswith(V1_TICKET_FILE) \
            else V1_TICKET_FILE
        other_path = os.path.join(self.store, V2_STORE_DIR, other)
        if os.path.exists(other_path):
            os.remove(other_path)
        with open(self.issues_path(), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def invariants_present(self, expect=1):
        data = json.loads(run(self.store, "validate", "--json", expect=expect))
        return {p["invariant"] for p in data["problems"]}, data

    # --- exit codes (SPEC.md section 5) ---

    def test_validate_exit_0_on_clean_store(self):
        run(self.store, "create", "a task")
        out = run(self.store, "validate")
        self.assertTrue(out.startswith("OK spec_version=2"))

    def test_validate_exit_2_on_missing_store(self):
        with tempfile.TemporaryDirectory() as bare:
            r = subprocess.run([sys.executable, TICKET_CLI, "--repo", bare, "validate"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)

    def test_validate_exit_2_on_unparseable_config(self):
        with open(self.config_path(), "w") as f:
            f.write("{not json")
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store, "validate"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("config.json", r.stderr)

    def test_validate_exit_2_on_missing_ticket_file(self):
        """cl-e92e45: the row file is a MUST (SPEC.md section 2); a store
        without it is exit 2 naming the file, not 'OK rows=0'."""
        os.remove(self.issues_path())
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store, "validate"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("tickets.jsonl: file not found", r.stderr)

    def test_validate_exit_1_and_numbered_steps_are_deterministic(self):
        self.write_rows([base_row(title="")])
        out1 = run(self.store, "validate", expect=1)
        out2 = run(self.store, "validate", expect=1)
        self.assertEqual(out1, out2)
        self.assertTrue(out1.splitlines()[0].startswith("FAIL spec_version=2"))
        self.assertTrue(out1.splitlines()[1].startswith("1. "))

    # --- I-01..I-18, each fires once on a targeted fixture ---

    def test_I01_stray_store_entry(self):
        with open(os.path.join(self.store, V2_STORE_DIR, "stray.txt"), "w") as f:
            f.write("junk")
        invs, _ = self.invariants_present()
        self.assertIn("I-01", invs)

    def test_I01_tolerates_tmp_artifacts(self):
        with open(os.path.join(self.store, V2_STORE_DIR, "scratch.tmp"), "w") as f:
            f.write("x")
        out = run(self.store, "validate")
        self.assertTrue(out.startswith("OK"))

    def test_I02_v0_store_is_exactly_one_step(self):
        with open(self.config_path(), "w") as f:
            json.dump({"prefix": "tt", "version": 1}, f)
        data = json.loads(run(self.store, "validate", "--json", expect=1))
        self.assertEqual(len(data["problems"]), 1)
        self.assertEqual(data["problems"][0]["invariant"], "I-02")

    def test_I02_spec_version_mismatch(self):
        with open(self.config_path(), "w") as f:
            json.dump({"prefix": "tt", "spec_version": 2}, f)
        invs, _ = self.invariants_present()
        self.assertIn("I-02", invs)

    def test_I03_id_does_not_carry_prefix(self):
        self.write_rows([base_row(id="zz-aaaaaa")])
        invs, _ = self.invariants_present()
        self.assertIn("I-03", invs)

    def test_I04_schema_violation_extra_key(self):
        row = base_row()
        row["bogus"] = 1
        self.write_rows([row])
        invs, _ = self.invariants_present()
        self.assertIn("I-04", invs)

    def test_I05_duplicate_id(self):
        self.write_rows([base_row(id="tt-aaaaaa"),
                         base_row(id="tt-aaaaaa", title="dup")])
        invs, _ = self.invariants_present()
        self.assertIn("I-05", invs)

    def test_I06_title_too_long(self):
        self.write_rows([base_row(title="x" * 201)])
        data = json.loads(run(self.store, "validate", "--json", expect=1))
        problems = [p for p in data["problems"] if p["invariant"] == "I-06"]
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0]["fix"].startswith("run: pm ticket edit"))
        self.assertTrue(problems[0]["agent_may_fix"])

    def test_I06_title_with_double_quote_is_shell_safe(self):
        self.write_rows([base_row(title='say "hello" ' + "x" * 250)])
        data = json.loads(run(self.store, "validate", "--json", expect=1))
        problems = [p for p in data["problems"] if p["invariant"] == "I-06"]
        self.assertEqual(len(problems), 1)
        fix = problems[0]["fix"]
        self.assertTrue(fix.startswith("run: pm ticket edit"))
        parts = shlex.split(fix[len("run: "):])
        self.assertEqual(parts[0:3], ["pm", "ticket", "edit"])
        self.assertEqual(len(parts), 6)
        self.assertEqual(parts[4], "--title")

    def test_I06_empty_title_is_operator_step_not_invented(self):
        self.write_rows([base_row(title="")])
        data = json.loads(run(self.store, "validate", "--json", expect=1))
        problems = [p for p in data["problems"] if p["invariant"] == "I-06"]
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0]["fix"].startswith("operator:"))
        self.assertNotIn("untitled", problems[0]["fix"])

    def test_I07_task_claimed_without_assignee(self):
        self.write_rows([base_row(status="claimed", assignee=None)])
        invs, _ = self.invariants_present()
        self.assertIn("I-07", invs)

    def test_I07_task_assignee_without_claimed(self):
        self.write_rows([base_row(status="open", assignee="someone")])
        invs, _ = self.invariants_present()
        self.assertIn("I-07", invs)

    def test_I08_epic_claimed(self):
        self.write_rows([base_row(kind="epic", status="claimed", assignee="a")])
        invs, _ = self.invariants_present()
        self.assertIn("I-08", invs)

    def test_I09_parent_missing(self):
        self.write_rows([base_row(parent="tt-abcdef")])
        invs, _ = self.invariants_present()
        self.assertIn("I-09", invs)

    def test_I09_parent_not_epic(self):
        self.write_rows([base_row(id="tt-aaaaaa"),
                         base_row(id="tt-bbbbbb", parent="tt-aaaaaa")])
        invs, _ = self.invariants_present()
        self.assertIn("I-09", invs)

    def test_I09_parent_cycle(self):
        self.write_rows([
            base_row(id="tt-aaaaaa", kind="epic", parent="tt-bbbbbb"),
            base_row(id="tt-bbbbbb", kind="epic", parent="tt-aaaaaa"),
        ])
        invs, _ = self.invariants_present()
        self.assertIn("I-09", invs)

    def test_I10_labels_not_sorted(self):
        self.write_rows([base_row(labels=["b", "a"])])
        data = json.loads(run(self.store, "validate", "--json", expect=1))
        problems = [p for p in data["problems"] if p["invariant"] == "I-10"]
        self.assertEqual(len(problems), 1)

    def test_I10_invalid_label(self):
        self.write_rows([base_row(labels=["Bad Label"])])
        data = json.loads(run(self.store, "validate", "--json", expect=1))
        problems = [p for p in data["problems"] if p["invariant"] == "I-10"]
        self.assertEqual(len(problems), 1)
        self.assertFalse(problems[0]["agent_may_fix"])

    def test_create_refuses_an_invalid_label_and_writes_nothing(self):
        """fr-3fc528: create checks the label pattern validate enforces."""
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store, "create",
                            "label probe", "--label", "initiative:I1"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not match", r.stderr)
        with open(self.issues_path()) as f:
            self.assertEqual(f.read(), "")

    def test_I11_edge_to_missing(self):
        self.write_rows([base_row(edges=[{"type": "blocks", "to": "tt-abcdef"}])])
        invs, _ = self.invariants_present()
        self.assertIn("I-11", invs)

    def test_I12_self_edge(self):
        self.write_rows([base_row(edges=[{"type": "related", "to": "tt-aaaaaa"}])])
        data = json.loads(run(self.store, "validate", "--json", expect=1))
        problems = [p for p in data["problems"] if p["invariant"] == "I-12"]
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]["fix"], "run: pm ticket unlink tt-aaaaaa tt-aaaaaa")

    def test_I13_blocks_cycle(self):
        self.write_rows([
            base_row(id="tt-aaaaaa", edges=[{"type": "blocks", "to": "tt-bbbbbb"}]),
            base_row(id="tt-bbbbbb", edges=[{"type": "blocks", "to": "tt-aaaaaa"}]),
        ])
        invs, _ = self.invariants_present()
        self.assertIn("I-13", invs)

    def test_I14_notes_out_of_order(self):
        self.write_rows([base_row(notes=[
            {"ts": "2026-01-02T00:00:00Z", "text": "later"},
            {"ts": "2026-01-01T00:00:00Z", "text": "earlier"},
        ])])
        invs, _ = self.invariants_present()
        self.assertIn("I-14", invs)

    def test_I15_updated_precedes_created(self):
        self.write_rows([base_row(created="2026-01-02T00:00:00Z",
                                  updated="2026-01-01T00:00:00Z")])
        invs, _ = self.invariants_present()
        self.assertIn("I-15", invs)

    def test_I16_archive_index_bad_shape(self):
        archive_dir = os.path.join(self.store, V2_STORE_DIR, "archive")
        os.makedirs(archive_dir)
        with open(os.path.join(archive_dir, "archive-index.jsonl"), "w") as f:
            f.write(json.dumps({"id": "tt-x", "title": "t"}) + "\n")
        invs, _ = self.invariants_present()
        self.assertIn("I-16", invs)

    def test_I17_archived_row_not_closed(self):
        archive_dir = os.path.join(self.store, V2_STORE_DIR, "archive")
        os.makedirs(archive_dir)
        with open(os.path.join(archive_dir, "tickets-2026.jsonl"), "w") as f:
            f.write(json.dumps(base_row(status="open")) + "\n")
        invs, _ = self.invariants_present()
        self.assertIn("I-17", invs)

    def test_I18_v1_archive_name_in_v2_store(self):
        archive_dir = os.path.join(self.store, V2_STORE_DIR, "archive")
        os.makedirs(archive_dir)
        with open(os.path.join(archive_dir, "issues-2026.jsonl"), "w") as f:
            f.write(json.dumps(base_row(status="closed")) + "\n")
        invs, _ = self.invariants_present()
        self.assertIn("I-18", invs)

    def test_I18_stray_archive_entry(self):
        archive_dir = os.path.join(self.store, V2_STORE_DIR, "archive")
        os.makedirs(archive_dir)
        with open(os.path.join(archive_dir, "junk.txt"), "w") as f:
            f.write("x")
        invs, _ = self.invariants_present()
        self.assertIn("I-18", invs)

    def test_archive_missing_bytes_is_not_a_problem(self):
        """R2 amendment: an index row whose path does not resolve is fine on
        a fresh clone -- only shape (I-16..I-18) is checked."""
        archive_dir = os.path.join(self.store, V2_STORE_DIR, "archive")
        os.makedirs(archive_dir)
        with open(os.path.join(archive_dir, "archive-index.jsonl"), "w") as f:
            f.write(json.dumps({
                "id": "tt-gone", "title": "gone", "source": "self", "closed": None,
                "path": "tickets-2020.jsonl", "archived": "2026-01-01T00:00:00Z",
                "meta": {},
            }) + "\n")
        out = run(self.store, "validate")
        self.assertTrue(out.startswith("OK"))

    # --- mechanical fixes agents may run straight from step text (F6) ---

    def test_mechanical_fixes_resolve_their_invariant(self):
        self.write_rows([base_row(status="claimed", assignee=None,
                                  edges=[{"type": "blocks", "to": "tt-aaaaaa"}])])
        run(self.store, "release", "tt-aaaaaa")
        run(self.store, "unlink", "tt-aaaaaa", "tt-aaaaaa")
        out = run(self.store, "validate")
        self.assertTrue(out.startswith("OK"))

    def test_release_also_fixes_stray_assignee_not_claimed(self):
        self.write_rows([base_row(status="open", assignee="someone")])
        run(self.store, "release", "tt-aaaaaa")
        out = run(self.store, "validate")
        self.assertTrue(out.startswith("OK"))

    def test_release_of_stray_assignee_keeps_a_closed_epic_closed(self):
        """cl-603745: I-08's fix (`release`) on a CLOSED epic with a stray
        assignee clears the assignee and does not reopen the epic."""
        self.write_rows([base_row(kind="epic", status="closed", assignee="human:stray")])
        run(self.store, "release", "tt-aaaaaa")
        row = json.loads(run(self.store, "show", "tt-aaaaaa", "--json"))
        self.assertEqual((row["status"], row["assignee"]), ("closed", None))
        self.assertTrue(run(self.store, "validate").startswith("OK"))

    # --- workspace fan-out (SPEC.md section 8) ---

    def test_workspace_fanout_with_trailing_comma_file(self):
        with tempfile.TemporaryDirectory() as ws_root:
            for name, prefix in (("repoa", "wa"), ("repob", "wb")):
                d = os.path.join(ws_root, name)
                os.makedirs(os.path.join(d, ".git"))
                run(d, "init", "--prefix", prefix, "--dir", d)
            ws_file = os.path.join(ws_root, "x.code-workspace")
            with open(ws_file, "w") as f:
                f.write('{\n  // a comment\n  "folders": [\n    {"path": "repoa"},\n'
                       '    {"path": "repob"},\n  ],\n}\n')
            r = subprocess.run([sys.executable, TICKET_CLI, "validate", "--workspace", ws_file],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("repoa", r.stdout)
            self.assertIn("repob", r.stdout)

    def test_workspace_fanout_detects_duplicate_prefix(self):
        with tempfile.TemporaryDirectory() as ws_root:
            for name in ("repoa", "repob"):
                d = os.path.join(ws_root, name)
                os.makedirs(os.path.join(d, ".git"))
                run(d, "init", "--prefix", "dup", "--dir", d)
            ws_file = os.path.join(ws_root, "x.code-workspace")
            with open(ws_file, "w") as f:
                json.dump({"folders": [{"path": "repoa"}, {"path": "repob"}]}, f)
            r = subprocess.run([sys.executable, TICKET_CLI, "validate", "--workspace", ws_file],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("prefix dup used by", r.stdout)

    def test_workspace_json_is_one_parseable_document(self):
        """cl-87442e: --workspace --json prints one object (repos + workspace
        problems), not '== repo ==' headers between per-repo documents."""
        with tempfile.TemporaryDirectory() as ws_root:
            for name in ("repoa", "repob"):
                d = os.path.join(ws_root, name)
                os.makedirs(os.path.join(d, ".git"))
                run(d, "init", "--prefix", "dup", "--dir", d)
            ws_file = os.path.join(ws_root, "x.code-workspace")
            with open(ws_file, "w") as f:
                json.dump({"folders": [{"path": "repoa"}, {"path": "repob"}]}, f)
            r = subprocess.run([sys.executable, TICKET_CLI, "validate", "--workspace",
                                ws_file, "--json"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            doc = json.loads(r.stdout)
            self.assertFalse(doc["ok"])
            self.assertEqual([os.path.basename(x["repo"]) for x in doc["repos"]],
                             ["repoa", "repob"])
            self.assertTrue(all(x["ok"] and x["spec_version"] == 2 for x in doc["repos"]))
            self.assertEqual([p["invariant"] for p in doc["workspace"]], ["W-01"])

    def test_validate_json_without_a_store_prints_json(self):
        """cl-87442e: no store + --json -> exit 2 and a JSON object on stdout
        (ok false, the error), not an empty stdout."""
        with tempfile.TemporaryDirectory() as bare:
            os.makedirs(os.path.join(bare, ".git"))
            r = subprocess.run([sys.executable, TICKET_CLI, "--store", bare, "validate",
                                "--json"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            doc = json.loads(r.stdout)
            self.assertEqual((doc["ok"], doc["spec_version"], doc["problems"], doc["path"]),
                             (False, None, [], None))
            self.assertIn("no ticket store found", doc["error"])
            r = subprocess.run([sys.executable, TICKET_CLI, "--store", bare, "validate"],
                               capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stdout), (2, ""))
            self.assertEqual(r.stderr.strip(), "pm: no ticket store found (run: pm ticket init)")

    # --- find_store git boundary (SPEC.md section 2, R1) ---

    def test_find_store_stops_at_git_boundary(self):
        nested = os.path.join(self.store, "nested")
        os.makedirs(os.path.join(nested, ".git"))
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", nested, "ready"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no ticket store found", r.stderr)

    # --- archive verb (SPEC.md section 10 / R7) ---

    def test_archive_moves_old_closed_rows(self):
        run(self.store, "create", "keep me")
        gone = run(self.store, "create", "archive me")
        run(self.store, "close", gone)
        # backdate it past the cutoff
        with open(self.issues_path()) as f:
            rows = [json.loads(l) for l in f if l.strip()]
        for r in rows:
            if r["id"] == gone:
                r["updated"] = "2020-01-01T00:00:00Z"
        self.write_rows(rows)
        run(self.store, "archive", "--closed-before", "2099-01-01", "--dry-run")
        run(self.store, "archive", "--closed-before", "2099-01-01")
        out = run(self.store, "validate")
        self.assertTrue(out.startswith("OK"))
        with open(self.issues_path()) as f:
            remaining = [json.loads(l)["id"] for l in f if l.strip()]
        self.assertNotIn(gone, remaining)
        index_path = os.path.join(self.store, V2_STORE_DIR, "archive", "archive-index.jsonl")
        with open(index_path) as f:
            index_ids = [json.loads(l)["id"] for l in f if l.strip()]
        self.assertIn(gone, index_ids)

    def ids_in_store(self):
        with open(self.issues_path()) as f:
            return [json.loads(l)["id"] for l in f if l.strip()]

    def archive_index_ids(self):
        path = os.path.join(self.store, V2_STORE_DIR, "archive", "archive-index.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(l)["id"] for l in f if l.strip()]

    def closed_pair(self):
        a, b = run(self.store, "create", "a"), run(self.store, "create", "b")
        for t in (a, b):
            run(self.store, "claim", t, "--as", "x")
            run(self.store, "close", t)
        return a, b

    def test_archive_by_id_moves_only_those_rows(self):
        a, b = self.closed_pair()
        run(self.store, "archive", a)
        self.assertNotIn(a, self.ids_in_store())
        self.assertIn(b, self.ids_in_store())
        self.assertEqual(self.archive_index_ids(), [a])
        self.assertTrue(run(self.store, "validate").startswith("OK"))

    def test_archive_on_v2_store_writes_tickets_year_file(self):
        a, _ = self.closed_pair()
        run(self.store, "archive", a)
        archive_dir = os.path.join(self.store, V2_STORE_DIR, "archive")
        year = [n for n in os.listdir(archive_dir) if n != "archive-index.jsonl"]
        self.assertEqual(len(year), 1)
        self.assertRegex(year[0], r"^tickets-[0-9]{4}\.jsonl$")
        with open(os.path.join(archive_dir, "archive-index.jsonl")) as f:
            self.assertEqual([json.loads(l)["path"] for l in f if l.strip()], year)
        self.assertTrue(run(self.store, "validate").startswith("OK"))

    def test_archive_year_filename_follows_spec_version(self):
        sys.path.insert(0, os.path.join(os.path.dirname(TICKET_CLI)))
        import ticket_core
        self.assertEqual(ticket_core.archive_year_filename(1, "2026"), "issues-2026.jsonl")
        self.assertEqual(ticket_core.archive_year_filename(None, "2026"), "issues-2026.jsonl")
        self.assertEqual(ticket_core.archive_year_filename(2, "2026"), "tickets-2026.jsonl")

    def test_archive_by_id_dry_run_moves_nothing(self):
        a, _ = self.closed_pair()
        self.assertIn(f"would archive {a}", run(self.store, "archive", a, "--dry-run"))
        self.assertIn(a, self.ids_in_store())
        self.assertEqual(self.archive_index_ids(), [])

    def test_archive_refuses_open_row_naming_close_and_moves_nothing(self):
        a, _ = self.closed_pair()
        live = run(self.store, "create", "still open")
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store,
                            "archive", a, live], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"pm ticket close {live}", r.stderr)
        self.assertIn(a, self.ids_in_store())
        self.assertEqual(self.archive_index_ids(), [])

    def test_archive_refuses_unknown_id_and_moves_nothing(self):
        a, _ = self.closed_pair()
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store,
                            "archive", a, "zz-000000"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("zz-000000: unknown ticket", r.stderr)
        self.assertIn(a, self.ids_in_store())

    def test_archive_without_ids_or_date_is_refused(self):
        self.closed_pair()
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store, "archive"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ticket ids", r.stderr)

    def test_archive_ids_with_date_filter_refuses_row_after_cutoff(self):
        a, _ = self.closed_pair()
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store, "archive",
                            a, "--closed-before", "2000-01-01"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not before 2000-01-01", r.stderr)
        self.assertIn(a, self.ids_in_store())
        run(self.store, "archive", a, "--closed-before", "2999-01-01")
        self.assertNotIn(a, self.ids_in_store())

    def closed_epic_with_child(self, close_child):
        e = run(self.store, "create", "epic", "--kind", "epic")
        c = run(self.store, "create", "child", "--parent", e)
        if close_child:
            run(self.store, "claim", c, "--as", "x")
            run(self.store, "close", c)
        run(self.store, "close", e, *([] if close_child else ["--force", "--findings", "none"]))
        return e, c

    def test_archive_by_id_refuses_parent_of_live_child(self):
        e, c = self.closed_epic_with_child(False)
        r = subprocess.run([sys.executable, TICKET_CLI, "--repo", self.store,
                            "archive", e], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"{e} is parent of live {c}", r.stderr)
        self.assertIn(e, self.ids_in_store())
        self.assertEqual(self.archive_index_ids(), [])
        self.assertTrue(run(self.store, "validate").startswith("OK"))

    def test_archive_parent_and_child_together_succeeds(self):
        e, c = self.closed_epic_with_child(True)
        run(self.store, "archive", e, c)
        self.assertEqual(sorted(self.archive_index_ids()), sorted([e, c]))
        self.assertTrue(run(self.store, "validate").startswith("OK"))

    def test_archive_bulk_skips_parent_of_live_child(self):
        e, c = self.closed_epic_with_child(False)
        a, b = self.closed_pair()
        out = run(self.store, "archive", "--closed-before", "2999-01-01")
        self.assertIn(f"skipped {e}: is parent of live {c}", out)
        self.assertIn(e, self.ids_in_store())
        self.assertEqual(sorted(self.archive_index_ids()), sorted([a, b]))
        self.assertTrue(run(self.store, "validate").startswith("OK"))

    def test_summary_hint_points_at_ids_not_a_required_date(self):
        big = run(self.store, "create", "old")
        run(self.store, "claim", big, "--as", "x")
        run(self.store, "close", big)
        with open(self.issues_path()) as f:
            rows = [json.loads(l) for l in f if l.strip()]
        for r in rows:
            r["updated"] = "2020-01-01T00:00:00Z"
        self.write_rows(rows)
        out = run(self.store, "summary")
        self.assertIn("pm ticket archive <id>", out)
        self.assertNotIn("--closed-before", out)


class AutoCommitTest(unittest.TestCase):
    """cl-865b04: every mutating op commits the v1 store's ticket file, and only
    that path, in the repo that owns the store. Tests run git with an
    isolated identity and signing off so they never touch the caller's key."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        with open(os.path.join(self.repo, "README"), "w") as f:
            f.write("x\n")
        self.git("add", "README")
        self.git("commit", "-q", "-m", "seed")
        run(self.repo, "init", "--prefix", "tt")

    def git(self, *argv, cwd=None):
        r = subprocess.run(["git", "-C", cwd or self.repo, *argv],
                           capture_output=True, text=True)
        assert r.returncode == 0, f"git {' '.join(argv)}: {r.stderr}"
        return r.stdout.strip()

    def cli(self, *argv, cwd=None):
        r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=cwd or self.repo,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip(), r.stderr.strip()

    def head_files(self):
        return self.git("show", "--name-only", "--format=", "HEAD").splitlines()

    def _fake_deploy(self, rc):
        """An executable bin/deploy that logs its argv and exits `rc`."""
        os.makedirs(os.path.join(self.repo, "bin"), exist_ok=True)
        path = os.path.join(self.repo, "bin", "deploy")
        log = os.path.join(self.repo, "deploy-calls.log")
        with open(path, "w") as f:
            f.write("#!/usr/bin/env python3\nimport sys\n"
                    f"open({log!r}, 'a').write(' '.join(sys.argv[1:]) + '\\n')\n"
                    "print('STALE tool-x [claude]: bin/tool (source changed)')\n"
                    f"sys.exit({rc})\n")
        os.chmod(path, 0o755)
        return log

    def _tooling_ticket_with_commit(self, labels=("tooling",)):
        argv = ["create", "gate probe"]
        for lbl in labels:
            argv += ["--label", lbl]
        tid, _ = self.cli(*argv)
        os.makedirs(os.path.join(self.repo, "tool"), exist_ok=True)
        with open(os.path.join(self.repo, "tool", "x.py"), "w") as f:
            f.write(f"x = {tid!r}\n")
        self.git("add", "tool/x.py")
        self.git("commit", "-q", "-m", f"{tid}: change the tool")
        return tid

    def close(self, *argv):
        return subprocess.run([sys.executable, TICKET_CLI, "close", *argv],
                              cwd=self.repo, capture_output=True, text=True)

    def test_close_refuses_a_tooling_ticket_whose_deploy_is_not_current(self):
        """fr-2aed04: exit 4, nothing closed, deploy's lines relayed; the
        check is given exactly the files of the ticket's `<id>:` commits."""
        log = self._fake_deploy(1)
        tid = self._tooling_ticket_with_commit()
        r = self.close(tid, "--findings", "none", "--note", "n")
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn("STALE tool-x [claude]", r.stderr)
        self.assertIn("--no-deploy-check", r.stderr)
        with open(log) as f:
            self.assertEqual(f.read(), "close-check tool/x.py\n")
        show = json.loads(self.cli("show", tid, "--json")[0])
        self.assertEqual(show["status"], "open")

    def test_close_passes_when_deploy_is_current(self):
        self._fake_deploy(0)
        tid = self._tooling_ticket_with_commit()
        r = self.close(tid, "--findings", "none", "--note", "n")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_deploy_check_closes_and_records_the_reason(self):
        self._fake_deploy(1)
        tid = self._tooling_ticket_with_commit()
        r = self.close(tid, "--findings", "none", "--note", "n",
                       "--no-deploy-check", "deploy runs from main later")
        self.assertEqual(r.returncode, 0, r.stderr)
        show = json.loads(self.cli("show", tid, "--json")[0])
        self.assertEqual(show["status"], "closed")
        self.assertIn("deploy check skipped: deploy runs from main later",
                      [n["text"] for n in show["notes"]])

    def test_deploy_check_skips_unlabelled_unmerged_and_repos_without_bin_deploy(self):
        tid = self._tooling_ticket_with_commit()
        self.assertEqual(self.close(tid, "--findings", "none", "--note", "n").returncode, 0)
        log = self._fake_deploy(1)
        plain = self._tooling_ticket_with_commit(labels=())
        self.assertEqual(self.close(plain, "--findings", "none", "--note", "n").returncode, 0)
        parked = self._tooling_ticket_with_commit()
        r = self.close(parked, "--unmerged", "--findings", "none", "--note", "n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(log))

    def test_first_op_commits_the_untracked_config_with_the_row_file(self):
        """fr-eb0ef5: the first store commit after `init` carries config.json
        too, so a later `git clean -fd` cannot delete it; later ops commit the
        row file alone."""
        tid, _ = self.cli("create", "first")
        self.assertEqual(sorted(self.head_files()), [".pm/config.json", V2_TICKET_PATH])
        self.git("clean", "-fdq")
        self.assertTrue(os.path.exists(os.path.join(self.repo, ".pm", "config.json")))
        self.cli("close", tid)
        self.assertEqual(self.head_files(), [V2_TICKET_PATH])

    def test_each_op_commits_only_the_store_file(self):
        with open(os.path.join(self.repo, "other.txt"), "w") as f:
            f.write("dirty\n")
        self.git("add", "other.txt")
        tid, err = self.cli("create", "auto")
        self.assertEqual(err, "")
        # the first op also carries the fresh init's config.json (fr-eb0ef5)
        self.assertEqual(sorted(self.head_files()), [".pm/config.json", V2_TICKET_PATH])
        self.assertEqual(self.git("log", "-1", "--format=%s"), f"pm: create {tid}")
        self.assertEqual(self.git("status", "--porcelain", "--", "other.txt"),
                         "A  other.txt")
        self.cli("claim", tid, "--as", "a")
        self.cli("close", tid)
        self.assertEqual(self.git("log", "-1", "--format=%s"), f"pm: close {tid}")
        self.assertEqual(self.git("status", "--porcelain", "--",
                                  V2_TICKET_PATH), "")
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "4")

    def test_no_op_mutation_does_not_commit(self):
        self.cli("create", "still open")
        before = self.git("rev-parse", "HEAD")
        _, err = self.cli("archive", "--closed-before", "2000-01-01")
        self.assertEqual(err, "")
        self.assertEqual(self.git("rev-parse", "HEAD"), before)

    def test_commit_failure_exits_nonzero_and_keeps_the_row(self):
        # cl-21c3ae: a real git-commit failure is loud (exit 3), not a
        # silently-swallowed stderr line -- but the row is still saved.
        self.git("config", "core.hooksPath", ".githooks")
        os.makedirs(os.path.join(self.repo, ".githooks"))
        hook = os.path.join(self.repo, ".githooks", "pre-commit")
        with open(hook, "w") as f:
            f.write("#!/bin/sh\necho refused >&2\nexit 1\n")
        os.chmod(hook, 0o755)
        before = self.git("rev-parse", "HEAD")
        # Not self.cli() (asserts returncode == 0) -- this op is expected to
        # exit non-zero. TICKET_CLI already honors PM_CLI_UNDER_TEST (module level).
        r = subprocess.run([sys.executable, TICKET_CLI, "create", "row survives"],
                           cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(r.returncode, 3)
        err = r.stderr
        self.assertIn("commit skipped", err)
        self.assertIn("refused", err)
        self.assertIn("commit it by hand", err)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        with open(os.path.join(self.repo, V2_STORE_DIR, V2_TICKET_FILE)) as f:
            self.assertIn("row survives", f.read())

    def test_off_default_branch_saves_but_skips(self):
        self.git("checkout", "-q", "-b", "feature")
        before = self.git("rev-parse", "HEAD")
        tid, err = self.cli("create", "on feature")
        self.assertIn("cl-111ef6", err)
        # the skip line names BOTH the current branch and the default branch
        # so the reason is legible without any agent reasoning (cl-111ef6).
        self.assertIn("on feature", err)
        self.assertIn("not main", err)
        # fr-4c8a0e: a policy skip (not just a GitFault) also prints the
        # exact by-hand commit command so the row is never silently stranded.
        self.assertIn("commit it by hand", err)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.git("checkout", "-q", "main")
        # back on main the next op sweeps the still-dirty file in one commit
        tid2, err = self.cli("create", "on main")
        self.assertEqual(err, "")
        self.assertEqual(self.git("log", "-1", "--format=%s"), f"pm: create {tid2}")
        self.assertEqual(self.git("status", "--porcelain", "--",
                                  V2_TICKET_PATH), "")

    def test_foreign_repo_target_commits_in_the_target_repo(self):
        # fr-4c8a0e: a --repo mutation into another repo's store commits
        # there exactly like an in-repo session would -- the command is
        # always scoped to the store's own repo (git -C <target> commit -o),
        # so cwd being elsewhere grants the skip nothing to protect.
        with tempfile.TemporaryDirectory() as elsewhere:
            before = self.git("rev-parse", "HEAD")
            tid, err = self.cli("--repo", self.repo, "create", "from elsewhere",
                               cwd=elsewhere)
            self.assertEqual(err, "")
            self.assertNotEqual(self.git("rev-parse", "HEAD"), before)
            self.assertEqual(self.git("log", "-1", "--format=%s"),
                             f"pm: create {tid}")
            # first op after init: the untracked config.json rides along (fr-eb0ef5)
            self.assertEqual(sorted(self.head_files()), [".pm/config.json", V2_TICKET_PATH])
            self.assertEqual(
                self.git("status", "--porcelain", "--", V2_TICKET_PATH), "")
            with open(os.path.join(self.repo, V2_STORE_DIR, V2_TICKET_FILE)) as f:
                ids = [json.loads(l)["id"] for l in f if l.strip()]
            self.assertIn(tid, ids)
        _, err = self.cli("--repo", self.repo, "note", tid, "same repo")
        self.assertEqual(err, "")
        self.assertEqual(self.git("log", "-1", "--format=%s"), f"pm: note {tid}")

    def test_summary_surfaces_dirty_store_and_hides_when_clean(self):
        # a committed store on the default branch: summary shows no note.
        self.cli("create", "seed")
        out, _ = self.cli("summary")
        self.assertNotIn("uncommitted", out)
        # an off-branch op modifies the tracked store but skips the commit;
        # summary now surfaces that skipped state without any agent reasoning.
        self.git("checkout", "-q", "-b", "feature")
        self.cli("create", "on feature")
        out, _ = self.cli("summary")
        self.assertIn("uncommitted", out)
        # back on the default branch the next op sweeps it in; note disappears.
        self.git("checkout", "-q", "main")
        self.cli("create", "on main")
        out, _ = self.cli("summary")
        self.assertNotIn("uncommitted", out)

    def test_store_outside_git_is_untouched(self):
        with tempfile.TemporaryDirectory() as plain:
            run(plain, "init", "--prefix", "pp")
            r = subprocess.run([sys.executable, TICKET_CLI, "create", "no git"], cwd=plain,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stderr, "")


class WorktreeStoreTest(unittest.TestCase):
    """cl-867194: a pm ticket op run inside a linked git worktree resolves its store
    to the MAIN checkout. The worktree's own v1 store directory copy is never read,
    locked, or committed, and the commit lands on the main checkout's default
    branch (so the cl-111ef6 off-branch skip no longer fires for worktrees).
    Git runs with an isolated identity and signing off, like AutoCommitTest."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        with open(os.path.join(self.repo, "README"), "w") as f:
            f.write("x\n")
        self.git("add", "README")
        self.git("commit", "-q", "-m", "seed")
        run(self.repo, "init", "--prefix", "tt")
        # a first row committed on main so the worktree checks out a real copy
        # of the v1 store's ticket file — the copy we prove is never touched.
        self.seed_tid = run(self.repo, "create", "seed row")
        self.wt = os.path.join(self.repo, ".worktrees", "cl-x")
        self.git("worktree", "add", "-q", self.wt, "-b", "cl-x")
        # sanity: the worktree really did check out its own store copy
        assert os.path.exists(os.path.join(self.wt, V2_STORE_DIR, V2_TICKET_FILE))

    def git(self, *argv, cwd=None):
        r = subprocess.run(["git", "-C", cwd or self.repo, *argv],
                           capture_output=True, text=True)
        assert r.returncode == 0, f"git {' '.join(argv)}: {r.stderr}"
        return r.stdout.strip()

    def cli(self, *argv, cwd=None):
        r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=cwd or self.repo,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip(), r.stderr.strip()

    def main_ids(self):
        p = os.path.join(self.repo, V2_STORE_DIR, V2_TICKET_FILE)
        with open(p) as f:
            return [json.loads(l)["id"] for l in f if l.strip()]

    def test_run_from_worktree_lands_in_main_store_and_commits_on_main(self):
        wt_store = os.path.join(self.wt, V2_STORE_DIR, V2_TICKET_FILE)
        with open(wt_store, "rb") as f:
            wt_before = f.read()
        before_main = self.git("rev-parse", "main")
        tid, err = self.cli("create", "from worktree", cwd=self.wt)
        # not skipped as off-branch: find_store resolved sideways to main
        self.assertEqual(err, "")
        # (a) the row landed in the MAIN checkout's store, beside the seed row
        ids = self.main_ids()
        self.assertIn(tid, ids)
        self.assertIn(self.seed_tid, ids)
        # (a) committed on the MAIN checkout's default branch, advancing it once
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual(self.git("log", "-1", "--format=%s"),
                         f"pm: create {tid}")
        self.assertEqual(self.git("rev-list", "--count",
                                  f"{before_main}..main"), "1")
        self.assertEqual(self.git("status", "--porcelain", "--",
                                  V2_TICKET_PATH), "")
        # (b) the worktree's own v1 store ticket file is byte-unchanged
        with open(wt_store, "rb") as f:
            self.assertEqual(f.read(), wt_before)

    def test_lock_taken_is_the_main_checkout_lock(self):
        # (c) hold the MAIN checkout's flock; a pm ticket op from the worktree must
        # block on it (times out), proving it is the main lock — not sleep.
        main_lock = os.path.join(self.repo, V2_STORE_DIR, "lock")
        lk = open(main_lock, "w")
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            with self.assertRaises(subprocess.TimeoutExpired):
                subprocess.run([sys.executable, TICKET_CLI, "create", "blocked"],
                               cwd=self.wt, capture_output=True, text=True,
                               timeout=5)
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)
            lk.close()
        # lock released -> the same op now completes into the main store
        tid, err = self.cli("create", "unblocked", cwd=self.wt)
        self.assertEqual(err, "")
        self.assertIn(tid, self.main_ids())


class HistoryCliTest(unittest.TestCase):
    """fr-4cc7ec: `history_ref` keeps ticket history on refs/heads/pm-store,
    never on main; `pm ticket history` moves a store in and out."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        with open(os.path.join(self.repo, "README"), "w") as f:
            f.write("x\n")
        self.git("add", "README")
        self.git("commit", "-q", "-m", "seed")
        run(self.repo, "init", "--prefix", "tt")
        self.seed_tid = run(self.repo, "create", "before history")
        self.git("add", ".gitignore", ".pm/config.json")
        self.git("commit", "-q", "-m", "track config")
        self.path = os.path.join(self.repo, V2_TICKET_PATH)

    def git(self, *argv, rc=0):
        r = subprocess.run(["git", "-C", self.repo, *argv], capture_output=True, text=True)
        assert r.returncode == rc, f"git {' '.join(argv)}: {r.stderr}"
        return r.stdout.strip()

    def cli(self, *argv, rc=0):
        r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=self.repo,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, rc, r.stderr)
        return r.stdout.strip(), r.stderr.strip()

    def main_count(self):
        return int(self.git("rev-list", "--count", "main"))

    def store_count(self):
        return int(self.git("rev-list", "--count", "refs/heads/pm-store"))

    def test_enable_then_create_claim_close_adds_nothing_to_main(self):
        out, _ = self.cli("history", "enable")
        self.assertEqual(out, f"OK: {self.repo} ticket history on refs/heads/pm-store")
        self.assertEqual(self.cli("history", "status")[0], "on")
        self.cli("validate")
        self.assertEqual(self.git("ls-files", "--", V2_TICKET_PATH), "")
        self.git("check-ignore", "-q", V2_TICKET_PATH)
        main_before, store_before = self.main_count(), self.store_count()
        tid, _ = self.cli("create", "after history")
        self.cli("claim", tid, "--as", "a")
        self.cli("close", tid)
        self.assertEqual(self.main_count(), main_before)
        self.assertEqual(self.store_count(), store_before + 3)
        self.assertEqual(self.git("diff", "--cached"), "")
        self.assertEqual(self.git("log", "-1", "--format=%s", "refs/heads/pm-store"),
                         f"pm: close {tid}")
        with open(self.path) as f:
            self.assertEqual(self.git("show", "refs/heads/pm-store:tickets.jsonl"),
                             f.read().strip())

    def test_no_op_verb_adds_no_commit(self):
        self.cli("history", "enable")
        self.cli("create", "still open")
        before = self.store_count()
        self.cli("archive", "--closed-before", "2000-01-01")
        self.assertEqual(self.store_count(), before)

    def test_ref_update_failure_exits_0_marks_pending_and_next_write_catches_up(self):
        self.cli("history", "enable")
        hook = os.path.join(self.repo, ".git", "hooks", "reference-transaction")
        with open(hook, "w") as f:
            f.write("#!/bin/sh\nif [ \"$1\" = prepared ] && cat | grep -q "
                    "refs/heads/pm-store; then echo 'ref refused' >&2; exit 1; fi\n")
        os.chmod(hook, 0o755)
        tip = self.git("rev-parse", "refs/heads/pm-store")
        main_tip = self.git("rev-parse", "main")
        pending = os.path.join(self.repo, V2_STORE_DIR, "history-pending")
        _, err = self.cli("create", "row survives")
        self.assertIn("commit skipped", err)
        self.assertIn("pm ticket history sync", err)
        self.assertTrue(os.path.exists(pending))
        self.assertEqual(self.git("rev-parse", "refs/heads/pm-store"), tip)
        self.assertEqual(self.git("rev-parse", "main"), main_tip)
        with open(self.path) as f:
            self.assertIn("row survives", f.read())
        out, _ = self.cli("summary")
        self.assertIn("ticket history is pending", out)
        os.remove(hook)
        self.assertEqual(self.cli("history", "status")[0], "behind")
        _, err = self.cli("create", "catches up")
        self.assertEqual(err, "")
        self.assertFalse(os.path.exists(pending))
        self.assertEqual(self.cli("history", "status")[0], "on")
        with open(self.path) as f:
            self.assertEqual(self.git("show", "refs/heads/pm-store:tickets.jsonl"),
                             f.read().strip())

    def test_summary_catches_up_a_pending_snapshot(self):
        self.cli("history", "enable")
        hook = os.path.join(self.repo, ".git", "hooks", "reference-transaction")
        with open(hook, "w") as f:
            f.write("#!/bin/sh\nif [ \"$1\" = prepared ] && cat | grep -q "
                    "refs/heads/pm-store; then exit 1; fi\n")
        os.chmod(hook, 0o755)
        self.cli("create", "lagging")
        os.remove(hook)
        out, _ = self.cli("summary")
        self.assertNotIn("history is pending", out)
        self.assertFalse(os.path.exists(
            os.path.join(self.repo, V2_STORE_DIR, "history-pending")))
        self.assertEqual(self.cli("history", "status")[0], "on")

    # --- history_interval_seconds: deferred snapshots ---

    def _enable_deferred(self, seconds=3600):
        self.cli("history", "enable")
        cfg_path = os.path.join(self.repo, V2_STORE_DIR, "config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        cfg["history_interval_seconds"] = seconds
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)
        self.pending = os.path.join(self.repo, V2_STORE_DIR, "history-pending")

    def _age_marker(self, seconds):
        t = os.path.getmtime(self.pending) - seconds
        os.utime(self.pending, (t, t))

    @DEFERRED
    def test_deferred_note_makes_no_commit_and_marks_once(self):
        self._enable_deferred()
        tid, _ = self.cli("create", "row")
        before = self.store_count()
        self.cli("note", tid, "one")
        self.assertEqual(self.store_count(), before)
        with open(self.pending) as f:
            first = f.read()
        self.assertTrue(first.startswith("deferred "))
        mtime = os.path.getmtime(self.pending)
        _, err = self.cli("note", tid, "two")
        self.assertEqual(err, "")
        self.assertEqual(self.store_count(), before)
        with open(self.pending) as f:
            self.assertEqual(f.read(), first)
        self.assertEqual(os.path.getmtime(self.pending), mtime)
        self.assertEqual(self.cli("history", "status")[0], "deferred")

    @DEFERRED
    def test_deferred_create_unclaimed_is_deferred(self):
        self._enable_deferred()
        before = self.store_count()
        self.cli("create", "plain")
        self.assertEqual(self.store_count(), before)
        self.assertTrue(os.path.exists(self.pending))

    @DEFERRED
    def test_deferred_claim_release_close_reopen_snapshot_at_once(self):
        self._enable_deferred()
        tid, _ = self.cli("create", "row")
        self.assertTrue(os.path.exists(self.pending))
        for argv in (("claim", tid, "--as", "a"), ("release", tid),
                     ("close", tid), ("reopen", tid)):
            before = self.store_count()
            self.cli(*argv)
            self.assertEqual(self.store_count(), before + 1, argv)
            self.assertFalse(os.path.exists(self.pending), argv)
            self.cli("note", tid, f"after {argv[0]}")
            self.assertTrue(os.path.exists(self.pending), argv)

    def test_deferred_create_claimed_snapshots_at_once(self):
        self._enable_deferred()
        before = self.store_count()
        self.cli("create", "mine", "--claim-as", "a")
        self.assertEqual(self.store_count(), before + 1)
        self.assertFalse(os.path.exists(self.pending))

    @DEFERRED
    def test_deferred_marker_past_the_interval_flushes_on_next_op(self):
        self._enable_deferred(60)
        tid, _ = self.cli("create", "row")
        self.assertTrue(os.path.exists(self.pending))
        self._age_marker(61)
        before = self.store_count()
        self.cli("note", tid, "late")
        self.assertEqual(self.store_count(), before + 1)
        self.assertFalse(os.path.exists(self.pending))
        self.assertEqual(self.cli("history", "status")[0], "on")

    def test_a_fault_marker_is_always_due(self):
        self._enable_deferred(3600)
        tid, _ = self.cli("create", "row")
        with open(self.pending, "w") as f:
            f.write("some git fault\n")
        before = self.store_count()
        self.cli("note", tid, "retry")
        self.assertEqual(self.store_count(), before + 1)
        self.assertFalse(os.path.exists(self.pending))

    def test_sweep_and_deferral_tolerate_a_row_without_an_id(self):
        self._enable_deferred(3600)
        cfg_path = os.path.join(self.repo, V2_STORE_DIR, "config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        cfg.update(compact_closed_after_days=0, archive_closed_after_days=0)
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)
        with open(self.path, "a") as f:
            f.write(json.dumps({"title": "no id here"}) + "\n")
        self.cli("note", self.seed_tid, "still works")
        with open(self.path) as f:
            self.assertIn("no id here", f.read())

    @DEFERRED
    def test_deferred_sync_flushes(self):
        self._enable_deferred()
        self.cli("create", "row")
        self.assertEqual(self.cli("history", "status")[0], "deferred")
        self.cli("history", "sync")
        self.assertFalse(os.path.exists(self.pending))
        self.assertEqual(self.cli("history", "status")[0], "on")

    @DEFERRED
    def test_deferred_summary_flushes_without_a_warning(self):
        self._enable_deferred()
        self.cli("create", "row")
        before = self.store_count()
        out, err = self.cli("summary")
        self.assertEqual(self.store_count(), before + 1)
        self.assertFalse(os.path.exists(self.pending))
        self.assertNotIn("behind", out)
        self.assertNotIn("pending", out)
        self.assertNotIn("commit skipped", err)
        self.assertEqual(self.cli("history", "status")[0], "on")

    def test_interval_zero_or_absent_snapshots_every_op(self):
        self._enable_deferred(0)
        tid, _ = self.cli("create", "row")
        before = self.store_count()
        self.cli("note", tid, "n")
        self.assertEqual(self.store_count(), before + 1)
        self.assertFalse(os.path.exists(self.pending))

    def test_bad_history_interval_values_fail_validate(self):
        self.cli("history", "enable")
        cfg_path = os.path.join(self.repo, V2_STORE_DIR, "config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        for bad in (-1, 1.5, "60", True):
            with self.subTest(bad=bad):
                cfg["history_interval_seconds"] = bad
                with open(cfg_path, "w") as f:
                    json.dump(cfg, f)
                out, _ = self.cli("validate", "--json", rc=1)
                problems = json.loads(out)["problems"]
                self.assertTrue(any(p["invariant"] == "I-02"
                                    and "history_interval_seconds" in p["message"]
                                    for p in problems), problems)

    def test_enable_disable_round_trip(self):
        self.assertEqual(self.cli("history", "status")[0], "legacy")
        self.cli("history", "enable")
        out, _ = self.cli("history", "disable")
        self.assertIn("ticket history back on its branch", out)
        self.assertEqual(self.git("ls-files", "--", V2_TICKET_PATH), V2_TICKET_PATH)
        self.assertEqual(self.cli("history", "status")[0], "legacy")
        with open(os.path.join(self.repo, ".gitignore")) as f:
            self.assertNotIn(V2_TICKET_PATH, f.read().splitlines())
        with open(os.path.join(self.repo, V2_STORE_DIR, "config.json")) as f:
            self.assertNotIn("history_ref", json.load(f))
        self.git("rev-parse", "--verify", "refs/heads/pm-store")
        before = self.main_count()
        tid, err = self.cli("create", "legacy again")
        self.assertEqual(err, "")
        self.assertEqual(self.main_count(), before + 1)
        self.assertEqual(self.git("log", "-1", "--format=%s"), f"pm: create {tid}")
        self.cli("history", "enable")
        self.assertEqual(self.cli("history", "status")[0], "on")

    def test_enable_rerun_after_crash_after_config_write_resumes(self):
        entry = "tickets.jsonl"
        blob = self.git("hash-object", "-w", "--no-filters", "--", V2_TICKET_PATH)
        tree = subprocess.run(
            ["git", "-C", self.repo, "mktree"], input=f"100644 blob {blob}\t{entry}\n",
            capture_output=True, text=True, check=True).stdout.strip()
        commit = self.git("commit-tree", tree, "-m", "pm: seed pm-store from x")
        self.git("update-ref", "refs/heads/pm-store", commit)
        cfg_path = os.path.join(self.repo, V2_STORE_DIR, "config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        cfg["history_ref"] = "pm-store"
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2, sort_keys=True)
            f.write("\n")
        self.assertEqual(self.cli("history", "status")[0], "migrating")
        out, _ = self.cli("history", "enable")
        self.assertIn("ticket history on refs/heads/pm-store", out)
        self.assertEqual(self.cli("history", "status")[0], "on")
        self.assertEqual(self.git("ls-files", "--", V2_TICKET_PATH), "")
        self.assertEqual(self.git("status", "--porcelain"), "")
        again, _ = self.cli("history", "enable")
        self.assertEqual(again, out)

    def test_enable_refuses_a_non_empty_index_and_leaves_it(self):
        with open(os.path.join(self.repo, "other.txt"), "w") as f:
            f.write("staged\n")
        self.git("add", "other.txt")
        _, err = self.cli("history", "enable", rc=1)
        self.assertIn("other.txt", err)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "other.txt")
        self.assertEqual(self.cli("history", "status")[0], "legacy")

    def test_restore_refuses_newer_working_file_and_restores_a_missing_one(self):
        self.cli("history", "enable")
        self.cli("create", "recorded")
        with open(self.path, "rb") as f:
            good = f.read()
        with open(self.path, "ab") as f:
            f.write(b"\n")
        _, err = self.cli("history", "restore", rc=1)
        self.assertIn("pm ticket history sync", err)
        with open(self.path, "rb") as f:
            self.assertEqual(f.read(), good + b"\n")
        os.remove(self.path)
        self.assertEqual(self.cli("history", "status")[0], "missing")
        for verb in (("list",), ("summary",), ("create", "x")):
            _, err = self.cli(*verb, rc=1)
            self.assertIn(".pm/tickets.jsonl is missing but this store keeps "
                          "history on pm-store; run: pm ticket history restore", err)
        self.cli("history", "restore")
        with open(self.path, "rb") as f:
            self.assertEqual(f.read(), good)
        self.assertEqual(self.cli("history", "status")[0], "on")

    def test_summary_dirty_line_compares_against_pm_store(self):
        self.cli("history", "enable")
        out, _ = self.cli("summary")
        self.assertNotIn("history is behind", out)
        with open(self.path, "ab") as f:
            f.write(b"\n")
        out, _ = self.cli("summary")
        self.assertIn("note: ticket history is behind the working file; "
                      "run: pm ticket history sync", out)
        self.cli("history", "sync")
        out, _ = self.cli("summary")
        self.assertNotIn("history is behind", out)

    def test_history_commit_ignores_the_off_branch_rule(self):
        self.cli("history", "enable")
        self.git("checkout", "-q", "-b", "feature")
        before = self.store_count()
        _, err = self.cli("create", "on feature")
        self.assertEqual(err, "")
        self.assertEqual(self.store_count(), before + 1)

    def _seed_pm_store(self):
        blob = self.git("hash-object", "-w", "--no-filters", "--", V2_TICKET_PATH)
        tree = subprocess.run(
            ["git", "-C", self.repo, "mktree"],
            input=f"100644 blob {blob}\ttickets.jsonl\n",
            capture_output=True, text=True, check=True).stdout.strip()
        self.git("update-ref", "refs/heads/pm-store",
                 self.git("commit-tree", tree, "-m", "pm: seed pm-store from x"))

    def test_enable_resumes_after_crash_between_stage_and_commit(self):
        self._seed_pm_store()
        cfg_path = os.path.join(self.repo, V2_STORE_DIR, "config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        cfg["history_ref"] = "pm-store"
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2, sort_keys=True)
            f.write("\n")
        with open(os.path.join(self.repo, ".gitignore"), "a") as f:
            f.write(V2_TICKET_PATH + "\n")
        self.git("rm", "--cached", "-q", "--", V2_TICKET_PATH)
        self.git("add", "--", ".pm/config.json", ".gitignore")
        self.assertEqual(self.git("diff", "--cached", "--name-status"),
                         "M\t.gitignore\nM\t.pm/config.json\nD\t.pm/tickets.jsonl")
        main_before = self.main_count()
        self.cli("history", "enable")
        self.assertEqual(self.cli("history", "status")[0], "on")
        self.assertEqual(self.main_count(), main_before + 1)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_enable_refuses_staged_gitignore_that_differs_from_worktree(self):
        gi = os.path.join(self.repo, ".gitignore")
        with open(gi, "a") as f:
            f.write("staged-line\n")
        self.git("add", ".gitignore")
        with open(gi, "a") as f:
            f.write("worktree-only\n")
        before = self.git("diff", "--cached", "--name-status")
        _, err = self.cli("history", "enable", rc=1)
        self.assertIn(".gitignore", err)
        self.assertEqual(self.git("diff", "--cached", "--name-status"), before)

    def test_enable_refuses_prestaged_tickets_file_modification(self):
        with open(self.path, "ab") as f:
            f.write(b"\n")
        self.git("add", V2_TICKET_PATH)
        _, err = self.cli("history", "enable", rc=1)
        self.assertIn(V2_TICKET_PATH, err)
        self.assertEqual(self.git("diff", "--cached", "--name-status"),
                         "M\t.pm/tickets.jsonl")

    def test_enable_flushes_unstaged_tracked_changes_to_main(self):
        with open(self.path, "ab") as f:
            f.write(b"\n")
        main_before = self.main_count()
        self.cli("history", "enable")
        self.assertEqual(self.main_count(), main_before + 2)
        flushed = subprocess.run(
            ["git", "-C", self.repo, "show", f"main~1:{V2_TICKET_PATH}"],
            capture_output=True).stdout
        with open(self.path, "rb") as f:
            self.assertEqual(flushed, f.read())
        self.assertIn(self.seed_tid.encode(), flushed)

    def test_disable_refuses_unrelated_staged_file(self):
        self.cli("history", "enable")
        with open(os.path.join(self.repo, "other.txt"), "w") as f:
            f.write("x\n")
        self.git("add", "other.txt")
        _, err = self.cli("history", "disable", rc=1)
        self.assertIn("other.txt", err)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "other.txt")

    def test_status_is_migrating_when_untracked_but_not_ignored(self):
        self.cli("history", "enable")
        gi = os.path.join(self.repo, ".gitignore")
        with open(gi) as f:
            kept = [ln for ln in f.read().splitlines(True)
                    if ln.strip() != V2_TICKET_PATH]
        with open(gi, "w") as f:
            f.write("".join(kept))
        self.assertEqual(self.cli("history", "status")[0], "migrating")
        self.git("checkout", "--", ".gitignore")
        self.assertEqual(self.cli("history", "status")[0], "on")

    def test_disable_preserves_other_gitignore_bytes(self):
        gi = os.path.join(self.repo, ".gitignore")
        with open(gi, "rb") as f:
            crlf = f.read().replace(b"\n", b"\r\n")
        with open(gi, "wb") as f:
            f.write(crlf)
        self.git("commit", "-q", "-am", "crlf gitignore")
        self.cli("history", "enable")
        self.cli("history", "disable")
        with open(gi, "rb") as f:
            self.assertEqual(f.read(), crlf)

    def test_enable_refuses_off_default_branch(self):
        self.git("checkout", "-q", "-b", "feature")
        _, err = self.cli("history", "enable", rc=1)
        self.assertIn("not main", err)


class StoreRoutingTest(unittest.TestCase):
    """fr-1576dd: id-taking verbs route by prefix through the registry
    (PM_STORES_FILE points at a temp one); --store aliases --repo."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = os.path.realpath(self._tmp.name)
        self.a = self.make_repo("a", "aa")
        self.b = self.make_repo("b", "bb")
        self.c = self.make_repo("c", "cc")
        self.a_id = run(self.a, "create", "in a")
        self.b_id = run(self.b, "create", "in b")
        self.c_id = run(self.c, "create", "in c")
        run(self.c, "claim", self.c_id, "--as", "x")
        run(self.c, "close", self.c_id)
        self.registry = os.path.join(self.base, "stores.json")
        self.write_registry([{"path": self.a}, {"path": self.b},
                             {"path": self.c, "role": "frozen"}])

    def make_repo(self, name, prefix):
        repo = os.path.join(self.base, name)
        os.makedirs(repo)
        for argv in (("init", "-q", "-b", "main"), ("config", "user.name", "t"),
                     ("config", "user.email", "t@example.invalid"),
                     ("config", "commit.gpgsign", "false")):
            subprocess.run(["git", "-C", repo, *argv], check=True,
                           capture_output=True)
        run(repo, "init", "--prefix", prefix)
        subprocess.run(["git", "-C", repo, "add", "-A", "."], check=True)
        subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "seed"], check=True,
                       capture_output=True)
        return repo

    def write_registry(self, stores):
        with open(self.registry, "w") as f:
            json.dump({"stores": stores}, f)

    def pm(self, cwd, *argv, rc=0):
        env = dict(os.environ, PM_STORES_FILE=self.registry)
        r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=cwd,
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, rc, r.stderr)
        return r.stdout.strip(), r.stderr.strip()

    def log(self, repo, ref="HEAD"):
        return subprocess.run(["git", "-C", repo, "log", "--format=%s", ref],
                              capture_output=True, text=True).stdout.split("\n")

    def rows_of(self, repo):
        with open(os.path.join(repo, ".pm", "tickets.jsonl")) as f:
            return {r["id"]: r for r in map(json.loads, f)}

    def test_show_routes_to_the_owning_store_without_a_flag(self):
        out, _ = self.pm(self.a, "show", self.b_id)
        self.assertIn(self.b_id, out)
        self.assertIn("in b", out)

    def test_where_prints_the_owning_repo_root(self):
        self.assertEqual(self.pm(self.a, "where", self.b_id)[0], self.b)
        self.assertEqual(self.pm(self.a, "where", self.a_id)[0], self.a)

    def test_where_works_outside_any_store(self):
        with tempfile.TemporaryDirectory() as bare:
            self.assertEqual(self.pm(bare, "where", self.b_id)[0], self.b)

    def test_where_refuses_with_the_design_text_when_nothing_owns_the_prefix(self):
        _, err = self.pm(self.a, "where", "zz-123456", rc=1)
        self.assertIn("pm: no registered store owns prefix 'zz'; pass --store "
                      "<repo>, or add the repo to "
                      "~/frontier/runtime-tools/pm/stores.json and deploy pm", err)

    def test_where_mutate_passes_for_a_live_id_and_writes_nothing(self):
        before = (self.rows_of(self.a), self.log(self.a))
        self.assertEqual(self.pm(self.a, "where", "--mutate", self.a_id)[0], self.a)
        self.assertEqual(self.pm(self.a, "where", "--mutate", self.b_id)[0], self.b)
        with tempfile.TemporaryDirectory() as bare:
            self.assertEqual(self.pm(bare, "where", "--mutate", self.b_id)[0], self.b)
        self.assertEqual((self.rows_of(self.a), self.log(self.a)), before)

    def test_where_mutate_refuses_a_frozen_store(self):
        before = self.frozen_state()
        for cwd in (self.a, self.c):
            _, err = self.pm(cwd, "where", "--mutate", self.c_id, rc=1)
            self.assertIn("frozen", err)
        _, err = self.pm(self.a, "--store", self.c, "where", "--mutate", self.c_id, rc=1)
        self.assertIn("frozen", err)
        self.assertEqual(self.frozen_state(), before)

    def test_where_mutate_refuses_an_unknown_id(self):
        _, err = self.pm(self.a, "where", "--mutate", "aa-ffffff", rc=1)
        self.assertIn("no ticket aa-ffffff", err)
        _, err = self.pm(self.a, "where", "--mutate", "zz-123456", rc=1)
        self.assertIn("no registered store owns prefix 'zz'", err)

    def test_where_mutate_refuses_an_untrusted_registry_even_for_the_cwd_store(self):
        with open(self.registry, "w") as f:
            f.write("{not json")
        self.pm(self.a, "where", "--mutate", self.a_id, rc=1)

    def test_where_mutate_validates_findings_with_the_close_parser(self):
        bad = "filed lai-e1855d; noted lai-6141cb; ..."
        _, err = self.pm(self.a, "where", "--mutate", self.a_id, "--findings", bad, rc=1)
        self.assertIn("--findings", err)
        _, close_err = self.pm(self.a, "close", self.a_id, "--findings", bad, rc=1)
        self.assertEqual(err, close_err)
        for v in ("none,%s" % self.b_id, "a,,b", "aa-ffffff", "bb-ffffff"):
            _, err = self.pm(self.a, "where", "--mutate", self.a_id, "--findings", v, rc=1)
            self.assertIn("--findings", err)
        self.assertIn("open", self.pm(self.a, "show", self.a_id)[0])

    def test_where_mutate_accepts_good_findings(self):
        for v in ("none", self.b_id, self.c_id, "%s,%s" % (self.b_id, self.c_id)):
            self.assertEqual(self.pm(self.a, "where", "--mutate", self.a_id,
                                     "--findings", v)[0], self.a)
        self.assertIn("open", self.pm(self.a, "show", self.a_id)[0])

    def test_where_mutate_refuses_an_already_closed_ticket_like_close(self):
        tid = run(self.a, "create", "to close")
        self.pm(self.a, "close", tid, "--findings", "none")
        _, err = self.pm(self.a, "where", "--mutate", tid, rc=1)
        self.assertIn("already closed", err)
        _, real = self.pm(self.a, "close", tid, "--findings", "none", rc=1)
        self.assertEqual(err, real)
        _, err = self.pm(self.a, "where", "--mutate", "--verb", "release", tid, rc=1)
        self.assertIn("not claimed (status: closed)", err)

    def test_where_mutate_refuses_an_epic_with_open_children_like_close(self):
        epic = run(self.a, "create", "epic", "--kind", "epic")
        child = run(self.a, "create", "kid", "--parent", epic)
        before = self.rows_of(self.a)
        _, err = self.pm(self.a, "where", "--mutate", epic, rc=1)
        self.assertIn("has open children", err)
        _, real = self.pm(self.a, "close", epic, "--findings", "none", rc=1)
        self.assertEqual(err, real)
        self.assertEqual(self.rows_of(self.a), before)
        self.pm(self.a, "close", child, "--findings", "none")
        self.assertEqual(self.pm(self.a, "where", "--mutate", epic)[0], self.a)

    def test_where_mutate_release_needs_a_claim_like_release(self):
        _, err = self.pm(self.a, "where", "--mutate", "--verb", "release", self.a_id, rc=1)
        self.assertIn("not claimed (status: open)", err)
        _, real = self.pm(self.a, "release", self.a_id, rc=1)
        self.assertEqual(err, real)
        self.pm(self.a, "claim", self.a_id, "--as", "x")
        self.assertEqual(self.pm(self.a, "where", "--mutate", "--verb", "release",
                                 self.a_id)[0], self.a)
        self.assertIn("claimed", self.pm(self.a, "show", self.a_id)[0])

    def test_where_verb_needs_mutate_and_release_takes_no_findings(self):
        _, err = self.pm(self.a, "where", self.a_id, "--verb", "close", rc=1)
        self.assertIn("--mutate", err)
        self.pm(self.a, "where", "--mutate", "--verb", "release", self.a_id,
                "--findings", "none", rc=1)

    def test_where_findings_needs_mutate(self):
        _, err = self.pm(self.a, "where", self.a_id, "--findings", "none", rc=1)
        self.assertIn("--mutate", err)

    def test_routed_mutation_commits_in_the_owning_repo(self):
        a_before = self.log(self.a)
        self.pm(self.a, "claim", self.b_id, "--as", "x")
        self.assertEqual(self.log(self.b)[0], f"pm: claim {self.b_id}")
        self.assertEqual(self.log(self.a), a_before)

    def test_routed_mutation_in_history_mode_commits_to_the_owners_ref(self):
        self.pm(self.b, "history", "enable")
        main_before = self.log(self.b, "main")
        self.pm(self.a, "claim", self.b_id, "--as", "x")
        self.assertEqual(self.log(self.b, "refs/heads/pm-store")[0],
                         f"pm: claim {self.b_id}")
        self.assertEqual(self.log(self.b, "main"), main_before)
        self.assertEqual(self.pm(self.b, "history", "status")[0], "on")

    def findings_of(self, cwd, tid):
        return json.loads(self.pm(cwd, "show", tid, "--json")[0]).get("findings")

    def test_findings_same_store_id_reads_no_registry(self):
        t = run(self.a, "create", "work")
        os.remove(self.registry)
        self.pm(self.a, "close", t, "--findings", self.a_id)
        self.assertEqual(self.findings_of(self.a, t), [self.a_id])

    def test_findings_other_store_id_bare_and_slash_form(self):
        t = run(self.a, "create", "work")
        slash = f"bb/{self.b_id}"
        self.pm(self.a, "close", t, "--findings", f"{self.b_id},{slash},{self.b_id}")
        self.assertEqual(self.findings_of(self.a, t), [self.b_id])

    def test_findings_slash_form_is_stored_bare_and_validates(self):
        t = run(self.a, "create", "work")
        self.pm(self.a, "close", t, "--findings", f"bb/{self.b_id},aa/{self.a_id}")
        self.assertEqual(self.findings_of(self.a, t), [self.b_id, self.a_id])
        self.pm(self.a, "validate")

    def test_findings_bare_foreign_id_validates(self):
        t = run(self.a, "create", "work")
        self.pm(self.a, "close", t, "--findings", self.b_id)
        self.assertEqual(self.findings_of(self.a, t), [self.b_id])
        self.pm(self.a, "validate")

    def test_findings_unknown_slash_id_still_refused(self):
        t = run(self.a, "create", "work")
        self.pm(self.a, "close", t, "--findings", "bb/bb-ffffff", rc=1)
        self.pm(self.a, "close", t, "--findings", "aa/aa-ffffff", rc=1)
        self.assertIn("open", self.pm(self.a, "show", t)[0])

    def test_findings_frozen_store_closed_id(self):
        t = run(self.a, "create", "work")
        self.pm(self.a, "close", t, "--findings", self.c_id)
        self.assertEqual(self.findings_of(self.a, t), [self.c_id])

    def test_findings_unowned_prefix_uses_the_resolve_store_text(self):
        t = run(self.a, "create", "work")
        for ref in ("zz-123456", "zz/zz-123456"):
            _, err = self.pm(self.a, "close", t, "--findings", ref, rc=1)
            self.assertIn("no registered store owns prefix 'zz'; pass --store "
                          "<repo>, or add the repo to "
                          "~/frontier/runtime-tools/pm/stores.json and deploy pm", err)
        self.assertIn("open", self.pm(self.a, "show", t)[0])

    def test_findings_other_store_id_without_a_row_names_the_store(self):
        t = run(self.a, "create", "work")
        _, err = self.pm(self.a, "close", t, "--findings", "bb-ffffff", rc=1)
        self.assertIn(f"no ticket bb-ffffff in store {self.b}", err)
        self.assertIn("open", self.pm(self.a, "show", t)[0])

    def test_bulk_ids_must_share_a_store(self):
        _, err = self.pm(self.a, "claim", self.a_id, self.b_id, "--as", "x", rc=1)
        self.assertIn("different stores", err)
        self.assertIn("open", self.pm(self.a, "show", self.a_id)[0])

    def test_frozen_store_answers_reads_and_refuses_mutations(self):
        out, _ = self.pm(self.a, "show", self.c_id)
        self.assertIn("in c", out)
        _, err = self.pm(self.a, "reopen", self.c_id, rc=1)
        self.assertIn("frozen", err)
        self.assertIn("closed", self.pm(self.a, "show", self.c_id)[0])

    def frozen_state(self):
        with open(os.path.join(self.c, ".pm", "tickets.jsonl"), "rb") as f:
            data = f.read()
        return data, self.log(self.c), os.listdir(os.path.join(self.c, ".pm"))

    def assert_refused_untouched(self, cwd, *argv):
        before = self.frozen_state()
        out, err = self.pm(cwd, *argv, rc=1)
        self.assertIn("frozen", err)
        self.assertIn(self.c, err)
        self.assertEqual(self.frozen_state(), before)

    def test_frozen_store_refuses_create_from_its_own_cwd(self):
        self.assert_refused_untouched(self.c, "create", "nope")

    def test_frozen_store_refusal_names_the_registry_and_the_live_owner(self):
        d = self.make_repo("d", "cc")
        self.write_registry([{"path": self.c, "role": "frozen"}, {"path": d}])
        _, err = self.pm(self.c, "create", "nope", rc=1)
        self.assertIn(self.registry, err)
        self.assertIn(f"the live store for its prefix is {d}", err)

    def test_frozen_refusal_names_the_successor_in_every_path(self):
        succ = os.path.join(self.base, "frontier")
        os.makedirs(succ)
        self.write_registry([{"path": self.a},
                             {"path": self.c, "role": "frozen", "successor": succ}])
        for cwd, argv in ((self.c, ("create", "nope")),
                          (self.a, ("reopen", self.c_id)),
                          (self.a, ("--store", self.c, "close", self.c_id))):
            _, err = self.pm(cwd, *argv, rc=1)
            self.assertIn("frozen", err)
            self.assertIn(f"use {succ}/.pm", err)

    def test_frozen_summary_and_ready_print_one_line_with_successor(self):
        succ = os.path.join(self.base, "frontier")
        os.makedirs(succ)
        run(self.c, "create", "open work")
        self.write_registry([{"path": self.a},
                             {"path": self.c, "role": "frozen", "successor": succ}])
        for verb in ("summary", "ready"):
            out, _ = self.pm(self.c, verb)
            self.assertEqual(len(out.splitlines()), 1, out)
            self.assertIn("frozen", out)
            self.assertIn(succ, out)
            self.assertNotIn("open work", out)
        out, _ = self.pm(self.c, "ready", "--json")
        self.assertIn("open work", out)

    def test_frozen_summary_without_successor_still_one_line(self):
        out, _ = self.pm(self.c, "summary")
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertIn("frozen", out)

    def test_live_store_summary_is_unchanged_by_a_frozen_peer(self):
        out, _ = self.pm(self.a, "summary")
        self.assertNotIn("frozen", out)

    def test_stores_check_flags_a_bad_successor(self):
        for bad in (5, "", os.path.join(self.base, "missing")):
            self.write_registry([{"path": self.a},
                                 {"path": self.c, "role": "frozen", "successor": bad}])
            out, _ = self.pm(self.a, "stores", "--check", rc=2)
            self.assertIn("successor", out)
        self.write_registry([{"path": self.a, "successor": self.b}])
        out, _ = self.pm(self.a, "stores", "--check", rc=2)
        self.assertIn("only meaningful on a frozen store", out)
        self.write_registry([{"path": self.a},
                             {"path": self.c, "role": "frozen", "successor": self.a}])
        out, _ = self.pm(self.a, "stores", "--check")
        self.assertIn("OK", out)

    def test_frozen_store_refuses_an_explicit_store_flag_mutation(self):
        for argv in (("note", self.c_id, "x"), ("close", self.c_id),
                     ("claim", self.c_id, "--as", "x"),
                     ("--store", self.c, "create", "nope")):
            if argv[0] == "--store":
                self.assert_refused_untouched(self.a, *argv)
            else:
                self.assert_refused_untouched(self.a, "--store", self.c, *argv)

    def test_frozen_store_refuses_every_store_scoped_verb(self):
        for argv in (("archive", "--closed-before", "2999-01-01"),
                     ("history", "enable"), ("history", "disable"),
                     ("history", "sync"), ("history", "restore")):
            self.assert_refused_untouched(self.c, *argv)
            self.assert_refused_untouched(self.a, "--store", self.c, *argv)

    def test_frozen_store_still_answers_reads(self):
        self.assertIn("in c", self.pm(self.c, "show", self.c_id)[0])
        self.pm(self.c, "list")
        self.pm(self.c, "validate")
        self.pm(self.c, "summary")
        self.pm(self.c, "history", "status")
        self.pm(self.a, "--store", self.c, "show", self.c_id)
        self.pm(self.a, "--store", self.c, "history", "status")
        self.pm(self.c, "archive", "--closed-before", "2999-01-01", "--dry-run")

    def a_state(self):
        with open(os.path.join(self.a, ".pm", "tickets.jsonl"), "rb") as f:
            return f.read()

    def test_unparsable_registry_refuses_every_mutation_but_not_reads(self):
        with open(self.registry, "w") as f:
            f.write("{nope")
        before = self.a_state()
        for argv in (("create", "x"), ("claim", self.a_id, "--as", "x"),
                     ("--store", self.a, "note", self.a_id, "x")):
            _, err = self.pm(self.a, *argv, rc=1)
            self.assertIn(self.registry, err)
            self.assertIn("cannot read store registry", err)
        self.assertEqual(self.a_state(), before)
        self.assertIn("in a", self.pm(self.a, "show", self.a_id)[0])
        self.pm(self.a, "list")
        self.pm(self.a, "validate")

    def test_non_utf8_registry_is_a_clean_refusal_not_a_traceback(self):
        with open(self.registry, "wb") as f:
            f.write(b'{"stores": [\xff]}')
        self.assertIn("in a", self.pm(self.a, "show", self.a_id)[0])
        before = self.a_state()
        for argv in (("note", self.a_id, "x"), ("note", self.b_id, "x")):
            _, err = self.pm(self.a, *argv, rc=1)
            self.assertIn(self.registry, err)
            self.assertNotIn("Traceback", err)
        self.assertEqual(self.a_state(), before)

    def test_dangling_symlink_registry_refuses_mutations(self):
        os.remove(self.registry)
        os.symlink(os.path.join(self.base, "nowhere.json"), self.registry)
        _, err = self.pm(self.a, "note", self.a_id, "x", rc=1)
        self.assertIn(self.registry, err)
        self.assertIn("in a", self.pm(self.a, "show", self.a_id)[0])

    def test_bad_role_refuses_mutations_naming_the_value(self):
        for role in ("Frozen", "archived"):
            self.write_registry([{"path": self.a}, {"path": self.c, "role": role}])
            before = self.a_state()
            _, err = self.pm(self.a, "claim", self.a_id, "--as", "x", rc=1)
            self.assertIn(repr(role), err)
            self.assertEqual(self.a_state(), before)
            self.pm(self.a, "list")

    def test_stores_check_reports_a_bad_role_as_exit_2_naming_it(self):
        self.write_registry([{"path": self.a}, {"path": self.c, "role": "Frozen"}])
        out, _ = self.pm(self.a, "stores", "--check", rc=2)
        self.assertIn("problem: ", out)
        self.assertIn("'Frozen'", out)

    def test_absent_registry_file_leaves_stores_live(self):
        os.remove(self.registry)
        self.assertIn("in a", self.pm(self.a, "show", self.a_id)[0])
        self.pm(self.a, "create", "still works")

    def test_live_store_mutations_are_unaffected_by_a_frozen_peer(self):
        t = self.pm(self.a, "create", "still live")[0]
        self.pm(self.a, "claim", t, "--as", "x")
        self.pm(self.b, "note", self.b_id, "fine")
        self.pm(self.a, "archive", "--closed-before", "2999-01-01")

    def test_id_taking_read_works_with_the_registry_deleted(self):
        self.write_registry([{"path": self.c, "role": "frozen"}])
        os.remove(self.registry)
        for argv in (("show", self.a_id), ("list",), ("validate",)):
            _, err = self.pm(self.a, *argv)
            self.assertEqual(err, "")

    def test_frozen_row_is_a_read_fallback_under_a_live_owner(self):
        cfg = os.path.join(self.a, ".pm", "config.json")
        with open(cfg) as f:
            data = json.load(f)
        data["legacy_prefixes"] = ["cc"]
        with open(cfg, "w") as f:
            json.dump(data, f)
        out, _ = self.pm(self.a, "show", self.c_id)
        self.assertIn("in c", out)
        self.assertEqual(self.pm(self.a, "where", self.c_id)[0], self.a)

    def declare_legacy(self, repo, legacy):
        cfg = os.path.join(repo, ".pm", "config.json")
        with open(cfg) as f:
            data = json.load(f)
        data["legacy_prefixes"] = legacy
        with open(cfg, "w") as f:
            json.dump(data, f)

    def graft_row(self, repo, src_id, new_id):
        path = os.path.join(repo, ".pm", "tickets.jsonl")
        with open(path) as f:
            rows = [json.loads(ln) for ln in f if ln.strip()]
        row = dict(next(r for r in rows if r["id"] == src_id), id=new_id)
        with open(path, "a") as f:
            f.write(json.dumps(row) + "\n")

    def edges_of(self, repo, tid):
        out, _ = self.pm(repo, "show", tid, "--json")
        return json.loads(out)["edges"]

    def test_create_mints_the_primary_prefix_only(self):
        self.declare_legacy(self.a, ["cc"])
        out, _ = self.pm(self.a, "create", "minted")
        self.assertTrue(out.startswith("aa-"), out)

    def set_config(self, repo, **keys):
        cfg = os.path.join(repo, ".pm", "config.json")
        with open(cfg) as f:
            data = json.load(f)
        data.update(keys)
        with open(cfg, "w") as f:
            json.dump(data, f)

    def test_validate_accepts_gate_and_known_red(self):
        self.set_config(self.a, gate=["python3", "tests/run_suite.py"],
                        known_red=[{"match": "x", "ticket": "aa-123456",
                                    "since": "2026-10-13"}])
        self.pm(self.a, "validate")

    def test_validate_refuses_a_malformed_gate(self):
        for bad in ("python3 run.py", [], ["ok", 1]):
            self.set_config(self.a, gate=bad)
            out, err = self.pm(self.a, "validate", rc=1)
            self.assertIn("/gate", out + err)

    def test_validate_refuses_a_malformed_known_red(self):
        self.set_config(self.a, known_red=[{"match": "x"}])
        self.pm(self.a, "validate", rc=1)

    def test_validate_accepts_a_legacy_prefixed_row(self):
        self.declare_legacy(self.a, ["cc"])
        self.graft_row(self.a, self.a_id, self.c_id)
        self.pm(self.a, "validate")

    def test_dep_related_legacy_id_is_local_when_the_row_is_held(self):
        self.declare_legacy(self.a, ["cc"])
        self.graft_row(self.a, self.a_id, self.c_id)
        for ref in (self.c_id, f"cc/{self.c_id}"):
            self.pm(self.a, "dep", self.a_id, "related", ref)
            self.assertEqual(self.edges_of(self.a, self.a_id),
                             [{"type": "related", "to": self.c_id}])
            self.pm(self.a, "unlink", self.a_id, self.c_id)

    def test_dep_related_legacy_id_is_cross_store_when_the_row_is_absent(self):
        self.declare_legacy(self.a, ["cc"])
        self.pm(self.a, "dep", self.a_id, "related", f"cc/{self.c_id}")
        self.assertEqual(self.edges_of(self.a, self.a_id),
                         [{"type": "related", "to": f"cc/{self.c_id}"}])
        out, _ = self.pm(self.a, "stores", "--check")
        self.assertIn("OK", out)

    def test_dep_related_unheld_legacy_id_without_a_frozen_owner_is_refused(self):
        self.declare_legacy(self.a, ["cc"])
        self.write_registry([{"path": self.a}])
        _, err = self.pm(self.a, "dep", self.a_id, "related", "cc/cc-abcdef", rc=1)
        self.assertIn("cc/cc-abcdef", err)

    def test_two_live_owners_are_refused(self):
        d = self.make_repo("d", "aa")
        self.write_registry([{"path": self.a}, {"path": d}, {"path": self.b}])
        with tempfile.TemporaryDirectory() as bare:
            _, err = self.pm(bare, "where", self.a_id, rc=1)
        self.assertIn("pm: prefix 'aa' is owned by two registered stores:", err)
        self.assertIn("fix runtime-tools/pm/stores.json or pass --store", err)

    def test_explicit_store_flag_and_repo_alias_agree(self):
        via_store, _ = self.pm(self.a, "--store", self.b, "show", self.b_id)
        via_repo, _ = self.pm(self.a, "--repo", self.b, "show", self.b_id)
        verb_level, _ = self.pm(self.a, "show", self.b_id, "--store", self.b)
        self.assertEqual(via_store, via_repo)
        self.assertEqual(via_store, verb_level)

    def test_repo_alias_is_hidden_from_help(self):
        top, _ = self.pm(self.a, "--help")
        verb, _ = self.pm(self.a, "show", "--help")
        for text in (top, verb):
            self.assertIn("--store", text)
            self.assertNotIn("--repo", text)

    def test_store_scoped_verbs_do_not_route(self):
        out, _ = self.pm(self.a, "list", "--json")
        ids = [t["id"] for t in json.loads(out)]
        self.assertEqual(ids, [self.a_id])

    def test_stores_lists_and_check_passes(self):
        out, _ = self.pm(self.a, "stores")
        self.assertIn(f"{self.b}  bb  live", out)
        self.assertIn(f"{self.c}  cc  frozen", out)
        out, _ = self.pm(self.a, "stores", "--check")
        self.assertIn("OK: 3 stores", out)

    def test_stores_check_reports_missing_path_and_collision(self):
        d = self.make_repo("d", "aa")
        self.write_registry([{"path": self.a}, {"path": d},
                             {"path": os.path.join(self.base, "gone")}])
        out, _ = self.pm(self.a, "stores", "--check", rc=2)
        self.assertIn("no .pm store at " + os.path.join(self.base, "gone"), out)
        self.assertIn("live prefix 'aa' is owned by", out)

    def test_cwd_store_reads_survive_a_malformed_registry_mutations_do_not(self):
        with open(self.registry, "w") as f:
            f.write('{"stores": [{"path": "/x", "role": "Frozen"}')
        out, _ = self.pm(self.a, "show", self.a_id)
        self.assertIn("in a", out)
        _, err = self.pm(self.a, "note", self.a_id, "refused", rc=1)
        self.assertIn(self.registry, err)
        self.assertNotIn("refused", self.pm(self.a, "show", self.a_id)[0])

    def test_prefix_slash_id_routes_and_normalises(self):
        out, _ = self.pm(self.a, "show", f"bb/{self.b_id}")
        self.assertIn("in b", out)
        self.pm(self.a, "note", f"bb/{self.b_id}", "via slash")
        self.assertIn("via slash", self.pm(self.b, "show", self.b_id)[0])
        self.assertEqual(self.log(self.b)[0], f"pm: note {self.b_id}")
        _, err = self.pm(self.a, "show", f"aa/{self.b_id}", rc=1)
        self.assertIn("prefix", err)

    def test_stores_check_reports_a_malformed_registry_as_exit_2(self):
        with open(self.registry, "w") as f:
            f.write("{nope")
        out, _ = self.pm(self.a, "stores", "--check", rc=2)
        self.assertIn("problem: ", out)

    def test_stores_check_reports_foreign_prefix_rows(self):
        with open(os.path.join(self.a, ".pm", "tickets.jsonl"), "a") as f:
            f.write(json.dumps({"id": "zz-111111"}) + "\n")
        out, _ = self.pm(self.b, "stores", "--check", rc=2)
        self.assertIn("ticket 'zz-111111' has a prefix its store does not own", out)

    def test_stores_check_reports_two_frozen_owners_but_not_a_symlink_twin(self):
        d = self.make_repo("d", "cc")
        self.write_registry([{"path": self.c, "role": "frozen"},
                             {"path": d, "role": "frozen"}])
        out, _ = self.pm(self.a, "stores", "--check", rc=2)
        self.assertIn("frozen prefix 'cc' is owned by", out)
        link = os.path.join(self.base, "link")
        os.symlink(self.a, link)
        self.write_registry([{"path": self.a}, {"path": link}])
        out, _ = self.pm(self.b, "stores", "--check")
        self.assertIn("OK: 2 stores", out)

    def test_tests_do_not_read_the_real_registry(self):
        self.assertNotEqual(os.environ["PM_STORES_FILE"],
                            os.path.join(os.path.dirname(TICKET_CLI), "..", "..", "stores.json"))
        with open(os.environ["PM_STORES_FILE"]) as f:
            self.assertEqual(json.load(f), {"stores": []})


def shape(obj):
    """Recursive type skeleton of a JSON value (list = sorted unique element shapes)."""
    if isinstance(obj, dict):
        return {k: shape(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return sorted({json.dumps(shape(v), sort_keys=True) for v in obj})
    return type(obj).__name__


ROW_KEYS = {"assignee", "body", "closure_reason", "created", "edges", "id", "kind",
            "labels", "notes", "parent", "priority", "status", "title", "updated"}


class CrossStoreEdgeTest(unittest.TestCase):
    """fr-b1b41c: a lin-style ticket blocks a lai-style gate through two temp
    stores and a PM_STORES_FILE registry."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = os.path.realpath(self._tmp.name)
        self.lin = self.make_repo("lin", "lin")
        self.lai = self.make_repo("lai", "lai")
        self.registry = os.path.join(self.base, "stores.json")
        self.write_registry([{"path": self.lin}, {"path": self.lai}])
        self.blocker = run(self.lin, "create", "init work")
        self.gate = run(self.lai, "create", "the gate")
        self.plain = run(self.lai, "create", "plain work")

    make_repo = StoreRoutingTest.make_repo
    write_registry = StoreRoutingTest.write_registry
    log = StoreRoutingTest.log

    def pm(self, cwd, *argv, rc=0):
        env = dict(os.environ, PM_STORES_FILE=self.registry)
        r = subprocess.run([sys.executable, TICKET_CLI, *argv], cwd=cwd,
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, rc, r.stderr)
        return r.stdout.strip(), r.stderr.strip()

    def ready(self, cwd=None):
        out, _ = self.pm(cwd or self.lai, "ready", "--json")
        return [t["id"] for t in json.loads(out)]

    def block(self, form="{id}"):
        return self.pm(self.lai, "dep", form.format(id=self.blocker), "blocks", self.gate)

    def test_dep_writes_blocked_by_on_the_gate_and_prints_the_arrow(self):
        lin_log = self.log(self.lin)
        out, _ = self.block()
        self.assertEqual(out, f"{self.gate} <--blocked-by-- lin/{self.blocker}")
        gate = json.loads(self.pm(self.lai, "show", self.gate, "--json")[0])
        self.assertEqual(gate["edges"],
                         [{"type": "blocked-by", "to": f"lin/{self.blocker}"}])
        self.assertEqual(self.log(self.lai)[0], f"pm: dep {self.blocker} {self.gate}")
        self.assertEqual(self.log(self.lin), lin_log)
        lin_row = json.loads(self.pm(self.lin, "show", self.blocker, "--json")[0])
        self.assertEqual(lin_row["edges"], [])

    def test_dep_accepts_the_prefix_slash_form_and_refuses_the_colon_form(self):
        out, _ = self.block("lin/{id}")
        self.assertEqual(out, f"{self.gate} <--blocked-by-- lin/{self.blocker}")
        _, err = self.pm(self.lai, "dep", f"lin:{self.blocker}", "blocks", self.gate, rc=1)
        self.assertIn(f"lin/{self.blocker}", err)
        self.assertIn("not <prefix>:<id>", err)
        _, err = self.pm(self.lai, "dep", f"lin/{self.blocker}", "blocks", self.gate, rc=1)
        self.assertIn("edge already exists", err)

    def test_dep_from_an_unrelated_cwd_mutates_the_blocked_stores_repo(self):
        with tempfile.TemporaryDirectory() as bare:
            self.pm(bare, "dep", self.blocker, "blocks", self.gate)
        self.assertEqual(self.log(self.lai)[0], f"pm: dep {self.blocker} {self.gate}")
        self.assertEqual(self.ready(), [self.plain])

    def test_dep_refuses_an_unresolvable_other_side_naming_the_registry(self):
        for other in ("zz-123456", "lin-ffffff"):
            _, err = self.pm(self.lai, "dep", other, "blocks", self.gate, rc=1)
            self.assertIn("pm ticket stores", err)
            self.assertIn("runtime-tools/pm/stores.json", err)
        gate = json.loads(self.pm(self.lai, "show", self.gate, "--json")[0])
        self.assertEqual(gate["edges"], [])

    def test_dep_related_stays_on_the_source_as_prefix_slash_id(self):
        lin_log = self.log(self.lin)
        out, _ = self.pm(self.lai, "dep", self.gate, "related", f"lin/{self.blocker}")
        self.assertEqual(out, f"{self.gate} --related--> lin/{self.blocker}")
        gate = json.loads(self.pm(self.lai, "show", self.gate, "--json")[0])
        self.assertEqual(gate["edges"], [{"type": "related", "to": f"lin/{self.blocker}"}])
        self.assertEqual(self.log(self.lin), lin_log)
        self.assertEqual(self.ready(), [self.gate, self.plain])

    def test_local_pairs_still_run_todays_code(self):
        out, _ = self.pm(self.lai, "dep", self.gate, "blocks", self.plain)
        self.assertEqual(out, f"{self.gate} --blocks--> {self.plain}")
        self.assertEqual(self.ready(), [self.gate])

    def test_create_discovered_from_takes_a_cross_store_id(self):
        out, _ = self.pm(self.lai, "create", "found", "--discovered-from",
                         f"lin/{self.blocker}")
        found = json.loads(self.pm(self.lai, "show", out, "--json")[0])
        self.assertEqual(found["edges"],
                         [{"type": "discovered-from", "to": f"lin/{self.blocker}"}])
        out, _ = self.pm(self.lai, "create", "found 2", "--discovered-from", self.blocker)
        self.assertEqual(json.loads(self.pm(self.lai, "show", out, "--json")[0])["edges"],
                         [{"type": "discovered-from", "to": f"lin/{self.blocker}"}])
        self.pm(self.lai, "create", "x", "--discovered-from", f"lin:{self.blocker}", rc=1)
        _, err = self.pm(self.lai, "create", "x", "--discovered-from", "zz-123456", rc=1)
        self.assertIn("pm ticket stores", err)

    def test_ready_hides_the_gate_until_the_blocker_closes(self):
        self.assertEqual(self.ready(), [self.gate, self.plain])
        self.block()
        self.assertEqual(self.ready(), [self.plain])
        self.pm(self.lin, "claim", self.blocker, "--as", "x")
        self.assertEqual(self.ready(), [self.plain])
        text, _ = self.pm(self.lai, "ready")
        self.assertNotIn(self.gate, text)
        self.pm(self.lin, "close", self.blocker)
        self.assertEqual(self.ready(), [self.gate, self.plain])

    def test_an_unregistered_blocker_keeps_the_gate_hidden(self):
        self.block()
        self.pm(self.lin, "claim", self.blocker, "--as", "x")
        self.pm(self.lin, "close", self.blocker)
        self.write_registry([{"path": self.lai}])
        self.assertEqual(self.ready(), [self.plain])
        out, _ = self.pm(self.lai, "summary")
        self.assertIn(f"{self.gate} <- lin/{self.blocker} (unresolved: "
                      "no registered store owns prefix 'lin')", out)
        self.write_registry([{"path": self.lin}, {"path": self.lai}])
        self.assertEqual(self.ready(), [self.gate, self.plain])

    def test_json_projections_keep_their_shape(self):
        def snap():
            return {
                "ready": json.loads(self.pm(self.lai, "ready", "--json")[0]),
                "summary": json.loads(self.pm(self.lai, "summary", "--json")[0]),
                "show": json.loads(self.pm(self.lai, "show", self.plain, "--json")[0]),
                "gate": json.loads(self.pm(self.lai, "show", self.gate, "--json")[0]),
                "tree": json.loads(self.pm(self.lai, "tree", self.gate, "--json")[0]),
                "list": json.loads(self.pm(self.lai, "list", "--json")[0]),
            }
        before = snap()
        self.block()
        after = snap()
        for key in ("ready", "summary", "show", "tree"):
            self.assertEqual(shape(before[key]), shape(after[key]), key)
        self.assertEqual({t["id"] for t in after["ready"]}, {self.plain})
        for row in after["ready"] + after["list"]:
            self.assertEqual(set(row), ROW_KEYS)
        self.assertEqual(set(after["gate"]), ROW_KEYS | {"blocked_by", "blocks",
                                                        "children", "ready"})
        self.assertEqual((after["gate"]["blocked_by"], after["gate"]["ready"]), ([], False))
        self.assertEqual(set(after["summary"]),
                         {"semaphores", "claimed", "unmerged", "ready", "open_total"})
        self.assertEqual(after["tree"], {"id": self.gate, "impacts": [],
                                         "blocked_by_chain": [], "subtree": []})
        for key in ("summary", "tree"):
            self.assertNotIn("lin/", json.dumps(after[key]))
        lin_tree = json.loads(self.pm(self.lin, "tree", self.blocker, "--json")[0])
        self.assertEqual(lin_tree["impacts"], [])

    def test_claim_refusal_names_the_remote_blocker_and_its_status(self):
        self.block()
        _, err = self.pm(self.lai, "claim", self.gate, "--as", "x", rc=1)
        self.assertIn(f"blocked by: lin/{self.blocker} (open)", err)
        self.pm(self.lin, "claim", self.blocker, "--as", "x")
        _, err = self.pm(self.lai, "claim", self.gate, "--as", "x", rc=1)
        self.assertIn(f"lin/{self.blocker} (claimed)", err)
        self.write_registry([{"path": self.lai}])
        _, err = self.pm(self.lai, "claim", self.gate, "--as", "x", rc=1)
        self.assertIn(f"lin/{self.blocker} (unresolved: no registered store owns "
                      "prefix 'lin')", err)
        self.pm(self.lai, "claim", self.gate, "--as", "x", "--force")
        self.assertIn("claimed", self.pm(self.lai, "show", self.gate)[0])

    def test_summary_lists_waiting_gates_in_text_only(self):
        self.assertNotIn("waiting on other stores:", self.pm(self.lai, "summary")[0])
        self.block()
        self.pm(self.lin, "claim", self.blocker, "--as", "x")
        out, _ = self.pm(self.lai, "summary")
        self.assertIn(f"waiting on other stores:\n  {self.gate} <- lin/{self.blocker} (claimed)",
                      out)
        self.assertNotIn("waiting", self.pm(self.lai, "summary", "--json")[0])
        self.pm(self.lin, "close", self.blocker)
        self.assertNotIn("waiting on other stores:", self.pm(self.lai, "summary")[0])

    def test_show_lists_remote_blockers_and_the_reverse_line(self):
        self.block()
        self.pm(self.lin, "claim", self.blocker, "--as", "x")
        out, _ = self.pm(self.lai, "show", self.gate)
        self.assertIn(f"blocked_by: lin/{self.blocker} (claimed)", out)
        out, _ = self.pm(self.lin, "show", self.blocker)
        self.assertIn(f"blocks (other stores): lai/{self.gate}", out)
        out, _ = self.pm(self.lin, "show", self.blocker, "--json")
        self.assertNotIn("other stores", out)
        self.assertNotIn("lai/", out)
        self.pm(self.lin, "close", self.blocker)
        self.assertNotIn("blocked_by:", self.pm(self.lai, "show", self.gate)[0])

    def test_tree_shows_remote_blockers_as_leaves(self):
        self.block()
        out, _ = self.pm(self.lai, "tree", self.gate)
        self.assertIn(f"blocked-by chain:\n  lin/{self.blocker} [open] init work\n"
                      "epic subtree:", out)
        self.write_registry([{"path": self.lai}])
        out, _ = self.pm(self.lai, "tree", self.gate)
        self.assertIn(f"  lin/{self.blocker} [unresolved: no registered store owns "
                      "prefix 'lin']", out)

    def test_unlink_blocks_removes_the_blocked_by_in_either_form(self):
        self.block()
        out, _ = self.pm(self.lai, "unlink", self.blocker, self.gate, "--type", "blocks")
        self.assertEqual(out, f"{self.gate}: removed 1 edge(s) to lin/{self.blocker}")
        self.assertEqual(self.ready(), [self.gate, self.plain])
        self.block()
        with tempfile.TemporaryDirectory() as bare:
            self.pm(bare, "unlink", f"lin/{self.blocker}", self.gate, "--type", "blocks")
        self.assertEqual(self.ready(), [self.gate, self.plain])
        self.block()
        self.pm(self.lai, "unlink", self.gate, f"lin/{self.blocker}",
                "--type", "blocked-by")
        self.assertEqual(self.ready(), [self.gate, self.plain])
        self.block()
        _, err = self.pm(self.lin, "unlink", self.blocker, self.gate, rc=1)
        self.assertIn("--type blocks", err)
        self.pm(self.lin, "unlink", self.blocker, self.gate, "--type", "blocks")
        self.assertEqual(self.ready(), [self.gate, self.plain])

    def test_validate_flags_a_blocked_by_without_a_cross_store_target(self):
        path = os.path.join(self.lai, ".pm", "tickets.jsonl")
        with open(path) as f:
            rows = [json.loads(x) for x in f if x.strip()]
        for r in rows:
            if r["id"] == self.gate:
                r["edges"] = [{"type": "blocked-by", "to": self.plain}]
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        data = json.loads(self.pm(self.lai, "validate", "--json", rc=1)[0])
        self.assertEqual([p["invariant"] for p in data["problems"]], ["I-04"])
        self.assertIn("cross-store", data["problems"][0]["message"])
        self.pm(self.lai, "unlink", self.gate, self.plain, "--type", "blocked-by")
        self.pm(self.lai, "validate")
        self.block()
        self.pm(self.lai, "validate")

    def test_stores_check_reports_dangling_and_blocker_side_edges(self):
        self.block()
        out, _ = self.pm(self.lai, "stores", "--check")
        self.assertIn("OK: 2 stores", out)
        self.write_registry([{"path": self.lai}])
        out, _ = self.pm(self.lai, "stores", "--check", rc=2)
        self.assertIn(f"{self.gate} blocked-by edge to lin/{self.blocker} dangles "
                      "(unresolved: no registered store owns prefix 'lin')", out)
        self.write_registry([{"path": self.lin}, {"path": self.lai}])
        path = os.path.join(self.lin, ".pm", "tickets.jsonl")
        with open(path) as f:
            rows = [json.loads(x) for x in f if x.strip()]
        rows[0]["edges"] = [{"type": "blocks", "to": f"lai/{self.gate}"},
                            {"type": "related", "to": "lai/lai-ffffff"}]
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        out, _ = self.pm(self.lai, "stores", "--check", rc=2)
        self.assertIn(f"{self.blocker} holds a cross-store blocks edge to "
                      f"lai/{self.gate}", out)
        self.assertIn(f"{self.blocker} related edge to lai/lai-ffffff dangles", out)

    def test_local_only_stores_never_read_the_registry(self):
        with open(self.registry, "w") as f:
            f.write("{nope")
        self.assertEqual(self.ready(), [self.gate, self.plain])
        self.assertIn("ticket store:", self.pm(self.lai, "summary")[0])
        self.block_with_broken_registry()

    def block_with_broken_registry(self):
        path = os.path.join(self.lai, ".pm", "tickets.jsonl")
        with open(path) as f:
            rows = [json.loads(x) for x in f if x.strip()]
        for r in rows:
            if r["id"] == self.gate:
                r["edges"] = [{"type": "blocked-by", "to": f"lin/{self.blocker}"}]
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        self.assertEqual(self.ready(), [self.plain])
        _, err = self.pm(self.lai, "claim", self.gate, "--as", "x", rc=1)
        self.assertIn("cannot read store registry", err)
        self.assertIn(self.registry, err)


FB272D_TITLE = "bin/test --hermetic: governance-lint fails on the delegate's hermetic SKIP"
FB272D_BODY = (
    "bin/test --hermetic on 2026-10-12: governance-lint@claude tests/test-governance-lint.py "
    "fails 2 cases ('real repo: exit 0', 'summary line present') because the projection "
    "delegate prints 'SKIP dispatch projection check (FRONTIER_TEST_HERMETIC=1)' and the "
    "lint reports it as ERROR; skill-dispatch@claude projection check exits 2 "
    "(DEGRADED). Not confirmed on a clean main. Fix: treat the hermetic SKIP as skipped, "
    "not an error, in the governance-lint test or the lint. Gate: bin/test --hermetic all green.")
F642EE_TITLE = ("governance-lint treats the projection delegate's hermetic SKIP as an error, "
                "failing bin/test --hermetic")
F642EE_BODY = (
    "bin/test --hermetic: governance-lint@claude tests/test-governance-lint.py fails 2/20 "
    "('real repo: exit 0', 'real repo: summary line present'): the projection delegate prints "
    "'SKIP dispatch projection check (FRONTIER_TEST_HERMETIC=1): reads the live claude-repo "
    "routing matrix' and governance-lint reports that skip as 'ERROR projection: delegate "
    "reported invocation/environment error'. A hermetic skip should be a skip, not an error. "
    "Not covered by fr-7ad0ae (PATH/identity). Reproduce: python3 ~/frontier/bin/test --hermetic.")
UNRELATED = [
    ("Worktree preflight: detect unprofiled repo and tracked .vscode before sandboxed add/remove",
     "wt start fails inside the sandbox when the repo has no permission profile."),
    ("pm ticket create: duplicate guard refuses when an open or recently closed ticket shares "
     "the title/body tokens",
     "Done in runtime-tools/pm/ticket/src/ticket cmd_create and ticket_core: before insert, "
     "tokenise title+body and score every row."),
]


class DuplicateGuardTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        run(self.store, "init", "--prefix", "tt")

    def create(self, title, body, *extra, expect=0):
        return run(self.store, "create", title, "--body", body, *extra, expect=expect)

    def rows(self):
        with open(os.path.join(self.store, V2_TICKET_PATH)) as f:
            return [json.loads(line) for line in f if line.strip()]

    def refusal(self, title, body, *extra):
        r = subprocess.run([sys.executable, TICKET_CLI, "create", title, "--body", body, *extra],
                           cwd=self.store, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stderr)
        return r

    def test_642ee5_text_matches_fb272d_text(self):
        first = self.create(FB272D_TITLE, FB272D_BODY)
        r = self.refusal(F642EE_TITLE, F642EE_BODY)
        self.assertIn(f"possible duplicate: {first} open {FB272D_TITLE}", r.stderr)
        self.assertEqual(len(self.rows()), 1)

    def test_match_survives_closing_within_the_window(self):
        first = self.create(FB272D_TITLE, FB272D_BODY)
        run(self.store, "close", first)
        r = self.refusal(F642EE_TITLE, F642EE_BODY)
        self.assertIn(f"possible duplicate: {first} closed", r.stderr)

    def test_json_prints_the_candidates(self):
        first = self.create(FB272D_TITLE, FB272D_BODY)
        r = self.refusal(F642EE_TITLE, F642EE_BODY, "--json")
        cands = json.loads(r.stdout)["possible_duplicates"]
        self.assertEqual([c["id"] for c in cands], [first])

    def test_unrelated_tickets_are_not_flagged(self):
        self.create(FB272D_TITLE, FB272D_BODY)
        self.create(F642EE_TITLE, F642EE_BODY, "--new")
        for title, body in UNRELATED:
            self.create(title, body)
        self.assertEqual(len(self.rows()), 4)

    def test_dup_of_appends_a_sighting_and_writes_no_row(self):
        first = self.create(FB272D_TITLE, FB272D_BODY)
        out = self.create(F642EE_TITLE, F642EE_BODY, "--dup-of", first,
                          "--discovered-from", first)
        self.assertEqual(out, first)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        note = rows[0]["notes"][-1]["text"]
        self.assertRegex(note, rf"^sighting \d{{4}}-\d\d-\d\d \(found in {first}\): ")
        self.assertTrue(note.endswith(F642EE_TITLE))

    def test_new_writes_the_row_and_the_marker(self):
        first = self.create(FB272D_TITLE, FB272D_BODY)
        second = self.create(F642EE_TITLE, F642EE_BODY, "--new")
        by_id = {r["id"]: r for r in self.rows()}
        self.assertNotIn("dedupe_overridden", by_id[first])
        self.assertIs(by_id[second]["dedupe_overridden"], True)
        run(self.store, "validate")

    def test_dup_of_and_new_conflict(self):
        first = self.create(FB272D_TITLE, FB272D_BODY)
        run(self.store, "create", "x", "--dup-of", first, "--new", expect=1)


class HelpTextTest(unittest.TestCase):
    """fr-84c506: help strings match the code's exit codes, spec version and
    check lists."""

    def help(self, *argv):
        with tempfile.TemporaryDirectory() as d:
            return " ".join(run(d, *argv, "--help").split())

    def test_epilog_exit_codes(self):
        h = self.help()
        self.assertIn("1 TicketError refusal", h)
        self.assertIn("or validate/lint found problems", h)
        self.assertIn("2 argparse usage error, validate/lint found no store", h)
        self.assertNotIn("2 validate/lint found problems", h)

    def test_validate_help_names_version_and_exits(self):
        h = self.help("validate")
        self.assertNotIn("spec/v1", h)
        self.assertIn("exit 1 on problems, 2 on no/unreadable store", h)

    def test_stores_check_help_names_checks(self):
        h = self.help("stores")
        for needle in ("missing paths", "bad configs", "foreign prefix",
                       "dangling cross-store edges", "blocks edges held on the "
                       "blocker", "frozen-only prefix collisions", "exit 2"):
            self.assertIn(needle, h)


if __name__ == "__main__":
    unittest.main(verbosity=1)
