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
import re
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

IDENTITY_VARS = ("PM_AGENT", "WT_ACTOR", "PM_SESSION_ID",
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

    def gate_label(self, argv):
        """What wt prints for the configured gate: old, the argv joined; new, the
        executable path `.wt/gate`."""
        raise NotImplementedError

    def unregister_store(self, repo):
        """Drop `repo` from this side's registry (new: its `$PM_STORES` line; old: the
        registry starts empty, so nothing to do)."""
        raise NotImplementedError

    def add_known_red(self, repo, ticket, match):
        raise NotImplementedError

    def guard_refuse_done(self, repo):
        """After this, closing a ticket is refused by pm after wt's merge. On the old
        side the ticket must have been filed with labels=("tooling",)."""
        raise NotImplementedError

    def register_store(self, prefix, repo):
        """Add the store of `repo` to this side's private registry."""
        raise NotImplementedError

    def blockers(self, repo, ticket):
        """Ids linked as blocking `ticket`, whatever their status."""
        raise NotImplementedError

    def close_ticket(self, repo, ticket, session):
        """Close `ticket` as wt's finish would, leaving any worktree in place."""
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

    def gate_label(self, argv):
        return " ".join(argv)

    def unregister_store(self, repo):
        pass

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

    def register_store(self, prefix, repo):
        path = self.env["PM_STORES_FILE"]
        with open(path) as f:
            data = json.load(f)
        data["stores"].append({"path": repo})
        with open(path, "w") as f:
            json.dump(data, f)

    def blockers(self, repo, ticket):
        return list(self._show(repo, ticket).get("blocked_by") or [])

    def close_ticket(self, repo, ticket, session):
        self._pm(repo, "close", ticket, "--via", "wt", "--findings", "none", session=session)


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

    def gate_label(self, argv):
        return ".wt/gate"

    def unregister_store(self, repo):
        path = self.env["PM_STORES"]
        with open(path) as f:
            lines = f.read().splitlines()
        keep = [l for l in lines if l.split(None, 1)[-1:] != [repo]]
        with open(path, "w") as f:
            f.write("".join(l + "\n" for l in keep))

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

    def register_store(self, prefix, repo):
        with open(self.env["PM_STORES"], "a") as f:
            f.write("%s %s\n" % (prefix, repo))

    def blockers(self, repo, ticket):
        value = json.loads(self._pm(repo, "show", ticket, "--json").stdout)["blocked_by"]
        return [v if isinstance(v, str) else v.get("id") for v in value or []]

    def close_ticket(self, repo, ticket, session):
        self._pm(repo, "done", ticket, "--findings", "none", "-m", "closed", session=session)


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
            "PM_AGENT": "kiro/worker",
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

    def wt(self, repo, *args, session=None, actor=None, cwd=None, path_first=None,
           env=None, path=None):
        """The one helper that runs wt. Returns a Result; ends the test as pending when
        the call exited 70 and appended to $WT_UNBUILT_LOG. `path_first` is a directory
        put first on PATH for this call only; `path` replaces PATH; `env` adds
        variables for this call only."""
        before = unbuilt_size()
        call = self.call_env(session, actor)
        if env:
            call.update(env)
        env = call
        if path is not None:
            env["PATH"] = path
        if path_first:
            env["PATH"] = path_first + ":" + env["PATH"]
        done = subprocess.run([CLI] + list(args), cwd=cwd or repo,
                              env=env, capture_output=True,
                              text=True, timeout=180)
        result = Result(done)
        if result.code == 70 and unbuilt_size() > before:
            raise Pending(shlex.join(["wt"] + list(args)))
        return result

    def git(self, repo, *args, check=True):
        return sh(["git", "-C", repo] + list(args), repo, self.env, check)

    def make_repo(self, name="main-repo", prefix=None, findings_required=False):
        """A fresh repo: git init -b main, one commit, a store made through the adapter.
        The default prefix is `tk` for the default name and `tk<name>` otherwise, so two
        repos in one test never share a prefix (the new pm refuses a shared one)."""
        if prefix is None:
            prefix = "tk" if name == "main-repo" else "tk" + "".join(
                c for c in name if c.isalnum())
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
        return os.path.join(repo, ".wt", ticket)

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

    def test_register_store_and_blockers(self):
        repo = self.make_repo()
        self.pm.register_store("tk", repo)
        first = self.pm.file_ticket(repo, "one")
        second = self.pm.file_ticket(repo, "two")
        self.assertEqual(self.pm.blockers(repo, second), [])
        self.pm.block(repo, second, first)
        self.assertEqual(self.pm.blockers(repo, second), [first])
        other = self.make_repo(name="elsewhere", prefix="zz")
        self.pm.register_store("zz", other)
        far = self.pm.file_ticket(other, "far")
        where = sh(["pm", "ticket", "where", far] if SIDE == "old"
                   else ["pm", "get", far, "store"], repo, self.env)
        self.assertIn(other, where.stdout)


# ---------------------------------------------------------------------- start
class StartTest(WtCase):
    def test_claims_and_adds_worktree(self):
        """`start` ... claim via pm ... add/resume the worktree; a worktree always lives at
        `<target_repo>/.wt/<id>` on branch `<id>`."""
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
        self.assert_wt_line(result, "wt: wt start requires --as <name> (or $WT_ACTOR)")
        self.assertEqual(self.pm.status(repo, ticket), "open")
        self.assertFalse(os.path.exists(self.worktree(repo, ticket)))

    def started_by(self, env=None, session_flag=None):
        """A ticket started by wt with the given variables, its worktree then removed by
        test code (git, not wt) so a later `start` can adopt it and succeed."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "token")
        args = ["start", ticket, "--as", "ada"]
        if session_flag:
            args += ["--session", session_flag]
        first = self.wt(repo, *args, env=env)
        self.assertEqual(first.code, 0, first.text)
        self.git(repo, "worktree", "remove", self.worktree(repo, ticket))
        return repo, ticket

    def assert_adopts(self, repo, ticket, *args, env=None):
        result = self.wt(repo, "start", ticket, "--as", "ada", *args, env=env)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "adopting existing claim on %s" % ticket)
        self.assert_wt_line(result, "OK: %s -> " % ticket)
        self.git(repo, "worktree", "remove", self.worktree(repo, ticket))

    def assert_refuses(self, repo, ticket, *args, env=None):
        result = self.wt(repo, "start", ticket, "--as", "ada", *args, env=env)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: ticket %s is not claimable" % ticket)
        self.assertFalse(os.path.exists(self.worktree(repo, ticket)))

    def test_session_flag_claims_with_that_token(self):
        """`start --session X` claims with token X: the same `--session` adopts, another
        refuses (no variable set in the environment)."""
        repo, ticket = self.started_by(session_flag="sx")
        self.assert_refuses(repo, ticket, "--session", "sy")
        self.assert_adopts(repo, ticket, "--session", "sx")

    def test_pm_session_id_is_the_default_session(self):
        """With no `--session`, `PM_SESSION_ID` is the session token; park folds it
        into the resume line the same way."""
        env = {"PM_SESSION_ID": "pm1"}
        repo, ticket = self.started_by(env=env)
        self.assert_refuses(repo, ticket, "--session", "pm2")
        self.assert_adopts(repo, ticket, "--session", "pm1")
        self.assert_adopts(repo, ticket, env=env)
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada", env=env).code, 0)
        wt_path = self.worktree(repo, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        parked = self.wt(repo, "park", ticket, "--findings", "none", env=env)
        self.assertEqual(parked.code, 0, parked.text)
        notes = [n for n in self.pm.notes(repo, ticket) if "branch %s @ " % ticket in n]
        self.assertEqual(len(notes), 1, self.pm.notes(repo, ticket))
        self.assertTrue(notes[0].endswith("wt start %s --as ada --session pm1 && "
                                          "wt finish %s" % (ticket, ticket)), notes[0])

    def test_worktree_add_eperm_appends_the_restart_hint(self):
        """`start` appends a restart/resume hint when `git worktree add` fails with
        `.git/worktrees` "Operation not permitted"."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "eperm")
        shim = os.path.join(self.root, "eperm-shim")
        os.mkdir(shim)
        path = os.path.join(shim, "git")
        with open(path, "w") as f:
            f.write('#!/bin/sh\n'
                    'case "$*" in *"worktree add"*)\n'
                    '  echo "error: cannot mkdir %s/.git/worktrees/x: Operation not permitted"'
                    ' >&2; exit 128;; esac\n'
                    'exec /usr/bin/git "$@"\n' % repo)
        os.chmod(path, 0o755)
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1", path_first=shim)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: git worktree add for %s failed: " % ticket)
        line = [l for l in result.lines() if l.startswith("wt: git worktree add")][0]
        self.assertIn("The worktrees admin directory was deleted during this session", line)
        self.assertIn("restart or resume the session.", line)
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


class StartedCase(WtCase):
    """Shared by the finish, park and deferred-teardown classes."""

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

    def head(self, repo):
        return self.git(repo, "rev-parse", "main").stdout.strip()

    def faults(self):
        return os.listdir(self.env["WT_FAULT_REPORT_DIR"])

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


