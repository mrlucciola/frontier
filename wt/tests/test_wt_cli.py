"""Black-box characterization of the wt verbs, run against any wt executable.

Run through run_wt.py, which sets:
    WT_CLI_UNDER_TEST  absolute path of the wt executable
    WT_PM_SIDE         old (installed `pm ticket ...`) or new (pm/cli/pm)
    WT_UNBUILT_LOG     file the new wt appends to when it answers exit 70 for a verb
                       it has not built yet (the pending rule)

Nothing here imports wt or pm. Every repo is built under a fresh temporary directory
with a private HOME, a private bin dir whose `pm` is the side's pm, a fixed git
identity and no inherited identity variables. Statuses compare in the new words:
open, taken, parked, done.
"""
import json
import os
import shlex
import shutil
import stat
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
WT_REPO = os.path.dirname(os.path.dirname(HERE))
NEW_PM = os.path.join(WT_REPO, "pm", "cli", "pm")
OLD_PM = "/Users/matthias/.local/libexec/pm/cli/pm"

CLI = os.environ.get("WT_CLI_UNDER_TEST", "")
SIDE = os.environ.get("WT_PM_SIDE", "old")
UNBUILT_LOG = os.environ.get("WT_UNBUILT_LOG", "")

IDENTITY_VARS = ("CLAUDE_CODE_SESSION_ID", "CLAUDECODE", "CODEX_THREAD_ID",
                 "CODEX_AGENT_IDENTITY", "PM_AGENT", "WT_ACTOR", "PM_SESSION_ID",
                 "PM_ACTOR")
OLD_STATUS = {"open": "open", "claimed": "taken", "done-unmerged": "parked",
              "closed": "done"}


class Pending(Exception):
    """The wt under test answered exit 70 and logged an unbuilt verb."""


class Unavailable(Exception):
    """An adapter method this side cannot implement."""


def unbuilt_size():
    try:
        return os.path.getsize(UNBUILT_LOG)
    except OSError:
        return 0


def sh(argv, cwd, env, check=True):
    done = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=120)
    if check and done.returncode != 0:
        raise AssertionError("%s failed (%d): %s%s" % (
            shlex.join(argv), done.returncode, done.stdout, done.stderr))
    return done


class Result:
    def __init__(self, done):
        self.code = done.returncode
        self.out = done.stdout
        self.err = done.stderr
        self.text = done.stdout + done.stderr

    def lines(self):
        return self.text.splitlines()

    def has_line(self, prefix):
        return any(line.startswith(prefix) for line in self.lines())


# ---------------------------------------------------------------- pm adapters
class PmAdapter:
    """One interface over the two pms. `env` is the isolated environment (identity
    variables already removed); a call that needs a session passes it explicitly."""

    def __init__(self, env, plugins_dir):
        self.env = env
        self.plugins_dir = plugins_dir

    def _call(self, argv, cwd, session=None, check=True):
        env = dict(self.env)
        if session:
            env["PM_SESSION_ID"] = session
        return sh(argv, cwd, env, check)

    def _git(self, repo, *args, check=True):
        return sh(["git", "-C", repo] + list(args), repo, self.env, check)

    def _commit_paths(self, repo, paths, message):
        existing = [p for p in paths if os.path.exists(os.path.join(repo, p))]
        self._git(repo, "add", "--", *existing)
        if self._git(repo, "diff", "--cached", "--quiet", check=False).returncode != 0:
            self._git(repo, "commit", "-q", "-m", message)

    def _edit_config(self, repo, **keys):
        path = os.path.join(repo, ".pm", "config.json")
        cfg = {}
        if os.path.exists(path):
            with open(path) as f:
                cfg = json.load(f)
        cfg.update(keys)
        with open(path, "w") as f:
            json.dump(cfg, f)
        self._commit_paths(repo, [".pm/config.json"], "store config")

    def make_store(self, repo, prefix, findings_required=False):
        raise NotImplementedError

    def file_ticket(self, repo, title, labels=()):
        raise NotImplementedError

    def status(self, repo, ticket):
        raise NotImplementedError

    def holder(self, repo, ticket):
        raise NotImplementedError

    def notes(self, repo, ticket):
        raise NotImplementedError

    def take(self, repo, ticket, actor, session=None, force=False):
        raise NotImplementedError

    def park(self, repo, ticket, text, actor=None, session=None):
        raise NotImplementedError

    def block(self, repo, blocked, blocker):
        raise NotImplementedError

    def set_gate(self, repo, argv=None, malformed=None):
        raise NotImplementedError

    def add_known_red(self, repo, ticket, match):
        raise NotImplementedError

    def guard_refuse_done(self, repo):
        """After this, closing a ticket is refused by pm after wt's merge. On the old
        side the ticket must have been filed with labels=("tooling",)."""
        raise NotImplementedError


