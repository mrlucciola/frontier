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

    def findings(self, repo, ticket):
        """The findings recorded on a closed ticket, as `none` or comma-joined ids."""
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

    def findings(self, repo, ticket):
        shown = self._show(repo, ticket)
        if shown.get("findings_absent"):
            return "none"
        return ",".join(shown.get("findings") or [])

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

    def findings(self, repo, ticket):
        value = json.loads(self._pm(repo, "show", ticket, "--json").stdout)["findings"]
        if isinstance(value, list):
            return ",".join(value) or "none"
        return value or "none"

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
        path = os.path.join(repo, ".wt", "gate")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            if malformed is not None:
                f.write("#!/bin/sh\nexit 0\n")
            else:
                f.write("#!/bin/sh\nexec %s\n" % shlex.join(argv))
        os.chmod(path, 0o644 if malformed is not None else 0o755)
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
            self.pm.set_gate(repo, malformed="nope")
            path = os.path.join(repo, ".wt", "gate")
            self.assertTrue(os.path.isfile(path))
            self.assertFalse(os.access(path, os.X_OK))
            self.assertEqual(self.git(repo, "status", "--short").stdout.strip(), "")
            return
        self.pm.set_gate(repo, malformed="not-a-list")
        with open(os.path.join(repo, ".pm", "config.json")) as f:
            self.assertEqual(json.load(f)["gate"], "not-a-list")

    def test_findings_reader(self):
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "closing")
        self.pm.take(repo, ticket, "ada", session="s1")
        if SIDE == "old":
            argv = ["pm", "ticket", "close", ticket, "--findings", "none"]
        else:
            argv = ["pm", "done", ticket, "--findings", "none", "-m", "checked"]
        sh(argv, repo, self.call_env("s1"))
        self.assertEqual(self.pm.findings(repo, ticket), "none")

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