class FinishTest(StartedCase):
    def finish(self, repo, ticket, *args):
        return self.wt(repo, "finish", ticket, *args, session="s1")

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
        self.assertNotIn("deferred", result.text)
        self.assertFalse(self.branch_exists(repo, ticket))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "done")

    def test_finish_is_fast_forward_only(self):
        """`finish` ... ff-only merge: the branch commit itself lands on main and no
        merge commit is created."""
        repo, ticket, wt_path = self.started()
        tip = self.git(wt_path, "rev-parse", "HEAD").stdout.strip()
        before = self.head(repo)
        self.assertEqual(self.finish(repo, ticket).code, 0)
        self.git(repo, "merge-base", "--is-ancestor", tip, "main")
        self.assertEqual(self.git(repo, "rev-list", "--merges",
                                  "%s..main" % before).stdout.strip(), "")

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
        self.assert_wt_line(result, "wt: gate %s exit 0, SKIP lines: 2" % self.pm.gate_label(gate))
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
        self.assert_wt_line(result, "wt: gate %s exit 3, SKIP lines: 0" % self.pm.gate_label(gate))
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
        self.assert_wt_line(result, "wt: worktree %s has uncommitted or untracked files"
                            % wt_path)
        self.assertFalse(os.path.exists(marker))
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_malformed_gate_refuses(self):
        """A malformed gate (old: not a list of strings; new: `.wt/gate` present but not
        executable) refuses too -- a typo never turns the gate off. Side-neutral: a `wt:`
        line with `gate` and `fix it or pass --no-gate.`, nothing touched."""
        repo, ticket, wt_path = self.started(malformed="not-a-list")
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assertTrue(any(l.startswith("wt: ") and "gate" in l and
                            "fix it or pass --no-gate." in l
                            for l in result.lines()), result.text)
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_no_gate_bypasses_and_notes_it(self):
        """`--no-gate` bypasses it and appends `gate skipped (--no-gate): <label>` to
        the close note (label: `gate_label()`)."""
        marker = os.path.join(self.root, "gate-ran.txt")
        gate = self.sh_gate("echo ran > %s; exit 1" % shlex.quote(marker))
        repo, ticket, wt_path = self.started(gate=gate)
        result = self.finish(repo, ticket, "--no-gate")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(os.path.exists(marker))
        self.assertFalse(result.has_line("wt: gate "), result.text)
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertTrue(any("gate skipped (--no-gate): " + self.pm.gate_label(gate) in n
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
        self.assertFalse(self.branch_exists(repo, ticket))
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
        self.assertFalse(self.branch_exists(repo, ticket))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def test_land_refuses_a_dirty_worktree(self):
        """`finish --keep-open` (`wt land`) ... same refusals (dirty worktree): nothing
        merged, ticket stays claimed, worktree and branch intact."""
        repo, ticket, wt_path = self.started()
        with open(os.path.join(wt_path, "stray.txt"), "w") as f:
            f.write("untracked\n")
        before = self.head(repo)
        result = self.wt(repo, "land", ticket, session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: worktree %s has uncommitted or untracked files"
                            % wt_path)
        self.assert_untouched(repo, ticket, wt_path, before)

    def test_land_rebase_conflict_auto_parks(self):
        """`land` has the same refusals as `finish` (rebase conflict): auto-parked, the
        branch kept, the worktree gone."""
        repo, ticket, wt_path = self.conflicting()
        before = self.head(repo)
        result = self.wt(repo, "land", ticket, session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: rebase of %s onto main conflicted; auto-parked"
                            % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.git(repo, "merge-base", "--is-ancestor", before, "main")
        with open(os.path.join(repo, "README.md")) as f:
            self.assertEqual(f.read(), "main side\n")

    def test_land_ffonly_exhaustion_auto_parks(self):
        """`land` has the same refusals as `finish` (ff-only exhaustion): auto-parked
        after three tries, nothing merged."""
        repo, ticket, wt_path = self.started()
        self.commit_file(repo, "later.txt", "later\n", "main moves first")
        self.hook_moves_main(repo, 9)
        result = self.wt(repo, "land", ticket, session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: ff-only merge of %s onto main failed 3 times"
                            % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertFalse(os.path.exists(os.path.join(repo, "work.txt")))

    def test_land_runs_the_gate(self):
        """`finish` and `land` read the gate: a passing gate on `land` without
        `--no-gate` prints its exit line and the land completes."""
        gate = self.sh_gate("echo fine")
        repo, ticket, wt_path = self.started(gate=gate)
        result = self.wt(repo, "land", ticket, session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: gate %s exit 0, SKIP lines: 0" % self.pm.gate_label(gate))
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def test_land_gate_failure_refuses(self):
        """A non-zero gate exit refuses `land`: nothing merged, ticket stays claimed,
        worktree intact."""
        gate = self.sh_gate("echo boom; exit 3")
        repo, ticket, wt_path = self.started(gate=gate)
        before = self.head(repo)
        result = self.wt(repo, "land", ticket, session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: gate %s exit 3, SKIP lines: 0" % self.pm.gate_label(gate))
        self.assertIn("boom", result.lines())
        self.assert_untouched(repo, ticket, wt_path, before)

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
        self.assert_wt_line(result, "wt: --no-gate: skipping gate %s" % self.pm.gate_label(gate))
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertFalse(any("gate skipped" in n for n in self.pm.notes(repo, ticket)))


    # ---------------------------------------------------- 2b: merge paths, teardown
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
        `wt start`. See fc-f0cc16."""
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
        counter = self.hook_moves_main(repo, 9)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: ff-only merge of %s onto main failed 3 times"
                            % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertFalse(os.path.exists(os.path.join(repo, "work.txt")))
        with open(counter) as f:
            self.assertEqual(f.read().strip(), "6")

    def test_ffonly_retry_absorbs_two_moves(self):
        """`finish` ... ff-only merge is retried up to three times: two moves are
        absorbed (the third try merges) and the finish succeeds."""
        repo, ticket, wt_path = self.started()
        self.commit_file(repo, "later.txt", "later\n", "main moves first")
        counter = self.hook_moves_main(repo, 2)
        result = self.finish(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s merged into main, " % ticket)
        with open(counter) as f:
            self.assertEqual(f.read().strip(), "0")
        self.assertTrue(os.path.isfile(os.path.join(repo, "moved2.txt")))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))
        self.assertEqual(self.pm.status(repo, ticket), "done")

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
        ok_line = [l for l in result.out.splitlines()
                   if l.startswith("OK: %s merged" % ticket)]
        self.assertEqual(len(ok_line), 1, result.text)
        self.assertIn("ticket NOT closed", ok_line[0])
        # The line ends with the command that closes the ticket: it names the id.
        self.assertIn(ticket, ok_line[0].rsplit("run ", 1)[1])
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

    def test_stale_worktree_of_a_closed_ticket(self):
        """Old wt deviates from the contract: a stale worktree of your own (ticket
        already closed and merged) is torn down by `wt finish <ticket-id>` and the last
        line reports the close failed (contract.md:198-200). Old wt's pre-close check
        (pm's own refusal) stops first: worktree and branch stay and the line is `wt: pm
        would refuse to update <id>: ...`. Old side pins that; new side pins the
        contract: worktree gone, branch gone, status `done`, last line `wt:` naming the
        id and saying the close failed. The exit code is not pinned on the new side."""
        repo, ticket, wt_path = self.started()
        self.git(repo, "merge", "-q", "--ff-only", ticket)
        self.git(repo, "update-ref", "refs/wt/merged/%s" % ticket, "refs/heads/%s" % ticket)
        self.pm.close_ticket(repo, ticket, "s1")
        self.assertEqual(self.pm.status(repo, ticket), "done")
        result = self.finish(repo, ticket, "--findings", "none")
        if SIDE == "old":
            self.assertNotEqual(result.code, 0, result.text)
            self.assert_wt_line(result, "wt: pm would refuse to update %s: " % ticket)
            self.assertFalse(result.has_line("OK: "), result.text)
            self.assertTrue(os.path.isdir(wt_path))
            self.assertTrue(self.branch_exists(repo, ticket))
        else:
            last = result.lines()[-1]
            self.assertTrue(last.startswith("wt:"), result.text)
            self.assertIn(ticket, last)
            self.assertIn("close", last)
            self.assertIn("fail", last)
            self.assertFalse(os.path.exists(wt_path))
            self.assertFalse(self.branch_exists(repo, ticket))
        self.assertEqual(self.pm.status(repo, ticket), "done")

    def nested_inner(self, wt_path, ticket, name, parts):
        """An ignored directory `name` in the worktree holding a `.git` dir with `parts`
        (file names created under it); returns its path."""
        self.commit_file(wt_path, ".gitignore", "%s/\n" % name, "%s: ignore %s" % (ticket, name))
        inner = os.path.join(wt_path, name)
        os.makedirs(os.path.join(inner, ".git"))
        for part in parts:
            if part == "hooks":
                os.mkdir(os.path.join(inner, ".git", part))
            else:
                with open(os.path.join(inner, ".git", part), "w") as f:
                    f.write("[core]\n")
        return inner

    def test_nested_git_repo_with_only_hooks_refuses(self):
        """A nested `.git` dir with `config` or `hooks`: a nested repo holding only
        `hooks` refuses the same way."""
        repo, ticket, wt_path = self.started()
        inner = self.nested_inner(wt_path, ticket, "inner", ["hooks"])
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: worktree %s holds paths the sandbox cannot delete"
                            % wt_path)
        self.assertIn("rm -rf %s" % inner, result.text)
        self.assert_untouched(repo, ticket, wt_path, before)
        self.assertEqual(self.faults(), [])

    def test_six_nested_repos_name_five_paths(self):
        """The line names up to 5 paths: with six nested repos it names five, then `and 1
        more`; the operator-run `rm -rf` list still carries every path."""
        repo, ticket, wt_path = self.started()
        inners = []
        for n in range(6):
            inners.append(self.nested_inner(wt_path, ticket, "n%d" % n, ["config"]))
        before = self.head(repo)
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        line = [l for l in result.lines()
                if l.startswith("wt: worktree %s holds paths" % wt_path)]
        self.assertEqual(len(line), 1, result.text)
        shown = line[0].split("(nested git repo or .vscode): ", 1)[1].split(". Nothing was", 1)[0]
        self.assertTrue(shown.endswith(" and 1 more"), shown)
        self.assertEqual(shown[:-len(" and 1 more")].split(", "), inners[:5])
        for inner in inners:
            self.assertIn("rm -rf %s" % inner, line[0])
        self.assert_untouched(repo, ticket, wt_path, before)

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
        repo. Runs here: `.vscode` can be created under the test root. In a sandbox
        that denies a `.vscode` path segment it skips itself (`skipped 1` fails the
        gate); run it unsandboxed there:
        /usr/bin/python3 -B wt/tests/run_wt.py --cli <wt> --pm old
        -k test_vscode_dir_refuses_before_merge -v, expecting `ok` and `failed 0`."""
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
        self.assertRegex(stop[0], r"merged %s into main, but `git -C \S+ worktree remove "
                         r"\S+` failed" % ticket)
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

    def merged_marked(self):
        """A started ticket already ff-merged with wt's merged marker, so finish takes
        the teardown-and-close route whatever shape the worktree is in."""
        repo, ticket, wt_path = self.started()
        self.git(repo, "merge", "-q", "--ff-only", ticket)
        self.git(repo, "update-ref", "refs/wt/merged/%s" % ticket, "refs/heads/%s" % ticket)
        return repo, ticket, wt_path

    def operator_part(self, result):
        stop = [l for l in result.lines() if l.startswith("wt: STOP.")]
        self.assertEqual(len(stop), 1, result.text)
        self.assertIn("operator-run, in order", stop[0])
        return stop[0].split("operator-run, in order", 1)[1]

    def test_failed_remove_dir_gone_hands_over_prune(self):
        """The failed-remove handoff is per shape: dir gone -> `worktree prune` (no
        `rm -rf`, no `--force`)."""
        repo, ticket, wt_path = self.merged_marked()
        shutil.rmtree(wt_path)
        shim = os.path.join(self.root, "prune-shim")
        os.mkdir(shim)
        with open(os.path.join(shim, "git"), "w") as f:
            f.write('#!/bin/sh\n'
                    'case "$*" in *"worktree prune"*)\n'
                    '  echo "fatal: prune refused" >&2; exit 1;; esac\n'
                    'exec /usr/bin/git "$@"\n')
        os.chmod(os.path.join(shim, "git"), 0o755)
        result = self.wt(repo, "finish", ticket, "--findings", "none", session="s1",
                         path_first=shim)
        self.assertNotEqual(result.code, 0, result.text)
        ops = self.operator_part(result)
        self.assertIn("`git -C %s worktree prune`" % repo, ops)
        self.assertNotIn("rm -rf", ops)
        self.assertNotIn("--force", ops)

    def test_failed_remove_gitfile_missing_hands_over_rm_then_prune(self):
        """The failed-remove handoff is per shape: `.git` file missing -> `rm -rf` then
        prune (no `--force`)."""
        repo, ticket, wt_path = self.merged_marked()
        os.remove(os.path.join(wt_path, ".git"))
        result = self.finish(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        ops = self.operator_part(result)
        self.assertIn("`rm -rf %s`" % wt_path, ops)
        self.assertIn("`git -C %s worktree prune`" % repo, ops)
        self.assertLess(ops.index("rm -rf"), ops.index("worktree prune"))
        self.assertNotIn("--force", ops)

    def fault_rows(self, name):
        with open(os.path.join(self.env["WT_FAULT_REPORT_DIR"], name)) as f:
            return [l for l in f.read().splitlines()
                    if l.startswith("| ") and not l.startswith("| when")]

    def unpaired_start(self, repo, other, ticket):
        return self.wt(repo, "start", ticket, "--as", "ada", "--store", other, session="s1")

    def test_fault_row_ends_the_line_with_reported_path_and_dedups(self):
        """A `wt:` line that ends `(reported: <path>)` means the fault is recorded: the
        path exists under $WT_FAULT_REPORT_DIR. Old wt dedups by file, not by row: one
        file per (root cause, day), one appended row per occurrence, so the same
        failure twice leaves one file. Side-neutral (the contract dedups to one row,
        the old wt appends): one file per root cause and at least one row."""
        repo = self.make_repo()
        other = self.make_repo(name="other")
        ticket = self.pm.file_ticket(other, "far")
        first = self.unpaired_start(repo, other, ticket)
        self.assertNotEqual(first.code, 0, first.text)
        line = [l for l in first.lines() if l.startswith("wt: cross-repo ")]
        self.assertEqual(len(line), 1, first.text)
        match = re.search(r"\(reported: (\S+)\)$", line[0])
        self.assertTrue(match, line[0])
        self.assertTrue(os.path.isfile(match.group(1)))
        self.assertEqual(os.path.dirname(match.group(1)), self.env["WT_FAULT_REPORT_DIR"])
        second = self.unpaired_start(repo, other, ticket)
        self.assertNotEqual(second.code, 0, second.text)
        self.assertEqual(self.faults(), [os.path.basename(match.group(1))])
        self.assertGreaterEqual(len(self.fault_rows(self.faults()[0])), 1)

    def test_infra_fault_line_names_the_recorded_path(self):
        """A failure that writes a row (rebase conflict) ends its `wt:` line `Recorded
        in <path>. This is infrastructure, not a finding: ...`; the path exists."""
        repo, ticket, wt_path = self.conflicting()
        result = self.finish(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        line = [l for l in result.lines() if l.startswith("wt: rebase of ")]
        self.assertEqual(len(line), 1, result.text)
        match = re.search(r"Recorded in (\S+)\. This is infrastructure, not a finding", line[0])
        self.assertTrue(match, line[0])
        self.assertTrue(os.path.isfile(match.group(1)))
        self.assertEqual(self.faults(), [os.path.basename(match.group(1))])

    def test_every_refusal_names_a_next_step(self):
        """A line starting `wt:` is a failure. It names the exact next step: every
        refusal of the gate and merge paths carries the specific next step the old wt
        prints (a command or an action), in a `wt:` line."""
        def findings_required():
            repo, ticket, _ = self.started(findings_required=True, name="r1")
            return self.finish(repo, ticket), ["pass --findings none or the ids"]

        def gate_fails():
            repo, ticket, _ = self.started(gate=self.sh_gate("exit 3"), name="r2")
            return self.finish(repo, ticket), [
                "re-run `wt finish %s` (doc-only ticket: add --no-gate)." % ticket]

        def dirty():
            repo, ticket, wt_path = self.started(name="r3")
            with open(os.path.join(wt_path, "stray.txt"), "w") as f:
                f.write("x\n")
            return self.finish(repo, ticket), [
                "Commit them (`git -C %s add <paths>` then commit) or remove them, then "
                "re-run `wt finish %s`." % (wt_path, ticket)]

        def malformed():
            repo, ticket, _ = self.started(malformed="not-a-list", name="r4")
            return self.finish(repo, ticket), ["fix it or pass --no-gate."]

        def land_note():
            repo, ticket, _ = self.started(name="r5")
            return (self.wt(repo, "land", ticket, "--note", "x", session="s1"),
                    ["pass them to the final `wt finish %s`." % ticket])

        def land_findings():
            repo, ticket, _ = self.started(name="r8")
            return (self.wt(repo, "land", ticket, "--findings", "x", session="s1"),
                    ["pass them to the final `wt finish %s`." % ticket])

        def conflict():
            repo, ticket, _ = self.conflicting(name="r6")
            return self.finish(repo, ticket), [
                "resolve the conflict by hand in a fresh `wt start %s`, then `wt finish %s` "
                "again" % (ticket, ticket)]

        def nested():
            repo, ticket, wt_path = self.started(name="r7")
            inner = self.nested_inner(wt_path, ticket, "inner", ["config"])
            return self.finish(repo, ticket), [
                "Hand the operator: rm -rf %s -- after that, `wt finish %s` completes "
                "normally." % (inner, ticket)]

        unbuilt = []
        for build in (findings_required, gate_fails, dirty, malformed, land_note,
                      land_findings, conflict, nested):
            with self.subTest(case=build.__name__):
                try:
                    result, steps = build()
                except Pending as step:
                    # A Pending inside a subTest is reported as an error; collect it
                    # and raise it once after the loop (failures stay failures).
                    unbuilt.append(step)
                    continue
                self.assertNotEqual(result.code, 0, result.text)
                lines = [l for l in result.lines() if l.startswith("wt: ")]
                self.assertTrue(lines, result.text)
                for step in steps:
                    self.assertTrue(any(step in l for l in lines), result.text)
        if unbuilt:
            raise unbuilt[0]


class ParkTest(StartedCase):
    def park(self, repo, ticket, *args):
        return self.wt(repo, "park", ticket, *args, session="s1")

    def write(self, where, name, text="x\n"):
        with open(os.path.join(where, name), "w") as f:
            f.write(text)

    def park_note(self, repo, ticket):
        notes = [n for n in self.pm.notes(repo, ticket) if "branch %s @ " % ticket in n]
        self.assertEqual(len(notes), 1, self.pm.notes(repo, ticket))
        return notes[0]

    def assert_untouched(self, repo, ticket, wt_path, tip):
        self.assertTrue(os.path.isdir(wt_path))
        self.assertEqual(self.git(repo, "rev-parse", ticket).stdout.strip(), tip)
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def test_wip_commit_and_park(self):
        """`park` removes the worktree and keeps the branch; it commits WIP first:
        subject `WIP: park <id>`; ticket parked; the worktree directory is gone at
        once."""
        repo, ticket, wt_path = self.started()
        self.write(wt_path, "tracked.txt")
        self.write(wt_path, "work.txt", "edited\n")
        before = self.head(repo)
        result = self.park(repo, ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s parked -- " % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertEqual(self.git(repo, "log", "-1", "--format=%s", ticket).stdout.strip(),
                         "WIP: park %s" % ticket)
        self.assertEqual(self.git(repo, "show", "%s:tracked.txt" % ticket).stdout, "x\n")
        self.assertEqual(self.git(repo, "show", "%s:work.txt" % ticket).stdout, "edited\n")
        # pm's own commits move main; the parked work must not be on it.
        self.assertFalse(os.path.exists(os.path.join(repo, "tracked.txt")))
        self.assertNotEqual(self.git(repo, "merge-base", "--is-ancestor", ticket, "main",
                                     check=False).returncode, 0)
        self.git(repo, "merge-base", "--is-ancestor", before, "main")

    def test_already_committed_work_parks_without_wip(self):
        """A park with a clean worktree and commits ahead commits no WIP."""
        repo, ticket, wt_path = self.started()
        tip = self.git(wt_path, "rev-parse", "HEAD").stdout.strip()
        result = self.park(repo, ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertEqual(self.git(repo, "rev-parse", ticket).stdout.strip(), tip)
        self.assertEqual(self.git(repo, "log", "--format=%s", "main..%s" % ticket)
                         .stdout.split("\n")[:-1], ["%s: work" % ticket])

    def test_generated_note_ends_with_resume_line(self):
        """The generated branch/sha/resume note: names the branch and sha and ends with
        the resume line (`wt start ... && wt finish ...`). Old wt: with a session in
        the environment the resume line carries it (`--session s1`); with none it
        carries none."""
        repo, ticket, wt_path = self.started()
        tip = self.git(wt_path, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(self.park(repo, ticket, "--findings", "none").code, 0)
        note = self.park_note(repo, ticket)
        self.assertIn("branch %s @ %s; waits-on (none); resume: " % (ticket, tip), note)
        self.assertTrue(note.endswith("wt start %s --as ada --session s1 && wt finish %s"
                                      % (ticket, ticket)), note)

    def test_resume_line_has_no_session_when_none_is_given(self):
        """`--session ID` is folded into the resume line's `wt start` only when given."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "bare")
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada").code, 0)
        wt_path = self.worktree(repo, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        result = self.wt(repo, "park", ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        note = self.park_note(repo, ticket)
        self.assertNotIn("--session", note)
        self.assertTrue(note.endswith("wt start %s --as ada && wt finish %s"
                                      % (ticket, ticket)), note)

    def test_note_is_prepended_and_resume_stays_last(self):
        """`--note TEXT` is prepended to the generated note; the resume line stays
        last."""
        repo, ticket, wt_path = self.started()
        self.assertEqual(self.park(repo, ticket, "--note", "my-own-words", "--findings",
                                   "none").code, 0)
        note = self.park_note(repo, ticket)
        self.assertTrue(note.startswith("my-own-words; branch %s @ " % ticket), note)
        self.assertTrue(note.endswith("&& wt finish %s" % ticket), note)

    def test_waits_on_note_and_session_in_resume_line(self):
        """`--waits-on <note>` appears as `waits-on <text>` in the note; `--session ID`
        is folded into the resume line's `wt start` only."""
        repo, ticket, wt_path = self.started()
        result = self.park(repo, ticket, "--waits-on", "the-upstream-api", "--session",
                           "sess-9", "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        note = self.park_note(repo, ticket)
        self.assertIn("; waits-on the-upstream-api; resume: ", note)
        self.assertTrue(note.endswith("wt start %s --as ada --session sess-9 && "
                                      "wt finish %s" % (ticket, ticket)), note)
        self.assertIn("waits-on the-upstream-api", result.out)

    def test_findings_reach_the_park(self):
        """`--findings` is passed to the park."""
        repo, ticket, wt_path = self.started()
        result = self.park(repo, ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(result.has_line("wt: no --findings"), result.text)
        self.assertEqual(self.pm.findings(repo, ticket), "none")

    def test_missing_findings_warns_and_parks(self):
        """`finish` and `park` warn when `--findings` is missing."""
        repo, ticket, wt_path = self.started()
        result = self.park(repo, ticket)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: no --findings")
        self.assertEqual(self.pm.status(repo, ticket), "parked")

    def test_findings_required_refuses_before_wip_commit(self):
        """... refuse before any merge or teardown (or WIP commit) once the store sets
        `findings_required`."""
        repo, ticket, wt_path = self.started(findings_required=True)
        tip = self.git(repo, "rev-parse", ticket).stdout.strip()
        self.write(wt_path, "dirty.txt")
        result = self.park(repo, ticket)
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: no --findings")
        self.assert_untouched(repo, ticket, wt_path, tip)
        self.assertTrue(os.path.exists(os.path.join(wt_path, "dirty.txt")))

    def test_zero_delta_park_releases_the_ticket(self):
        """A zero-delta park releases the ticket instead of closing it, so it records
        neither `--note` nor `--findings` and says so; the branch is deleted."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "idle")
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada", session="s1").code, 0)
        wt_path = self.worktree(repo, ticket)
        result = self.park(repo, ticket, "--note", "zero-note", "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s parked with nothing to merge" % ticket)
        self.assert_wt_line(result, "wt: --note/--findings were NOT recorded")
        self.assertEqual(self.pm.status(repo, ticket), "open")
        self.assertEqual(self.pm.holder(repo, ticket), "")
        self.assertFalse(any("zero-note" in n for n in self.pm.notes(repo, ticket)))
        self.assertFalse(os.path.exists(wt_path))
        self.assertFalse(self.branch_exists(repo, ticket))

    def test_local_dir_blocks_the_park(self):
        """A non-empty `<worktree>/.local` blocks the park: nothing committed, ticket
        still taken, worktree intact (gitignored, so it is wt's check, not git's)."""
        repo, ticket, wt_path = self.started()
        self.commit_file(wt_path, ".gitignore", ".local/\n", "%s: ignore" % ticket)
        tip = self.git(repo, "rev-parse", ticket).stdout.strip()
        os.mkdir(os.path.join(wt_path, ".local"))
        self.write(os.path.join(wt_path, ".local"), "state.txt")
        self.write(wt_path, "dirty.txt")
        result = self.park(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: %s/.local is non-empty" % wt_path)
        self.assert_untouched(repo, ticket, wt_path, tip)

    def bulk_deleted(self, count):
        repo, ticket, wt_path = self.started()
        bulk = os.path.join(wt_path, "bulk")
        os.mkdir(bulk)
        for n in range(count):
            self.write(bulk, "f%02d.txt" % n, "%d\n" % n)
        self.git(wt_path, "add", "--", "bulk")
        self.git(wt_path, "commit", "-q", "-m", "%s: bulk" % ticket)
        for n in range(count):
            os.remove(os.path.join(bulk, "f%02d.txt" % n))
        return repo, ticket, wt_path

    def test_mass_deletion_refuses(self):
        """`park` refuses a worktree that is only deletions (>50): nothing committed."""
        repo, ticket, wt_path = self.bulk_deleted(51)
        tip = self.git(repo, "rev-parse", ticket).stdout.strip()
        result = self.park(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: refusing to park %s" % ticket)
        self.assert_untouched(repo, ticket, wt_path, tip)

    def test_fifty_deletions_do_not_refuse(self):
        """The refusal is for more than 50 deletions; 50 park."""
        repo, ticket, wt_path = self.bulk_deleted(50)
        result = self.park(repo, ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertEqual(self.git(repo, "log", "-1", "--format=%s", ticket).stdout.strip(),
                         "WIP: park %s" % ticket)

    def test_lost_git_file_refuses(self):
        """`park` refuses a worktree that has lost its `.git` file."""
        repo, ticket, wt_path = self.started()
        tip = self.git(repo, "rev-parse", ticket).stdout.strip()
        os.remove(os.path.join(wt_path, ".git"))
        result = self.park(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: %s has no .git file" % wt_path)
        self.assert_untouched(repo, ticket, wt_path, tip)

    def test_nested_git_repo_refuses(self):
        """`finish` and `park` refuse (before any merge, WIP commit or remove) a
        worktree holding a nested git repo: names the path and the operator-run
        `rm -rf`; no fault row."""
        repo, ticket, wt_path = self.started()
        self.commit_file(wt_path, ".gitignore", "inner/\n", "%s: ignore" % ticket)
        tip = self.git(repo, "rev-parse", ticket).stdout.strip()
        inner = os.path.join(wt_path, "inner")
        os.makedirs(os.path.join(inner, ".git"))
        self.write(os.path.join(inner, ".git"), "config", "[core]\n")
        self.write(wt_path, "dirty.txt")
        result = self.park(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: worktree %s holds paths the sandbox cannot delete"
                            % wt_path)
        self.assertIn("rm -rf %s" % inner, result.text)
        self.assert_untouched(repo, ticket, wt_path, tip)
        self.assertEqual(self.faults(), [])

    def test_vscode_dir_refuses_the_park(self):
        """`finish` and `park` refuse a worktree holding a `.vscode` dir: nothing
        committed or removed, no fault row. Skips itself where the sandbox denies a
        `.vscode` path segment (run it unsandboxed:
        /usr/bin/python3 -B wt/tests/run_wt.py --cli <wt> --pm old
        -k test_vscode_dir_refuses_the_park -v, expecting `ok` and `failed 0`)."""
        repo, ticket, wt_path = self.started()
        self.commit_file(wt_path, ".gitignore", ".vscode/\n", "%s: ignore" % ticket)
        tip = self.git(repo, "rev-parse", ticket).stdout.strip()
        vscode = os.path.join(wt_path, ".vscode")
        try:
            os.mkdir(vscode)
        except OSError as err:
            self.skipTest("sandbox denies .vscode: %s" % err)
        self.write(wt_path, "dirty.txt")
        result = self.park(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: worktree %s holds paths the sandbox cannot delete"
                            % wt_path)
        self.assertIn("rm -rf %s" % vscode, result.text)
        self.assert_untouched(repo, ticket, wt_path, tip)
        self.assertEqual(self.faults(), [])

    def test_merged_marker_tears_down_and_closes(self):
        """`park` on a branch whose tip equals `refs/wt/merged/<id>` (and is in the
        default branch) tears down and closes the ticket, never parks or releases it."""
        repo, ticket, wt_path = self.started()
        self.git(repo, "merge", "-q", "--ff-only", ticket)
        self.git(repo, "update-ref", "refs/wt/merged/%s" % ticket, "refs/heads/%s" % ticket)
        result = self.park(repo, ticket, "--findings", "none")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(result.has_line("OK: %s parked" % ticket), result.text)
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertFalse(os.path.exists(wt_path))

    def test_failed_remove_prints_stop(self):
        """A failed `git worktree remove` (park) prints a `STOP.` line and never
        invites a retry; the park itself already happened (ticket parked) and a fault
        row is written."""
        repo, ticket, wt_path, cache = self.locked_started()
        result = self.park(repo, ticket, "--findings", "none")
        self.assertNotEqual(result.code, 0, result.text)
        stop = [l for l in result.lines() if l.startswith("wt: STOP.")]
        self.assertEqual(len(stop), 1, result.text)
        self.assertIn("Do not run any further git, wt or pm command", stop[0])
        self.assertIn("do not escalate", stop[0])
        self.assertNotIn("retry", stop[0].lower())
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertEqual(len(self.faults()), 1, self.faults())
        self.assertTrue(self.branch_exists(repo, ticket))

    def test_start_resumes_the_parked_work_and_finish_merges_it(self):
        """Resume later with `wt start`: the worktree comes back with the WIP commit;
        `wt finish` merges it."""
        repo, ticket, wt_path = self.started()
        self.write(wt_path, "wip.txt", "wip\n")
        self.assertEqual(self.park(repo, ticket, "--findings", "none").code, 0)
        self.assertFalse(os.path.exists(wt_path))
        started = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(started.code, 0, started.text)
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertEqual(open(os.path.join(wt_path, "wip.txt")).read(), "wip\n")
        self.assertEqual(self.git(wt_path, "log", "-1", "--format=%s").stdout.strip(),
                         "WIP: park %s" % ticket)
        finished = self.wt(repo, "finish", ticket, "--findings", "none", session="s1")
        self.assertEqual(finished.code, 0, finished.text)
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertTrue(os.path.isfile(os.path.join(repo, "wip.txt")))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))


SHIM = """#!/usr/bin/python3
import os, shutil, sys
argv = sys.argv[1:]
repo, i = os.getcwd(), 0
while i < len(argv) and argv[i].startswith("-"):
    if argv[i] == "-C":
        repo = os.path.join(repo, argv[i + 1])
        i += 2
    elif argv[i] == "-c":
        i += 2
    else:
        i += 1
rest = argv[i:]
state = %(state)r
if rest[:2] == ["worktree", "remove"]:
    admin = os.path.join(repo, ".git", "worktrees", os.path.basename(rest[2]))
    shutil.rmtree(rest[2], ignore_errors=True)
    with open(state, "w") as f:
        f.write(admin)
    sys.stderr.write("error: failed to delete '%%s': Operation not permitted\\n" %% admin)
    sys.exit(255)
if rest[:2] == ["worktree", "prune"] and os.path.exists(state):
    with open(state) as f:
        admin = f.read()
    sys.stderr.write("error: failed to delete '%%s': Operation not permitted\\n" %% admin)
    sys.exit(0)
os.execv("/usr/bin/git", ["git"] + argv)
"""


class DeferredTeardownTest(StartedCase):
    """A git shim fakes the sandbox: `worktree remove` deletes the tree and fails with
    `Operation not permitted` on `.git/worktrees/<id>` (exit 255), `worktree prune`
    prints the same and exits 0; every other git call is real."""

    def shim_dir(self):
        shim = os.path.join(self.root, "shim")
        os.mkdir(shim)
        path = os.path.join(shim, "git")
        with open(path, "w") as f:
            f.write(SHIM % {"state": os.path.join(self.root, "shim-state")})
        os.chmod(path, 0o755)
        return shim

    def prunable(self, repo, wt_path):
        listing = self.git(repo, "worktree", "list", "--porcelain").stdout
        for block in listing.split("\n\n"):
            if os.path.realpath(wt_path) in [os.path.realpath(l[len("worktree "):])
                                             for l in block.splitlines()
                                             if l.startswith("worktree ")]:
                return any(l.startswith("prunable") for l in block.splitlines())
        return False

    def assert_deferred(self, result, repo, ticket, wt_path, kind):
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: worktree for %s is gone but its leftover "
                            "registration" % ticket)
        self.assertTrue(result.has_line("OK: %s " % ticket), result.text)
        line = [l for l in result.lines() if l.startswith("wt: worktree for ")]
        self.assertEqual(len(line), 1, result.text)
        self.assertIn("This is infrastructure, not a finding: file no ticket and write no "
                      "retro.", line[0])
        if kind == "finish":
            self.assertIn("registration and branch deferred to wt prune, ticket closed",
                          result.out)
        self.assertFalse(result.has_line("wt: STOP."), result.text)
        low = result.text.lower()
        for word in ("retry", "re-run", "--force", "escalate", "disable"):
            self.assertNotIn(word, low)
        self.assertFalse(os.path.exists(wt_path))
        self.assertTrue(self.prunable(repo, wt_path))
        self.assertTrue(any(n.endswith("-wt-%s-teardown-deferred.md" % kind)
                            for n in self.faults()), self.faults())
        self.assertTrue(os.path.exists(os.path.join(repo, ".git", "worktrees", ".keep",
                                                    "locked")))

    def test_finish_deferred(self):
        """`finish` prints the deferred line, then `OK:` naming the deferral; ticket
        done, branch kept, registration prunable, fault row, keep entry."""
        repo, ticket, wt_path = self.started()
        result = self.wt(repo, "finish", ticket, "--findings", "none", session="s1",
                         path_first=self.shim_dir())
        self.assert_deferred(result, repo, ticket, wt_path, "finish")
        self.assertEqual(self.pm.status(repo, ticket), "done")
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertTrue(os.path.isfile(os.path.join(repo, "work.txt")))

    def test_park_deferred(self):
        """`park` prints the same shape; ticket parked, branch kept."""
        repo, ticket, wt_path = self.started()
        result = self.wt(repo, "park", ticket, "--findings", "none", session="s1",
                         path_first=self.shim_dir())
        self.assert_deferred(result, repo, ticket, wt_path, "park")
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertTrue(self.branch_exists(repo, ticket))

    def test_zero_delta_park_deferred(self):
        """A zero-delta park under the fake releases the ticket (`open`)."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "idle")
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada", session="s1").code, 0)
        wt_path = self.worktree(repo, ticket)
        result = self.wt(repo, "park", ticket, session="s1", path_first=self.shim_dir())
        self.assert_deferred(result, repo, ticket, wt_path, "park")
        self.assertEqual(self.pm.status(repo, ticket), "open")
        self.assertEqual(self.pm.holder(repo, ticket), "")
        self.assertIn("registration deferred to wt prune", result.out)

    def test_prune_clears_the_debt(self):
        """`wt prune` (real git) clears the registration and deletes the merged
        branch."""
        repo, ticket, wt_path = self.started()
        self.assertEqual(self.wt(repo, "finish", ticket, "--findings", "none",
                                 session="s1", path_first=self.shim_dir()).code, 0)
        self.assertTrue(self.prunable(repo, wt_path))
        self.assertTrue(self.branch_exists(repo, ticket))
        pruned = self.wt(repo, "prune")
        self.assertEqual(pruned.code, 0, pruned.text)
        self.assertFalse(self.prunable(repo, wt_path))
        self.assertNotIn(os.path.realpath(wt_path),
                         self.git(repo, "worktree", "list", "--porcelain").stdout)
        self.assertFalse(self.branch_exists(repo, ticket))


LOG_SHIM = """#!/bin/sh
for a in "$@"; do printf '%%s\\t' "$a"; done >> %(log)s
printf '\\n' >> %(log)s
exec %(real)s "$@"
"""


class NeverForceTest(StartedCase):
    """`wt` never runs `branch -D`, `worktree remove --force` or `rm -rf`: logging
    `git` and `rm` shims (they pass everything to the real tools) record every argv."""

    def logged(self):
        shim = os.path.join(self.root, "log-shim")
        os.mkdir(shim)
        self.git_log = os.path.join(self.root, "git-argv.log")
        self.rm_log = os.path.join(self.root, "rm-argv.log")
        for name, log, real in (("git", self.git_log, "/usr/bin/git"),
                                ("rm", self.rm_log, "/bin/rm")):
            path = os.path.join(shim, name)
            with open(path, "w") as f:
                f.write(LOG_SHIM % {"log": shlex.quote(log), "real": real})
            os.chmod(path, 0o755)
        return shim

    def calls(self, log):
        if not os.path.exists(log):
            return []
        with open(log) as f:
            return [line.rstrip("\n").split("\t")[:-1] for line in f if line.strip()]

    def subcommand(self, argv):
        i = 0
        while i < len(argv) and argv[i].startswith("-"):
            i += 2 if argv[i] in ("-C", "-c") else 1
        return (argv[i], argv[i + 1:]) if i < len(argv) else ("", [])

    def shorts(self, args):
        return "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))

    def forbidden_git(self):
        found = []
        for argv in self.calls(self.git_log):
            sub, rest = self.subcommand(argv)
            letters = self.shorts(rest)
            if sub == "branch":
                delete = "--delete" in rest or "d" in letters or "D" in letters
                force = "--force" in rest or "f" in letters or "D" in letters
                if "D" in letters or (delete and force):
                    found.append(argv)
            if sub == "worktree" and rest[:1] == ["remove"]:
                if "--force" in rest or "f" in self.shorts(rest[1:]):
                    found.append(argv)
        return found

    def forbidden_rm(self):
        return [argv for argv in self.calls(self.rm_log)
                if "--recursive" in argv or "r" in self.shorts(argv) or "R" in self.shorts(argv)]

    def saw(self, *words):
        return any(self.subcommand(argv)[0] == words[0]
                   and self.subcommand(argv)[1][:len(words) - 1] == list(words[1:])
                   for argv in self.calls(self.git_log))

    def assert_never_forced(self):
        self.assertEqual(self.forbidden_git(), [])
        self.assertEqual(self.forbidden_rm(), [])

    def test_start_finish_never_forces(self):
        """`wt` never runs `branch -D`, `worktree remove --force`, `rm -rf` (a full
        start and finish)."""
        shim = self.logged()
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "work")
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada", session="s1",
                                 path_first=shim).code, 0)
        wt_path = self.worktree(repo, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        result = self.wt(repo, "finish", ticket, "--findings", "none", session="s1",
                         path_first=shim)
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(self.saw("worktree", "remove"), self.calls(self.git_log))
        self.assertTrue(self.saw("branch", "-d"), self.calls(self.git_log))
        self.assert_never_forced()

    def test_start_park_never_forces(self):
        """The same for a start and a park."""
        shim = self.logged()
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "work")
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada", session="s1",
                                 path_first=shim).code, 0)
        wt_path = self.worktree(repo, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        result = self.wt(repo, "park", ticket, "--findings", "none", session="s1",
                         path_first=shim)
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(self.saw("worktree", "remove"), self.calls(self.git_log))
        self.assert_never_forced()

    def test_failed_remove_never_forces(self):
        """The same on a failed remove: the STOP line hands the operator `--force`, wt
        itself does not run it."""
        shim = self.logged()
        repo, ticket, wt_path, cache = self.locked_started()
        result = self.wt(repo, "finish", ticket, "--findings", "none", session="s1",
                         path_first=shim)
        self.assertNotEqual(result.code, 0, result.text)
        self.assertTrue(result.has_line("wt: STOP."), result.text)
        self.assertTrue(self.saw("worktree", "remove"), self.calls(self.git_log))
        self.assert_never_forced()


class StatusPruneTest(StartedCase):
    shim_dir = DeferredTeardownTest.shim_dir
    prunable = DeferredTeardownTest.prunable

    def registered(self, repo, wt_path):
        return os.path.realpath(wt_path) in [
            os.path.realpath(l[len("worktree "):])
            for l in self.git(repo, "worktree", "list", "--porcelain").stdout.splitlines()
            if l.startswith("worktree ")]

    def status_line(self, result, wt_path):
        rows = [l for l in result.lines() if l.startswith(wt_path + "  ")]
        self.assertEqual(len(rows), 1, result.text)
        return rows[0]

    def stale(self, repo, name, commit=False):
        """A ticket started by wt whose worktree directory is then deleted by test code
        (not wt): the registration stays. Returns (ticket, wt_path)."""
        ticket = self.pm.file_ticket(repo, name)
        self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada", session="s1").code, 0)
        wt_path = self.worktree(repo, ticket)
        if commit:
            self.commit_file(wt_path, "%s.txt" % ticket, "x\n", "%s: work" % ticket)
        shutil.rmtree(wt_path)
        return ticket, wt_path

    def test_status_lists_worktrees_with_ticket_status(self):
        """`status` lists live worktrees joined against their tickets; a worktree with
        no ticket behind it shows as FOREIGN/ORPHAN. Old wt line shape:
        `<path>  <branch>  <pm status>` (the old pm's words)."""
        repo, ticket, wt_path = self.started()
        self.git(repo, "worktree", "add", "-q", "-b", "stray",
                 os.path.join(repo, ".wt", "stray"))
        result = self.wt(repo, "status")
        self.assertEqual(result.code, 0, result.text)
        mine = self.status_line(result, wt_path)
        words = {"taken", "claimed"}
        self.assertTrue(mine.startswith("%s  %s  " % (wt_path, ticket)), mine)
        self.assertIn(mine.split("  ", 2)[2].split(" ")[0], words, mine)
        orphan = self.status_line(result, os.path.join(repo, ".wt", "stray"))
        self.assertTrue(orphan.startswith("%s  stray  FOREIGN/ORPHAN" %
                                          os.path.join(repo, ".wt", "stray")), orphan)
        self.assertFalse(any(l.startswith(repo + "  ") for l in result.lines()), result.text)

    def test_status_with_no_worktrees(self):
        """`status` with only the main checkout prints one line."""
        repo = self.make_repo()
        result = self.wt(repo, "status")
        self.assertEqual(result.code, 0, result.text)
        self.assertEqual(result.out.strip(), "no worktrees besides the main checkout")

    def test_status_after_park_does_not_list_the_ticket(self):
        """`park` ... the worktree directory is gone at once: a just-parked ticket is
        not listed by status."""
        repo, ticket, wt_path = self.started()
        self.assertEqual(self.wt(repo, "park", ticket, "--findings", "none",
                                 session="s1").code, 0)
        result = self.wt(repo, "status")
        self.assertEqual(result.code, 0, result.text)
        self.assertNotIn(ticket, result.text)
        self.assertEqual(result.out.strip(), "no worktrees besides the main checkout")

    def test_status_labels_deferred_teardown(self):
        """A registration whose directory is gone is labelled `deferred-teardown`."""
        repo = self.make_repo()
        ticket, wt_path = self.stale(repo, "gone")
        self.assertTrue(self.prunable(repo, wt_path))
        result = self.wt(repo, "status")
        self.assertEqual(result.code, 0, result.text)
        row = self.status_line(result, wt_path)
        self.assertTrue(row.startswith("%s  %s  deferred-teardown" % (wt_path, ticket)), row)

    def test_park_waits_on_ticket_id_records_a_dependency_and_note(self):
        """`park --waits-on <ticket-id>`: the contract names only the free-text form.
        Old wt records BOTH the note (`waits-on <id>`) and a pm dependency of the parked
        ticket on the blocker; wt prints no extra line for it."""
        repo, ticket, wt_path = self.started()
        blocker = self.pm.file_ticket(repo, "blocker")
        result = self.wt(repo, "park", ticket, "--waits-on", blocker, "--findings", "none",
                         session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: %s parked -- " % ticket)
        self.assertEqual(self.pm.status(repo, ticket), "parked")
        self.assertEqual(self.pm.blockers(repo, ticket), [blocker])
        self.assertTrue(any("waits-on %s;" % blocker in n
                            for n in self.pm.notes(repo, ticket)), self.pm.notes(repo, ticket))
        self.assertFalse(result.has_line("wt: "), result.text)

    def test_pending_lists_done_unmerged_with_cleared_blockers(self):
        """`pending` lists `done-unmerged` tickets. Old wt: one line `<id>  P<n>
        <clean|CONFLICT>  <title>`; a ticket whose blocker is still open is not listed;
        once the blocker is closed it is."""
        if SIDE == "new":
            self.skipTest("dropped for pm ls parked")
        repo, ticket, wt_path = self.started()
        blocker = self.pm.file_ticket(repo, "the blocker")
        self.assertEqual(self.wt(repo, "park", ticket, "--waits-on", blocker, "--findings",
                                 "none", session="s1").code, 0)
        waiting = self.wt(repo, "pending")
        self.assertEqual(waiting.code, 0, waiting.text)
        self.assertEqual(waiting.out.strip(),
                         "no done-unmerged tickets with cleared blockers")
        self.pm.take(repo, blocker, "ada", session="s1")
        sh(["pm", "ticket", "close", blocker, "--findings", "none"], repo,
           self.call_env("s1"))
        self.assertEqual(self.pm.status(repo, blocker), "done")
        cleared = self.wt(repo, "pending")
        self.assertEqual(cleared.code, 0, cleared.text)
        rows = [l for l in cleared.lines() if l.startswith(ticket + "  ")]
        self.assertEqual(len(rows), 1, cleared.text)
        self.assertRegex(rows[0], r"^%s  P\d  clean  work$" % ticket)
        # Old pm: a closed blocker no longer shows in `blocked_by`.
        self.assertEqual(self.pm.blockers(repo, ticket), [])

    def test_prune_clears_registration_keeps_keep_entry_and_unmerged_branch(self):
        """`prune` clears a registration whose directory is gone and keeps the `.keep`
        entry; it deletes the branch of a cleared registration only when it is an
        ancestor of main (`OK: wt prune -- N registration(s) cleared, M remain, K
        branch(es) deleted: <ids>`), and keeps an unmerged branch."""
        repo = self.make_repo()
        merged = self.pm.file_ticket(repo, "merged")
        unmerged = self.pm.file_ticket(repo, "unmerged")
        paths = []
        for ticket in (merged, unmerged):
            self.assertEqual(self.wt(repo, "start", ticket, "--as", "ada",
                                     session="s1").code, 0)
            paths.append(self.worktree(repo, ticket))
        self.commit_file(paths[1], "u.txt", "x\n", "%s: work" % unmerged)
        merged_path, unmerged_path = paths
        shutil.rmtree(merged_path)
        shutil.rmtree(unmerged_path)
        result = self.wt(repo, "prune")
        self.assertEqual(result.code, 0, result.text)
        self.assertEqual(result.out.strip(), "OK: wt prune -- 2 registration(s) cleared, "
                         "0 remain, 1 branch(es) deleted: %s" % merged)
        self.assertFalse(self.registered(repo, merged_path))
        self.assertFalse(self.registered(repo, unmerged_path))
        self.assertFalse(self.branch_exists(repo, merged))
        self.assertTrue(self.branch_exists(repo, unmerged))
        self.assertTrue(os.path.exists(os.path.join(repo, ".git", "worktrees", ".keep",
                                                    "locked")))

    def test_prune_keeps_a_branch_a_worktree_holds(self):
        """`prune` deletes a branch only when no worktree holds it: a merged-marker
        branch checked out in a live worktree stays."""
        repo, ticket, wt_path = self.started()
        self.git(repo, "update-ref", "refs/wt/merged/%s" % ticket, "refs/heads/main")
        self.git(repo, "branch", "-f", "-q", "stale-marked", "main")
        self.git(repo, "update-ref", "refs/wt/merged/stale-marked", "refs/heads/main")
        self.git(repo, "branch", "-f", "-q", "plain-merged", "main")
        result = self.wt(repo, "prune")
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(self.branch_exists(repo, ticket))
        self.assertTrue(os.path.isdir(wt_path))
        self.assertFalse(self.branch_exists(repo, "stale-marked"))
        self.assertTrue(self.branch_exists(repo, "plain-merged"))

    def test_prune_prints_remaining_registrations(self):
        """`prune` when the sandbox still denies the delete (git shim): the `wt: N
        deferred-teardown registration(s) remain` line, then `OK: wt prune -- 0
        registration(s) cleared, 1 remain, 0 branch(es) deleted`."""
        repo, ticket, wt_path = self.started()
        shim = self.shim_dir()
        self.assertEqual(self.wt(repo, "finish", ticket, "--findings", "none",
                                 session="s1", path_first=shim).code, 0)
        result = self.wt(repo, "prune", path_first=shim)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: 1 deferred-teardown registration(s) remain")
        remain = [l for l in result.lines() if l.startswith("wt: 1 deferred-teardown")]
        self.assertEqual(len(remain), 1, result.text)
        self.assertTrue(remain[0].endswith("Operator: !git -C %s worktree prune" % repo),
                        remain[0])
        self.assertIn("OK: wt prune -- 0 registration(s) cleared, 1 remain, "
                      "0 branch(es) deleted", result.out)
        self.assertTrue(self.prunable(repo, wt_path))

    def test_start_runs_prune_quietly(self):
        """A stale registration is gone after an unrelated `wt start`, and start prints
        no prune output."""
        repo = self.make_repo()
        gone, gone_path = self.stale(repo, "gone")
        other = self.pm.file_ticket(repo, "other")
        result = self.wt(repo, "start", other, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertFalse(self.registered(repo, gone_path))
        self.assertFalse([l for l in result.lines()
                          if "prune" in l.lower() or "registration" in l.lower()
                          or "deferred" in l.lower()], result.text)
        self.assertFalse(result.has_line("wt: "), result.text)

    def test_start_twice_from_the_same_session(self):
        """Not stated by the contract, so state only (the old wt exits 1 with a
        `git worktree add ... failed` line; a new wt may be idempotent): the worktree
        still exists at the same tip, the ticket is `taken` by the same holder, and
        there is one registration for it. Exit code and output are not pinned."""
        repo, ticket, wt_path = self.started()
        tip = self.git(wt_path, "rev-parse", "HEAD").stdout.strip()
        holder = self.pm.holder(repo, ticket)
        self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertTrue(os.path.isdir(wt_path))
        self.assertEqual(self.git(wt_path, "rev-parse", "HEAD").stdout.strip(), tip)
        self.assertEqual(self.pm.status(repo, ticket), "taken")
        self.assertEqual(self.pm.holder(repo, ticket), holder)
        listing = self.git(repo, "worktree", "list", "--porcelain").stdout
        self.assertEqual(sum(1 for l in listing.splitlines()
                             if l.startswith("worktree ")
                             and os.path.realpath(l[len("worktree "):])
                             == os.path.realpath(wt_path)), 1, listing)

    def test_selftest_exits_zero(self):
        """`selftest` exits 0, prints its case lines (`ok: ...`) and a final line `SELFTEST
        PASSED` with no failure line; it leaves no worktree registration in the cwd repo,
        no fault row and no scratch behind (its scratch path is not pinned)."""
        repo = self.make_repo()
        result = self.wt(repo, "selftest")
        self.assertEqual(result.code, 0, result.text[-2000:])
        out = [l for l in result.out.splitlines() if l.strip()]
        self.assertTrue(any(l.startswith("ok: ") for l in out), result.text[-2000:])
        self.assertTrue(out[-1].startswith("SELFTEST PASSED"), out[-1])
        self.assertFalse(result.has_line("SELFTEST FAILED"), result.text[-2000:])
        self.assertFalse(any(l.startswith("FAIL") or l.startswith("fail") for l in out),
                         result.text[-2000:])
        self.assertEqual(self.git(repo, "worktree", "list").stdout.count("\n"), 1)
        self.assertEqual(self.faults(), [])
        left = []
        for top, dirs, files in os.walk(self.root):
            if top == os.path.join(self.root, "repos"):
                dirs[:] = [d for d in dirs if d != os.path.basename(repo)]
            # Old wt leaves three `wt-selftest-*pairs*.json` files in $TMPDIR (files,
            # not scratch repos); only a leftover directory fails.
            left += [n for n in dirs if n.startswith("wt-selftest")]
        self.assertEqual(left, [])


class ResolutionTest(StartedCase):
    SUBS = ["add", "commit", "worktree", "branch", "merge", "rebase", "update-ref",
            "switch", "reset", "tag", "stash", "restore", "rm", "mv", "fetch", "pull"]

    def pair(self, source, *targets):
        """Declare git-pairs pairs source -> each target in the private pairs file: wt
        refuses a cross-repo mutation the pairs file does not declare (an old-wt rule
        outside this ticket's verbs), and every case here crosses repos."""
        path = self.env["GIT_PAIRS_FILE"]
        with open(path) as f:
            data = json.load(f)
        data["pairs"].append({"source": source, "targets": list(targets),
                              "git": self.SUBS})
        with open(path, "w") as f:
            json.dump(data, f)

    def two(self, a_prefix="aa", b_prefix="bb"):
        a = self.make_repo(name="repo-a", prefix=a_prefix)
        b = self.make_repo(name="repo-b", prefix=b_prefix)
        self.pair(a, b)
        self.pair(b, a)
        return a, b

    def test_unregistered_prefix_uses_cwd_repo(self):
        """Without `--store`, an unregistered prefix: the store is the cwd repo. The new
        pm registers every store at init, so the repo is unregistered first
        (`unregister_store`; a no-op on the old side)."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "here")
        self.pm.unregister_store(repo)
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(os.path.isdir(self.worktree(repo, ticket)))
        self.assertEqual(self.pm.status(repo, ticket), "taken")

    def test_registered_prefix_from_another_repo(self):
        """A prefix registered to repo B, `start` run with cwd in repo A: the ticket is
        taken in B and the worktree is `B/.wt/<id>`."""
        a, b = self.two()
        self.pm.register_store("bb", b)
        ticket = self.pm.file_ticket(b, "there")
        result = self.wt(a, "start", ticket, "--as", "ada", session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertEqual(self.pm.status(b, ticket), "taken")
        self.assertTrue(os.path.isdir(self.worktree(b, ticket)))
        self.assertFalse(os.path.exists(self.worktree(a, ticket)))

    def test_two_owners_stop_with_a_wt_line(self):
        """A prefix registered to two stores stops with a `wt:` line; nothing claimed.
        Old side only: the new pm routes a shared prefix itself (design.md, Ids and the
        registry), so there it skips."""
        if SIDE == "new":
            self.skipTest("the new pm routes a shared prefix itself (design.md, Ids "
                          "and the registry)")
        a, b = self.two()
        b2 = self.make_repo(name="repo-b2", prefix="bb")
        self.pm.register_store("bb", b)
        self.pm.register_store("bb", b2)
        ticket = self.pm.file_ticket(b, "ambiguous")
        result = self.wt(a, "start", ticket, "--as", "ada", session="s1")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: `pm ticket where %s` failed (exit 1): pm: prefix "
                            "'bb' is owned by two registered stores" % ticket)
        self.assertEqual(self.pm.status(b, ticket), "open")
        self.assertFalse(os.path.exists(self.worktree(b, ticket)))
        self.assertFalse(os.path.exists(self.worktree(a, ticket)))

    def test_pm_missing_stops_start_with_a_wt_line(self):
        """Any other `where` failure (two owners, pm missing) stops with pm's message:
        with pm off PATH `start` stops with a `wt:` line and creates nothing."""
        repo = self.make_repo()
        ticket = self.pm.file_ticket(repo, "nopm")
        result = self.wt(repo, "start", ticket, "--as", "ada", session="s1",
                         path="/usr/bin:/bin")
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: could not run `pm ")
        self.assertFalse(os.path.exists(self.worktree(repo, ticket)))
        self.assertFalse(self.branch_exists(repo, ticket))
        self.assertEqual(self.pm.status(repo, ticket), "open")

    def test_registered_prefix_resolves_finish_and_park_too(self):
        """A prefix registered to repo B resolves for `finish` and `park` run with cwd in
        repo A, not only `start`: merged and closed in B, parked in B."""
        a, b = self.two()
        self.pm.register_store("bb", b)
        done_ticket = self.pm.file_ticket(b, "to finish")
        park_ticket = self.pm.file_ticket(b, "to park")
        paths = {}
        for ticket in (done_ticket, park_ticket):
            started = self.wt(a, "start", ticket, "--as", "ada", session="s1")
            self.assertEqual(started.code, 0, started.text)
            paths[ticket] = self.worktree(b, ticket)
            self.commit_file(paths[ticket], "%s.txt" % ticket, "x\n", "%s: work" % ticket)
        finished = self.wt(a, "finish", done_ticket, "--findings", "none", session="s1")
        self.assertEqual(finished.code, 0, finished.text)
        self.assertTrue(os.path.isfile(os.path.join(b, "%s.txt" % done_ticket)))
        self.assertEqual(self.pm.status(b, done_ticket), "done")
        parked = self.wt(a, "park", park_ticket, "--findings", "none", session="s1")
        self.assertEqual(parked.code, 0, parked.text)
        self.assertEqual(self.pm.status(b, park_ticket), "parked")
        self.assertTrue(self.branch_exists(b, park_ticket))
        self.assertFalse(os.path.exists(paths[park_ticket]))
        self.assertFalse(os.path.exists(self.worktree(a, park_ticket)))

    def test_store_flag_overrides_lookup_and_sets_the_target(self):
        """`--store <path>` names the repo whose store holds the ticket for an
        unregistered store; the worktree target defaults to that store's repo."""
        a, s = self.two("aa", "ss")
        ticket = self.pm.file_ticket(s, "via flag")
        result = self.wt(a, "start", ticket, "--as", "ada", "--store", s, session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertEqual(self.pm.status(s, ticket), "taken")
        self.assertTrue(os.path.isdir(self.worktree(s, ticket)))
        self.assertFalse(os.path.exists(self.worktree(a, ticket)))

    def test_repo_flag_overrides_the_target_independently(self):
        """`--repo <path>` overrides the worktree target; the ticket stays in the
        `--store` repo."""
        a, s = self.two("aa", "ss")
        ticket = self.pm.file_ticket(s, "split")
        result = self.wt(a, "start", ticket, "--as", "ada", "--store", s, "--repo", a,
                         session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertEqual(self.pm.status(s, ticket), "taken")
        self.assertTrue(os.path.isdir(self.worktree(a, ticket)))
        self.assertFalse(os.path.exists(self.worktree(s, ticket)))

    def split_started(self):
        a, s = self.two("aa", "ss")
        ticket = self.pm.file_ticket(s, "split")
        elsewhere = self.make_repo(name="cwd-only", prefix="cc")
        self.pair(elsewhere, a, s)
        self.assertEqual(self.wt(elsewhere, "start", ticket, "--as", "ada", "--store", s,
                                 "--repo", a, session="s1").code, 0)
        wt_path = self.worktree(a, ticket)
        self.commit_file(wt_path, "work.txt", "work\n", "%s: work" % ticket)
        return elsewhere, a, s, ticket, wt_path

    def test_finish_takes_store_and_repo_flags(self):
        """The same flags on `finish`: merged into the `--repo` repo's default branch,
        ticket closed in the `--store` repo."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        result = self.wt(elsewhere, "finish", ticket, "--findings", "none", "--store", s,
                         "--repo", a, session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(os.path.isfile(os.path.join(a, "work.txt")))
        self.assertFalse(os.path.exists(wt_path))
        self.assertEqual(self.pm.status(s, ticket), "done")

    def test_park_takes_store_and_repo_flags(self):
        """The same flags on `park`: branch kept in the `--repo` repo, ticket parked in
        the `--store` repo."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        result = self.wt(elsewhere, "park", ticket, "--findings", "none", "--store", s,
                         "--repo", a, session="s1")
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(self.branch_exists(a, ticket))
        self.assertFalse(os.path.exists(wt_path))
        self.assertEqual(self.pm.status(s, ticket), "parked")

    def refused_untouched(self, result, store, repo, ticket, status):
        self.assertNotEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "wt: cross-repo ")
        self.assertEqual(self.pm.status(store, ticket), status)
        for where in (store, repo):
            self.assertFalse(os.path.exists(self.worktree(where, ticket)) and status == "open")
            self.assertFalse(self.branch_exists(where, ticket) and status == "open")

    def test_undeclared_pair_refuses_start_and_mutates_nothing(self):
        """store/repo guard: a `--store` into another repo with no declared pair in
        $GIT_PAIRS_FILE refuses with the `wt: cross-repo` line before the claim."""
        a = self.make_repo(name="repo-a", prefix="aa")
        s = self.make_repo(name="repo-s", prefix="ss")
        ticket = self.pm.file_ticket(s, "far")
        before = (self.git(a, "rev-parse", "HEAD").stdout, self.git(s, "rev-parse", "HEAD").stdout)
        result = self.wt(a, "start", ticket, "--as", "ada", "--store", s, session="s1")
        self.refused_untouched(result, s, a, ticket, "open")
        self.assertEqual(self.pm.holder(s, ticket), "")
        self.assertEqual(before, (self.git(a, "rev-parse", "HEAD").stdout,
                                  self.git(s, "rev-parse", "HEAD").stdout))
        self.assertEqual(self.git(a, "worktree", "list").stdout.count("\n"), 1)
        self.assertEqual(self.git(s, "worktree", "list").stdout.count("\n"), 1)

    def test_undeclared_pair_refuses_a_repo_flag(self):
        """The same guard on the worktree target: `--repo` into another repo with no
        declared pair refuses; the ticket is not claimed."""
        a = self.make_repo(name="repo-a", prefix="aa")
        s = self.make_repo(name="repo-s", prefix="ss")
        ticket = self.pm.file_ticket(s, "far")
        result = self.wt(s, "start", ticket, "--as", "ada", "--repo", a, session="s1")
        self.refused_untouched(result, s, a, ticket, "open")

    def test_undeclared_pair_refuses_finish_and_mutates_nothing(self):
        """The same guard on `finish`: with the pairs file emptied after the start,
        nothing is merged, the worktree stays and the ticket stays claimed."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        with open(self.env["GIT_PAIRS_FILE"], "w") as f:
            json.dump({"pairs": []}, f)
        before = self.git(a, "rev-parse", "main").stdout
        result = self.wt(elsewhere, "finish", ticket, "--findings", "none", "--store", s,
                         "--repo", a, session="s1")
        self.refused_untouched(result, s, a, ticket, "taken")
        self.assertEqual(self.git(a, "rev-parse", "main").stdout, before)
        self.assertTrue(os.path.isdir(wt_path))
        self.assertTrue(self.branch_exists(a, ticket))

    def test_undeclared_pair_refuses_park_and_mutates_nothing(self):
        """The same guard on `park`: with the pairs file emptied after the start, no WIP
        commit, the worktree and branch stay and the ticket stays claimed."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        with open(os.path.join(wt_path, "dirty.txt"), "w") as f:
            f.write("dirty\n")
        with open(self.env["GIT_PAIRS_FILE"], "w") as f:
            json.dump({"pairs": []}, f)
        tip = self.git(a, "rev-parse", ticket).stdout.strip()
        main = self.git(a, "rev-parse", "main").stdout
        store_main = self.git(s, "rev-parse", "HEAD").stdout
        result = self.wt(elsewhere, "park", ticket, "--findings", "none", "--store", s,
                         "--repo", a, session="s1")
        self.refused_untouched(result, s, a, ticket, "taken")
        self.assertEqual(self.git(a, "rev-parse", ticket).stdout.strip(), tip)
        self.assertEqual(self.git(a, "rev-parse", "main").stdout, main)
        self.assertEqual(self.git(s, "rev-parse", "HEAD").stdout, store_main)
        self.assertTrue(os.path.isdir(wt_path))
        self.assertTrue(os.path.isfile(os.path.join(wt_path, "dirty.txt")))
        self.assertTrue(self.branch_exists(a, ticket))

    def test_undeclared_pair_refuses_land_and_mutates_nothing(self):
        """The same guard on `land`: with the pairs file emptied after the start,
        nothing is merged, the worktree stays and the ticket stays claimed."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        with open(self.env["GIT_PAIRS_FILE"], "w") as f:
            json.dump({"pairs": []}, f)
        before = self.git(a, "rev-parse", "main").stdout
        result = self.wt(elsewhere, "land", ticket, "--store", s, "--repo", a, session="s1")
        self.refused_untouched(result, s, a, ticket, "taken")
        self.assertEqual(self.git(a, "rev-parse", "main").stdout, before)
        self.assertTrue(os.path.isdir(wt_path))
        self.assertTrue(self.branch_exists(a, ticket))

    def test_partial_pair_refuses_finish_and_mutates_nothing(self):
        """The guard is per git subcommand (crossrepo.pair_allows checks the pair's
        `git` list): a pair declared for `commit` only, with `worktree`, `merge` and
        the rest undeclared, still refuses `finish`; nothing is merged."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        with open(self.env["GIT_PAIRS_FILE"], "w") as f:
            json.dump({"pairs": [{"source": elsewhere, "targets": [a, s],
                                  "git": ["commit"]}]}, f)
        before = self.git(a, "rev-parse", "main").stdout
        result = self.wt(elsewhere, "finish", ticket, "--findings", "none", "--store", s,
                         "--repo", a, session="s1")
        self.refused_untouched(result, s, a, ticket, "taken")
        self.assertEqual(self.git(a, "rev-parse", "main").stdout, before)
        self.assertTrue(os.path.isdir(wt_path))
        self.assertTrue(self.branch_exists(a, ticket))

    def test_status_takes_store_and_repo_flags(self):
        """The same flags on `status`: worktrees of `--repo`, joined against the
        `--store` repo's tickets."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        result = self.wt(elsewhere, "status", "--store", s, "--repo", a)
        self.assertEqual(result.code, 0, result.text)
        self.assertTrue(any(l.startswith("%s  %s  " % (wt_path, ticket)) and
                            "FOREIGN" not in l for l in result.lines()), result.text)

    def test_prune_takes_a_repo_flag(self):
        """The same flags on `prune`: clears the stale registration in the `--repo`
        repo while cwd is another repo."""
        elsewhere, a, s, ticket, wt_path = self.split_started()
        shutil.rmtree(wt_path)
        result = self.wt(elsewhere, "prune", "--store", s, "--repo", a)
        self.assertEqual(result.code, 0, result.text)
        self.assert_wt_line(result, "OK: wt prune -- 1 registration(s) cleared")
        self.assertNotIn(os.path.realpath(wt_path),
                         self.git(a, "worktree", "list", "--porcelain").stdout)


if __name__ == "__main__":
    unittest.main()