class OldPm(PmAdapter):
    def _pm(self, repo, *args, session=None, check=True):
        return self._call(["pm", "ticket"] + list(args), repo, session, check)

    def make_store(self, repo, prefix, findings_required=False):
        self._pm(repo, "init", "--prefix", prefix, "--dir", repo)
        self._commit_paths(repo, [".gitignore"], "store ignore")
        if findings_required:
            self._edit_config(repo, findings_required=True)

    def file_ticket(self, repo, title, labels=()):
        args = ["create", title, "--new"]
        for label in labels:
            args += ["--label", label]
        return self._pm(repo, *args).stdout.strip().splitlines()[-1]

    def _show(self, repo, ticket):
        return json.loads(self._pm(repo, "show", ticket, "--json").stdout)

    def status(self, repo, ticket):
        return OLD_STATUS[self._show(repo, ticket)["status"]]

    def holder(self, repo, ticket):
        return self._show(repo, ticket).get("assignee") or ""

    def notes(self, repo, ticket):
        return [n["text"] if isinstance(n, dict) else str(n)
                for n in self._show(repo, ticket).get("notes", [])]

    def take(self, repo, ticket, actor, session=None, force=False):
        args = ["claim", ticket, "--as", actor]
        if session:
            args += ["--session", session]
        if force:
            args.append("--force")
        self._pm(repo, *args)

    def park(self, repo, ticket, text, actor=None, session=None):
        self._pm(repo, "close", ticket, "--unmerged", "--note", text, "--via", "wt",
                 session=session)

    def block(self, repo, blocked, blocker):
        self._pm(repo, "dep", blocker, "blocks", blocked)

    def set_gate(self, repo, argv=None, malformed=None):
        self._edit_config(repo, gate=argv if malformed is None else malformed)

    def add_known_red(self, repo, ticket, match):
        path = os.path.join(repo, ".pm", "config.json")
        with open(path) as f:
            entries = json.load(f).get("known_red", [])
        entries.append({"match": match, "ticket": ticket, "since": "2026-01-01"})
        self._edit_config(repo, known_red=entries)

    def guard_refuse_done(self, repo):
        tool = os.path.join(repo, "bin", "deploy")
        os.makedirs(os.path.dirname(tool), exist_ok=True)
        with open(tool, "w") as f:
            f.write("#!/bin/sh\necho 'package not deployed current'\nexit 1\n")
        os.chmod(tool, 0o755)
        self._commit_paths(repo, ["bin/deploy"], "deploy close-check stub")