class FinishTest(WtCase):
    def started(self, gate=None, findings_required=False, red=None, malformed=None,
                name="main-repo", labels=()):
        """A repo with a ticket started by wt and one commit in its worktree. `red` is a
        match string registered as a known red for the ticket. Returns
        (repo, ticket, worktree)."""
        repo = self.make_repo(name=name, findings_required=findings_required)
        ticket = self.pm.file_ticket(repo, "work", labels=labels)
        if gate is not None or malformed is not None:
            self.pm.set_gate(repo, gate, malformed=malformed)
        if red:
            self.pm.add_known_red(repo, ticket, red)
        started = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(started.code, 0, started.text)
        wt_path = self.worktree(repo, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        return repo, ticket, wt_path

    def finish(self, repo, ticket, *args):
        return self.wt(repo, "finish", ticket, *args, session="s1")

    def head(self, repo):
        return self.git(repo, "rev-parse", "main").stdout.strip()

    def assert_untouched(self, repo, ticket, wt_path, before):
        """Nothing merged, worktree intact, ticket still taken."""
        self.assertEqual(self.head(repo), before)
        self.assertTrue(os.path.isdir(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def sh_gate(self, script):
        return ["sh", "-c", script]

    def test_finish_merges_and_closes(self):
        """`finish` ... gate, rebase, ff-only merge, teardown, close: merged into the
        default branch, worktree and branch removed, ticket done."""
        repo, ticket, wt_path = self.started()
        result = self.finish(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(result.out.startswith("OK: %s merged into main, " % ticket),
                        result.text)
        self.assertFalse(os.path.exists(wt_path))
        ok_line = [l for l in result.lines() if l.startswith("OK: ")][-1]
        if "deferred" not in ok_line:
            self.assertFalse(self.branch_exists(repo, ticket))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "done")

    def test_finish_is_fast_forward_only(self):
        """`finish` ... ff-only merge: the branch commit itself lands on main."""
        repo, ticket, wt_path = self.started()
        tip = self.git(wt_path, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(self.finish(repo, ticket).code, 0)
        self.git(repo, "merge-base", "--is-ancestor", tip, "main")

    def test_note_and_findings_reach_the_close(self):
        """`finish [--note TEXT] [--findings VALUE]`: both are recorded on the close."""
        repo, ticket, wt_path = self.started()
        result = self.finish(repo, ticket, "--note", "closing-note-xyz", "--findings",
                             "none")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(result.has_line("wt: no --findings"), result.text)
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertEqual(self.pm.findings(repo, ticket), "none")
        joined = "\n".join(self.pm.notes(repo, ticket))
        self.assertIn("closing-note-xyz", joined)

    def test_note_omitted_when_not_given(self):
        """`--note` is omitted from the close when not given."""
        repo, ticket, wt_path = self.started()
        self.assertEqual(self.finish(repo, ticket, "--findings", "none").code, 0)
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertEqual([n for n in self.pm.notes(repo, ticket)
                          if "closing-note" in n], [])

    def test_findings_warning_still_finishes(self):
        """`finish` and `park` warn when `--findings` is missing."""
        repo, ticket, wt_path = self.started()
        result = self.finish(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: no --findings")
        self.assertEqual(self.pm.status(repo, ticket), "done")

    def test_findings_required_refuses_before_merge(self):
        """... refuse before any merge or teardown once the store sets
        `findings_required`."""
        repo, ticket, wt_path = self.started(findings_required=True)
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: no --findings")
        self.assert_untouched(repo, ticket, wt_path, before)
        self.assertFalse(os.path.exists(os.path.join(repo, "work.txt")))

    def test_gate_pass_prints_exit_and_skip_count(self):
        """Every run prints `gate <argv> exit N, SKIP lines: K` (output lines matching
        `skip`/`skipped`, case-insensitive)."""
        gate = self.sh_gate("echo 'skip: one'; echo 'Skipped two'; echo fine")
        repo, ticket, wt_path = self.started(gate=gate)
        result = self.finish(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: gate %s exit 0, SKIP lines: 2" % " ".join(gate))
        self.assertEqual(self.pm.status(repo, ticket), "done")

    def test_gate_fail_refuses_and_prints_last_30_lines(self):
        """Non-zero exit refuses the finish: nothing merged, ticket stays claimed,
        worktree intact, and the last 30 lines of output are printed."""
        gate = self.sh_gate("i=1; while [ $i -le 40 ]; do printf 'out-%02d\\n' $i; "
                            "i=$((i+1)); done; exit 3")
        repo, ticket, wt_path = self.started(gate=gate)
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: gate %s exit 3, SKIP lines: 0" % " ".join(gate))
        lines = result.lines()
        for n in range(11, 41):
            self.assertIn("out-%02d" % n, lines)
        for n in range(1, 11):
            self.assertNotIn("out-%02d" % n, lines)
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_gate_runs_in_worktree_before_merge(self):
        """It runs in the worktree (after the dirty-worktree check, before any rebase
        or merge)."""
        marker = os.path.join(self.root, "gate-ran.txt")
        repo = self.make_repo()
        gate = self.sh_gate("pwd > %s; git -C %s rev-parse main >> %s"
                            % (shlex.quote(marker), shlex.quote(repo), shlex.quote(marker)))
        ticket = self.pm.file_ticket(repo, "work")
        self.pm.set_gate(repo, gate)
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada", session="s1").code, 0)
        before = self.head(repo)
        wt_path = self.worktree(repo, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        self.assertEqual(self.finish(repo, ticket).code, 0)
        with open(marker) as f:
            where, main_then = f.read().split()
        self.assertEqual(os.path.realpath(where), os.path.realpath(wt_path))
        self.assertEqual(main_then, before)

    def test_dirty_worktree_refuses_before_gate(self):
        """The gate runs after the dirty-worktree check: a dirty worktree refuses,
        nothing merged, ticket stays claimed, worktree intact."""
        marker = os.path.join(self.root, "gate-ran.txt")
        gate = self.sh_gate("echo ran > %s" % shlex.quote(marker))
        repo, ticket, wt_path = self.started(gate=gate)
        with open(os.path.join(wt_path, "stray.txt"), "w") as f:
            f.write("untracked\n")
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assertTrue(result.has_line("wt: "), result.text)
        self.assertFalse(os.path.exists(marker))
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_malformed_gate_refuses(self):
        """A malformed `gate` (not a list of strings) refuses too -- a typo never turns
        the gate off. (New side: `.wt/gate` present but not executable.)"""
        repo, ticket, wt_path = self.started(malformed="not-a-list")
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assertTrue(result.has_line("wt: "), result.text)
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_no_gate_bypasses_and_notes_it(self):
        """`--no-gate` bypasses it and appends `gate skipped (--no-gate): <argv>` to
        the close note."""
        marker = os.path.join(self.root, "gate-ran.txt")
        gate = self.sh_gate("echo ran > %s; exit 1" % shlex.quote(marker))
        repo, ticket, wt_path = self.started(gate=gate)
        result = self.finish(repo, ticket, "--no-gate")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(os.path.exists(marker))
        self.assertFalse(result.has_line("wt: gate "), result.text)
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertTrue(any("gate skipped (--no-gate): " in n
                            for n in self.pm.notes(repo, ticket)),
                        self.pm.notes(repo, ticket))

    def test_no_gate_configured_prints_no_gate_line(self):
        """No `gate` key, no gate."""
        repo, ticket, wt_path = self.started()
        result = self.finish(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(any("gate " in l and "exit" in l for l in result.lines()),
                         result.text)
        self.assertFalse(any("gate skipped" in n for n in self.pm.notes(repo, ticket)))

    def test_known_red_passes_and_is_noted(self):
        """`known red (<ticket>): <line>` passes (the close note says `known red
        <ticket>`)."""
        gate = self.sh_gate("echo 'FAIL alpha-case'; exit 1")
        repo, ticket, wt_path = self.started(gate=gate, red="alpha-case")
        result = self.finish(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "known red (%s): FAIL alpha-case" % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertTrue(any("known red %s" % ticket in n for n in self.pm.notes(repo, ticket)),
                        self.pm.notes(repo, ticket))

    def test_known_red_uncovered_failure_still_refuses(self):
        """A known red excuses only the lines it matches: another failure line refuses."""
        gate = self.sh_gate("echo 'FAIL alpha-case'; echo 'FAIL beta-case'; exit 1")
        repo, ticket, wt_path = self.started(gate=gate, red="alpha-case")
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_known_red_that_stopped_failing_refuses(self):
        """An entry whose line stopped failing refuses until it is dropped."""
        gate = self.sh_gate("echo 'ok alpha-case'; exit 0")
        repo, ticket, wt_path = self.started(gate=gate, red="alpha-case")
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: known-red now green")
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_land_merges_and_leaves_ticket_taken(self):
        """`wt land` = finish --keep-open: merge + teardown, ticket stays claimed; `wt
        start <id>` from the same session adopts the claim."""
        repo, ticket, wt_path = self.started()
        holder = self.pm.holder(repo, ticket)
        result = self.wt(repo, "land", ticket, session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(result.out.startswith("OK: %s merged into main, " % ticket),
                        result.text)
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertEqual(self.pm.holder(repo, ticket), holder)
        again = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(again.code, 0, again.text)
        self.assert_wt_line(again, "adopting existing claim on %s" % ticket)

    def test_finish_keep_open_is_land(self):
        """`finish --keep-open` (`wt land`) skips the `pm ticket close`."""
        repo, ticket, wt_path = self.started()
        result = self.finish(repo, ticket, "--keep-open")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def test_land_rejects_note_and_findings(self):
        """It rejects `--note`/`--findings` (nothing to attach them to)."""
        repo, ticket, wt_path = self.started()
        before = self.head(repo)
        for flag in ("--note", "--findings"):
            result = self.wt(repo, "land", ticket, flag, "x", session="s1")
            self.assertNotEqual(result.code, 0, result.text)
            self.assertTrue(result.has_line("wt: "), result.text)
            self.assert_untouched(repo, ticket, wt_path, before)

    def test_land_no_gate_prints_skip(self):
        """`--no-gate` ... (`land` has no close, so it only prints the skip)."""
        gate = self.sh_gate("exit 1")
        repo, ticket, wt_path = self.started(gate=gate)
        result = self.wt(repo, "land", ticket, "--no-gate", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: --no-gate: skipping gate %s" % " ".join(gate))
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertFalse(any("gate skipped" in n for n in self.pm.notes(repo, ticket)))


    # ---------------------------------------------------- 2b: merge paths, teardown
    def faults(self):
        return os.listdir(self.env["WT_FAULT_REPORT_DIR"])

    def conflicting(self, **kw):
        """A started ticket whose commit and a later main commit change README.md's
        one line differently."""
        repo, ticket, wt_path = self.started(**kw)
        self.commit_file(wt_path, "README.md", "branch side\n", "%s: edit" % ticket)
        self.commit_file(repo, "README.md", "main side\n", "main edits the line")
        return repo, ticket, wt_path

    def test_rebase_conflict_auto_parks(self):
        """`finish` **auto-parks** when the rebase conflicts: the ticket is
        `done-unmerged`, the branch is kept, the worktree is gone. Resume later with
        `wt start`."""
        repo, ticket, wt_path = self.conflicting()
        tip = self.git(wt_path, "rev-parse", "HEAD").stdout.strip()
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: rebase of %s onto main conflicted; auto-parked"
                            % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertEqual(self.git(repo, "rev-parse", ticket).stdout.strip(), tip)
        self.git(repo, "merge-base", "--is-ancestor", before, "main")
        self.assertNotEqual(self.git(repo, "merge-base", "--is-ancestor", tip, "main",
                                     check=False).returncode, 0)
        with open(os.path.join(repo, "README.md")) as f:
            self.assertEqual(f.read(), "main side\n")
        # Old wt: start finds the same conflict in its own rebase, removes the worktree
        # again and keeps the branch (the contract says "resume").
        again = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertNotEqual(again.code, 0, again.text)
        self.assert_wt_line(again, "wt: resuming %s: rebase onto main conflicted" % ticket)
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertEqual(self.git(repo, "rev-parse", ticket).stdout.strip(), tip)

    def hook_moves_main(self, repo, times):
        """A post-rewrite hook (runs after wt's rebase) that commits to main in the main
        checkout `times` times, counted in a file."""
        hooks = os.path.join(self.root, "hooks")
        os.mkdir(hooks)
        counter = os.path.join(self.root, "moves-left")
        with open(counter, "w") as f:
            f.write("%d\n" % times)
        script = os.path.join(hooks, "post-rewrite")
        with open(script, "w") as f:
            f.write("#!/bin/sh\n"
                    "n=$(cat %(c)s)\n"
                    "[ \"$n\" -gt 0 ] || exit 0\n"
                    "echo $((n-1)) > %(c)s\n"
                    "unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE\n"
                    "echo $n > %(r)s/moved$n.txt\n"
                    "git -C %(r)s add -- moved$n.txt\n"
                    "git -C %(r)s commit -q -m \"main moves $n\"\n"
                    % {"c": shlex.quote(counter), "r": shlex.quote(repo)})
        os.chmod(script, 0o755)
        self.git(repo, "config", "core.hooksPath", hooks)
        return counter

    def test_ffonly_retry_absorbs_one_move(self):
        """`finish` ... ff-only merge: when main moves after the rebase, one move is
        absorbed by a retry and the finish succeeds."""
        repo, ticket, wt_path = self.started()
        self.commit_file(repo, "later.txt", "later\n", "main moves first")
        counter = self.hook_moves_main(repo, 1)
        result = self.finish(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s merged into main, " % ticket)
        with open(counter) as f:
            self.assertEqual(f.read().strip(), "0")
        self.assertTrue(os.path.isfile(os.path.join(repo, "moved1.txt")))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "done")

    def test_ffonly_retries_exhausted_auto_parks(self):
        """`finish` **auto-parks** when the ff-only merge still fails after three
        tries: the ticket is `done-unmerged`, the branch is kept, the worktree is gone."""
        repo, ticket, wt_path = self.started()
        self.commit_file(repo, "later.txt", "later\n", "main moves first")
        self.hook_moves_main(repo, 9)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: ff-only merge of %s onto main failed 3 times"
                            % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertFalse(os.path.exists(os.path.join(repo, "work.txt")))

    def test_refusal_after_merge_leaves_ticket_taken(self):
        """`OK: <id> merged ...; ticket NOT closed`: the merge landed, pm refused the
        close, the ticket stays claimed."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "guarded", labels=("tooling",))
        started = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(started.code, 0, started.text)
        wt_path = self.worktree(repo, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        self.pm.guard_refuse_done(repo)
        result = self.finish(repo, ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s merged into main, " % ticket)
        self.assertIn("ticket NOT closed", result.out)
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def test_stale_merged_worktree_is_torn_down_and_closed(self):
        """A successful ff-only merge pins the tip in `refs/wt/merged/<id>`; `finish` on
        a branch whose tip equals that marker (and is in the default branch) tears down
        and closes the ticket, never parks or releases it."""
        repo, ticket, wt_path = self.started()
        self.git(repo, "merge", "-q", "--ff-only", ticket)
        self.git(repo, "update-ref", "refs/wt/merged/%s" % ticket, "refs/heads/%s" % ticket)
        result = self.finish(repo, ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s merged into main, " % ticket)
        self.assertFalse(os.path.exists(wt_path))
        self.assertEqual(self.pm.status(repo, ticket), "done")

    def test_nested_git_repo_refuses_before_merge(self):
        """`finish` refuses (before any merge) a worktree holding a nested git repo (a
        `.git` dir with `config` or `hooks`): names the path and the operator-run
        `rm -rf`; no fault row."""
        repo, ticket, wt_path = self.started()
        self.commit_file(wt_path, ".gitignore", "inner/\n", "%s: ignore" % ticket)
        inner = os.path.join(wt_path, "inner")
        os.makedirs(os.path.join(inner, ".git"))
        with open(os.path.join(inner, ".git", "config"), "w") as f:
            f.write("[core]\n")
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: worktree %s holds paths the sandbox cannot delete"
                            % wt_path)
        self.assertIn("rm -rf %s" % inner, result.text)
        self.assert_untouched(repo, ticket, wt_path, before)
        self.assertEqual(self.faults(), [])

    def test_vscode_dir_refuses_before_merge(self):
        """`finish` refuses a worktree holding a `.vscode` dir, same line as a nested
        repo."""
        repo, ticket, wt_path = self.started()
        self.commit_file(wt_path, ".gitignore", ".vscode/\n", "%s: ignore" % ticket)
        vscode = os.path.join(wt_path, ".vscode")
        try:
            os.mkdir(vscode)
        except OSError as err:
            self.skipTest("sandbox denies .vscode: %s" % err)
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: worktree %s holds paths the sandbox cannot delete"
                            % wt_path)
        self.assertIn("rm -rf %s" % vscode, result.text)
        self.assert_untouched(repo, ticket, wt_path, before)
        self.assertEqual(self.faults(), [])

    def locked_started(self):
        repo, ticket, wt_path = self.started()
        self.commit_file(wt_path, ".gitignore", "cache/\n", "%s: ignore" % ticket)
        cache = os.path.join(wt_path, "cache")
        os.mkdir(cache)
        with open(os.path.join(cache, "keep.log"), "w") as f:
            f.write("ignored\n")
        os.chmod(cache, 0o555)
        self.addCleanup(lambda: os.path.isdir(cache) and os.chmod(cache, 0o755))
        return repo, ticket, wt_path, cache

    def test_failed_remove_prints_stop(self):
        """A failed `git worktree remove` (finish) prints a `STOP.` line and never
        invites a retry, `--force` or a sandbox-disabled attempt; the ticket is still
        claimed and a fault row is written."""
        repo, ticket, wt_path, cache = self.locked_started()
        result = self.finish(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        stop = [l for l in result.lines() if l.startswith("wt: STOP.")]
        self.assertEqual(len(stop), 1, result.text)
        self.assertIn("Do not run any further git, wt or pm command", stop[0])
        self.assertIn("do not escalate", stop[0])
        self.assertNotIn("retry", stop[0].lower())
        # Old wt: the operator-run cleanup it hands over does carry `--force`.
        self.assertLess(stop[0].index("operator-run"), stop[0].index("--force"))
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertEqual(len(self.faults()), 1, self.faults())
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        marker = self.git(repo, "rev-parse", "--verify", "-q",
                          "refs/wt/merged/%s" % ticket, check=False)
        self.assertEqual(marker.stdout.strip(), self.git(repo, "rev-parse", ticket).stdout.strip())

    def test_failed_remove_leaves_nothing_for_finish_to_adopt(self):
        """A stale worktree of your own (ticket already closed and merged): `wt finish
        <ticket-id>`. After a failed remove, pinned as the old wt behaves."""
        repo, ticket, wt_path, cache = self.locked_started()
        self.assertNotEqual(self.finish(repo, ticket).code, 0)
        if os.path.isdir(cache):
            os.chmod(cache, 0o755)
        again = self.finish(repo, ticket, "--findings", "none")
        # Old wt: git already dropped the registration while failing to delete the
        # tree, so finish finds no worktree; the operator's cleanup (the STOP line) is
        # the way out and the ticket stays claimed (contract: finish tears it down).
        self.assertNotEqual(again.code, 0, again.text)
        self.assert_wt_line(again, "wt: no worktree at %s for %s" % (wt_path, ticket))
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def test_every_refusal_names_a_next_step(self):
        """A line starting `wt:` is a failure. It names the exact next step: every
        refusal of the gate and merge paths is non-empty after the prefix."""
        def findings_required():
            repo, ticket, _ = self.started(findings_required=True, name="r1")
            return self.finish(repo, ticket)

        def gate_fails():
            repo, ticket, _ = self.started(gate=self.sh_gate("exit 3"), name="r2")
            return self.finish(repo, ticket)

        def dirty():
            repo, ticket, wt_path = self.started(name="r3")
            with open(os.path.join(wt_path, "stray.txt"), "w") as f:
                f.write("x\n")
            return self.finish(repo, ticket)

        def malformed():
            repo, ticket, _ = self.started(malformed="not-a-list", name="r4")
            return self.finish(repo, ticket)

        def land_note():
            repo, ticket, _ = self.started(name="r5")
            return self.wt(repo, "land", ticket, "--note", "x", session="s1")

        def conflict():
            repo, ticket, _ = self.conflicting(name="r6")
            return self.finish(repo, ticket)

        def nested():
            repo, ticket, wt_path = self.started(name="r7")
            self.commit_file(wt_path, ".gitignore", "inner/\n", "ignore")
            os.makedirs(os.path.join(wt_path, "inner", ".git"))
            with open(os.path.join(wt_path, "inner", ".git", "config"), "w") as f:
                f.write("[core]\n")
            return self.finish(repo, ticket)

        for build in (findings_required, gate_fails, dirty, malformed, land_note,
                      conflict, nested):
            with self.subTest(case=build.__name__):
                result = build()
                self.assertNotEqual(result.code, 0, result.text)
                lines = [l for l in result.lines() if l.startswith("wt: ")]
                self.assertTrue(lines, result.text)
                self.assertTrue(any(l[len("wt: "):].strip() for l in lines), result.text)


# Parts 3 and 4 fill these in. Keep the names: the overseer's prompts address them.
class ParkTest(WtCase):
    pass


class StatusPruneTest(WtCase):
    pass


class ResolutionTest(WtCase):
    pass


if __name__ == "__main__":
    unittest.main()