class NewPm(PmAdapter):
    def _pm(self, repo, *args, session=None, check=True):
        return self._call(["pm"] + list(args), repo, session, check)

    def make_store(self, repo, prefix, findings_required=False):
        self._pm(repo, "init", prefix)
        self._commit_paths(repo, [".gitignore", ".pm/config.json"], "store")
        if findings_required:
            self._edit_config(repo, findings_required=True)

    def file_ticket(self, repo, title, labels=()):
        args = ["new", title, "--new"]
        for label in labels:
            args += ["-l", label]
        return self._pm(repo, *args).stdout.strip().splitlines()[-1]

    def status(self, repo, ticket):
        return self._pm(repo, "get", ticket, "status").stdout.strip()

    def holder(self, repo, ticket):
        return self._pm(repo, "get", ticket, "holder").stdout.strip()

    def notes(self, repo, ticket):
        texts = []
        for line in self._pm(repo, "log", ticket).stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("text"):
                texts.append(event["text"])
        return texts

    def take(self, repo, ticket, actor, session=None, force=False):
        args = ["take", ticket, "--as", actor]
        if force:
            args.append("--force")
        self._pm(repo, *args, session=session)

    def park(self, repo, ticket, text, actor=None, session=None):
        self._pm(repo, "park", ticket, "-m", text, session=session)

    def block(self, repo, blocked, blocker):
        self._pm(repo, "link", blocker, "blocks", blocked)

    def set_gate(self, repo, argv=None, malformed=None):
        if malformed is not None:
            raise Unavailable("new side has no malformed gate value: .wt/gate is "
                              "an executable file, its contract case is undefined")
        path = os.path.join(repo, ".wt", "gate")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("#!/bin/sh\nexec %s\n" % shlex.join(argv))
        os.chmod(path, 0o755)
        self._commit_paths(repo, [".wt/gate"], "gate")

    def add_known_red(self, repo, ticket, match):
        path = os.path.join(repo, ".wt", "known-red")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write("%s %s\n" % (ticket, match))
        self._commit_paths(repo, [".wt/known-red"], "known red")

    def guard_refuse_done(self, repo):
        plugin = os.path.join(self.plugins_dir, "guard")
        os.makedirs(plugin, exist_ok=True)
        hook = os.path.join(plugin, "pre-done")
        with open(hook, "w") as f:
            f.write("#!/bin/sh\necho 'guard: not yet'\nexit 1\n")
        os.chmod(hook, os.stat(hook).st_mode | stat.S_IXUSR)


# ------------------------------------------------------------------- the base
class WtCase(unittest.TestCase):
    """The isolated environment, the one wt-runner helper and the repo fixture."""

    def setUp(self):
        if not CLI or not os.path.isfile(CLI):
            self.fail("WT_CLI_UNDER_TEST is not a file: %r" % CLI)
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="wt-t-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        for name in ("home", "bin", "plugins", "faults", "repos"):
            os.mkdir(os.path.join(self.root, name))
        pm = NEW_PM if SIDE == "new" else OLD_PM
        os.symlink(pm, os.path.join(self.root, "bin", "pm"))
        stores = os.path.join(self.root, "old-stores.json")
        with open(stores, "w") as f:
            json.dump({"stores": []}, f)
        pairs = os.path.join(self.root, "pairs.json")
        with open(pairs, "w") as f:
            json.dump({"pairs": []}, f)
        env = {k: v for k, v in os.environ.items() if k not in IDENTITY_VARS}
        env.update({
            "HOME": os.path.join(self.root, "home"),
            "PATH": os.path.join(self.root, "bin") + ":/usr/bin:/bin",
            "TMPDIR": self.root,
            "LC_ALL": "C",
            "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
            "WT_FAULT_REPORT_DIR": os.path.join(self.root, "faults"),
            "PM_STORES_FILE": stores,
            "PM_TELEMETRY_DIR": "-",
            # Old pm writes `human:<actor>` claims without a provider, which no session
            # could adopt; the agents wt serves always carry one.
            "PM_AGENT": "claude/worker",
            "GIT_PAIRS_FILE": pairs,
            "PM_STORES": os.path.join(self.root, "new-stores"),
            "PM_PLUGINS": os.path.join(self.root, "plugins"),
        })
        self.env = env
        adapter = NewPm if SIDE == "new" else OldPm
        self.pm = adapter(env, os.path.join(self.root, "plugins"))

    def call_env(self, session=None, actor=None):
        env = dict(self.env)
        if session:
            env["PM_SESSION_ID"] = session
        if actor:
            env["WT_ACTOR"] = actor
        return env

    def wt(self, repo, *args, session=None, actor=None, cwd=None):
        """The one helper that runs wt. Returns a Result; ends the test as pending when
        the call exited 70 and appended to $WT_UNBUILT_LOG."""
        before = unbuilt_size()
        done = subprocess.run([CLI] + list(args), cwd=cwd or repo,
                              env=self.call_env(session, actor), capture_output=True,
                              text=True, timeout=180)
        result = Result(done)
        if result.code == 70 and unbuilt_size() > before:
            raise Pending(shlex.join(["wt"] + list(args)))
        return result

    def git(self, repo, *args, check=True):
        return sh(["git", "-C", repo] + list(args), repo, self.env, check)

    def make_repo(self, name="main-repo", prefix="tk", findings_required=False):
        """A fresh repo: git init -b main, one commit, a store made through the adapter."""
        repo = os.path.join(self.root, "repos", name)
        os.mkdir(repo)
        self.git(repo, "init", "-q", "-b", "main")
        with open(os.path.join(repo, "README.md"), "w") as f:
            f.write("seed\n")
        self.git(repo, "add", "--", "README.md")
        self.git(repo, "commit", "-q", "-m", "seed")
        self.pm.make_store(repo, prefix, findings_required)
        return repo

    def worktree(self, repo, ticket):
        return os.path.join(repo, ".worktrees", ticket)

    def branch_exists(self, repo, name):
        return self.git(repo, "rev-parse", "--verify", "-q", "refs/heads/%s" % name,
                        check=False).returncode == 0

    def commit_file(self, where, name, text, message):
        with open(os.path.join(where, name), "w") as f:
            f.write(text)
        self.git(where, "add", "--", name)
        self.git(where, "commit", "-q", "-m", message)

    def assert_wt_line(self, result, prefix):
        self.assertTrue(result.has_line(prefix),
                        "no line starting %r in:\n%s" % (prefix, result.text))


# ---------------------------------------------------------------- adapter alone
class AdapterTest(WtCase):
    """No wt: proves each pm side behind the adapter."""

    def test_make_file_status_take_holder(self):
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "first")
        self.assertTrue(ticket.startswith("tk-"), ticket)
        self.assertEqual(self.pm.status(repo, ticket), "open")
        self.pm.take(repo, ticket, "ada", session="s1")
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertIn("ada", self.pm.holder(repo, ticket))

    def test_park_and_notes(self):
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "second")
        self.pm.take(repo, ticket, "ada", session="s1")
        self.pm.park(repo, ticket, "stopped here", actor="ada", session="s1")
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertTrue(any("stopped here" in n for n in self.pm.notes(repo, ticket)))

    def test_block(self):
        repo = self.make_repo()
        first = self.pm.file_ticket(repo, "blocker one")
        second = self.pm.file_ticket(repo, "blocked two")
        self.pm.block(repo, second, first)
        with self.assertRaises(AssertionError):
            self.pm.take(repo, second, "ada", session="s1")
        self.pm.take(repo, second, "ada", session="s1", force=True)
        self.assertEqual(self.pm.status(repo, second), "taken")

    def test_set_gate_and_known_red(self):
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "gated")
        self.pm.set_gate(repo, ["sh", "-c", "exit 0"])
        self.pm.add_known_red(repo, ticket, "alpha-case")
        self.assertEqual(self.git(repo, "status", "--short").stdout.strip(), "")
        if SIDE == "old":
            with open(os.path.join(repo, ".pm", "config.json")) as f:
                cfg = json.load(f)
            self.assertEqual(cfg["gate"], ["sh", "-c", "exit 0"])
            self.assertEqual(cfg["known_red"][0]["ticket"], ticket)
        else:
            self.assertTrue(os.access(os.path.join(repo, ".wt", "gate"), os.X_OK))
            with open(os.path.join(repo, ".wt", "known-red")) as f:
                self.assertEqual(f.read(), "%s alpha-case\n" % ticket)

    def test_require_findings(self):
        repo = self.make_repo(findings_required=True)
        with open(os.path.join(repo, ".pm", "config.json")) as f:
            self.assertIs(json.load(f)["findings_required"], True)

    def test_malformed_gate(self):
        repo = self.make_repo()
        if SIDE == "new":
            with self.assertRaises(Unavailable):
                self.pm.set_gate(repo, malformed="nope")
            return
        self.pm.set_gate(repo, malformed="not-a-list")
        with open(os.path.join(repo, ".pm", "config.json")) as f:
            self.assertEqual(json.load(f)["gate"], "not-a-list")

    def test_guard_refuses_done(self):
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "guarded", labels=("tooling",))
        self.pm.take(repo, ticket, "ada", session="s1")
        self.commit_file(repo, "f.txt", "x\n", "%s: change" % ticket)
        self.pm.guard_refuse_done(repo)
        if SIDE == "old":
            done = sh(["pm", "ticket", "close", ticket], repo, self.call_env("s1"),
                      check=False)
        else:
            done = sh(["pm", "done", ticket], repo, self.call_env("s1"), check=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(self.pm.status(repo, ticket), "taken")


# ---------------------------------------------------------------------- start
class StartTest(WtCase):
    def test_claims_and_adds_worktree(self):
        """`start` ... claim via pm ... add/resume the worktree; a worktree always lives at
        `<target_repo>/.worktrees/<id>` on branch `<id>`."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "work")
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(result.out.startswith("OK: %s -> " % ticket), result.out)
        printed = result.out.splitlines()[0].split(" -> ", 1)[1]
        wt_path = self.worktree(repo, ticket)
        self.assertEqual(os.path.realpath(printed), os.path.realpath(wt_path))
        self.assertTrue(os.path.isdir(wt_path))
        head = self.git(wt_path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(head, ticket)
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertIn("ada", self.pm.holder(repo, ticket))

    def test_resumes_existing_branch(self):
        """`start` ... add/resume the worktree: an existing branch `<id>` is checked
        out again, rebased onto the default branch."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "resume")
        self.git(repo, "branch", ticket)
        self.git(repo, "switch", "-q", ticket)
        self.commit_file(repo, "mine.txt", "mine\n", "%s: work" % ticket)
        self.git(repo, "switch", "-q", "main")
        self.commit_file(repo, "later.txt", "later\n", "main moves")
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s -> " % ticket)
        wt_path = self.worktree(repo, ticket)
        self.assertTrue(os.path.isfile(os.path.join(wt_path, "mine.txt")))
        self.assertTrue(os.path.isfile(os.path.join(wt_path, "later.txt")))

    def test_resumes_parked_ticket(self):
        """`start` ... `done-unmerged` ... Resume later with `wt start`: a parked ticket
        is taken again and its branch is checked out."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "parked work")
        self.pm.take(repo, ticket, "ada", session="s1")
        self.git(repo, "branch", ticket)
        self.git(repo, "switch", "-q", ticket)
        self.commit_file(repo, "kept.txt", "kept\n", "%s: work" % ticket)
        self.git(repo, "switch", "-q", "main")
        self.pm.park(repo, ticket, "parked for test", actor="ada", session="s1")
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s -> " % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertTrue(os.path.isfile(os.path.join(self.worktree(repo, ticket), "kept.txt")))

    def test_adopts_own_claim(self):
        """`start` adopts a ticket that is already `claimed` by the claim it would itself
        write (same provider/actor and same session token) ... prints one `adopting
        existing claim` line and skips the claim."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "own")
        self.pm.take(repo, ticket, "ada", session="s1")
        holder = self.pm.holder(repo, ticket)
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "adopting existing claim on %s" % ticket)
        self.assertEqual(sum(1 for l in result.lines()
                             if l.startswith("adopting existing claim")), 1)
        self.assert_wt_line(result, "OK: %s -> " % ticket)
        self.assertTrue(os.path.isdir(self.worktree(repo, ticket)))
        self.assertEqual(self.pm.holder(repo, ticket), holder)

    def _refused(self, taker, take_session, start_actor, start_session):
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "foreign")
        self.pm.take(repo, ticket, taker, session=take_session)
        holder = self.pm.holder(repo, ticket)
        result = self.wt(repo, "start", ticket, "--as", start_actor, session=start_session)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: ticket %s is not claimable" % ticket)
        self.assertFalse(result.has_line("adopting existing claim"))
        self.assertFalse(os.path.exists(self.worktree(repo, ticket)))
        self.assertFalse(self.branch_exists(repo, ticket))
        self.assertEqual(self.pm.holder(repo, ticket), holder)

    def test_refuses_foreign_claim_other_token(self):
        """A different token ... still refuses (`ticket <id> is not claimable`)."""
        self._refused("ada", "s1", "ada", "s2")

    def test_refuses_foreign_claim_other_actor(self):
        """A different actor ... still refuses (`ticket <id> is not claimable`)."""
        self._refused("ada", "s1", "bob", "s1")

    def test_refuses_bare_name_claim(self):
        """A bare-name claim still refuses (`ticket <id> is not claimable`)."""
        self._refused("ada", None, "ada", "s1")

    def test_unknown_ticket_not_claimable(self):
        """`ticket <id> is not claimable` from `start` means taken or refused."""
        repo = self.make_repo()
        result = self.wt(repo, "start", "tk-nope", "--as", "ada", session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: ticket tk-nope is not claimable")
        self.assertFalse(os.path.exists(self.worktree(repo, "tk-nope")))

    def test_blocked_ticket_needs_force_and_prints_park_reminder(self):
        """`wt start --force` passes `--force` to `pm ticket claim` (blocked ticket) ...
        end a force-claimed ticket with `wt park`, never `wt finish` (start prints a
        reminder)."""
        repo = self.make_repo()
        blocker = self.pm.file_ticket(repo, "blocker")
        blocked = self.pm.file_ticket(repo, "blocked")
        self.pm.block(repo, blocked, blocker)
        refused = self.wt(repo, "start", blocked, "--as", "ada", session="s1")
        self.assertNotEqual(refused.code, 0, refused.text)
        self.assert_wt_line(refused, "wt: ticket %s is not claimable" % blocked)
        self.assertEqual(self.pm.status(repo, blocked), "open")
        forced = self.wt(repo, "start", blocked, "--as", "ada", "--force", session="s1")
        self.assertEqual(forced.code, 0, forced.text)
        self.assert_wt_line(forced, "forced claim on %s" % blocked)
        reminder = [l for l in forced.lines() if l.startswith("forced claim on")][0]
        self.assertIn("wt park", reminder)
        self.assertIn("never `wt finish`", reminder)
        self.assert_wt_line(forced, "OK: %s -> " % blocked)
        self.assertEqual(self.pm.status(repo, blocked), "taken")

    def test_unforced_start_prints_no_force_reminder(self):
        """`start --force` ... (start prints a reminder): only a forced claim does."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "plain")
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(result.has_line("forced claim"))

    def test_as_defaults_to_wt_actor(self):
        """`--as` defaults to `$WT_ACTOR` when set."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "actor")
        result = self.wt(repo, "start", ticket, session="s1", actor="zed")
        self.assertEqual(result.code, 0, result.text)
        self.assertIn("zed", self.pm.holder(repo, ticket))

    def test_no_actor_refuses_before_claim(self):
        """`--as` defaults to `$WT_ACTOR` when set: with neither, start claims nothing."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "nobody")
        result = self.wt(repo, "start", ticket, session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assertTrue(result.has_line("wt:"), result.text)
        self.assertEqual(self.pm.status(repo, ticket), "open")
        self.assertFalse(os.path.exists(self.worktree(repo, ticket)))

    def test_refuses_to_resume_mass_deleting_wip_tip(self):
        """`start` refuses to resume a branch whose tip is a mass-deleting `WIP: park`
        commit."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "wiped")
        self.git(repo, "switch", "-q", "-c", "stage")
        bulk = os.path.join(repo, "bulk")
        os.mkdir(bulk)
        for n in range(60):
            with open(os.path.join(bulk, "f%02d.txt" % n), "w") as f:
                f.write("%d\n" % n)
        self.git(repo, "add", "--", "bulk")
        self.git(repo, "commit", "-q", "-m", "bulk files")
        self.git(repo, "switch", "-q", "main")
        self.git(repo, "merge", "-q", "--ff-only", "stage")
        self.git(repo, "branch", "-q", "-d", "stage", check=False)
        self.git(repo, "switch", "-q", "-c", ticket)
        self.git(repo, "rm", "-q", "-r", "--", "bulk")
        self.git(repo, "commit", "-q", "-m", "WIP: park %s" % ticket)
        self.git(repo, "switch", "-q", "main")
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: refusing to resume %s" % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "open")
        self.assertFalse(os.path.exists(self.worktree(repo, ticket)))


# Parts 2 to 4 fill these in. Keep the names: the overseer's prompts address them.
class FinishTest(WtCase):
    pass


class ParkTest(WtCase):
    pass


class StatusPruneTest(WtCase):
    pass


class ResolutionTest(WtCase):
    pass


if __name__ == "__main__":
    unittest.main()
