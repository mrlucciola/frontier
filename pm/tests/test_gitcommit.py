"""Tests for pm/tools/gitcommit.py: env scrub, ref commits, fault classifier."""
import importlib.util
import io
import os
import subprocess
import tempfile
import types
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "gitcommit", os.path.join(HERE, "..", "tools", "gitcommit.py"))
gitcommit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gitcommit)


def _git(path, *argv):
    r = subprocess.run(["git", "-C", path, *argv], capture_output=True,
                       text=True, env=gitcommit.clean_env())
    assert r.returncode == 0, f"git {' '.join(argv)}: {r.stderr}"
    return r


def _scoped_env(test, values):
    patcher = unittest.mock.patch.dict(os.environ, values)
    patcher.start()
    test.addCleanup(patcher.stop)


def _mkrepo(path):
    os.makedirs(path)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.name", "t")
    _git(path, "config", "user.email", "t@example.invalid")
    _git(path, "config", "commit.gpgsign", "false")
    with open(os.path.join(path, "seed"), "w") as f:
        f.write("seed\n")
    _git(path, "add", "seed")
    _git(path, "commit", "-q", "-m", "seed")
    return path


class GitDirScrubTest(unittest.TestCase):
    """Ambient GIT_DIR/GIT_INDEX_FILE point at a decoy; the commit must land in
    the target repo and leave the decoy untouched."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        _scoped_env(self, {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"})
        self.decoy = _mkrepo(os.path.join(self.base, "decoy"))
        self.target = _mkrepo(os.path.join(self.base, "target"))
        os.environ["GIT_DIR"] = os.path.join(self.decoy, ".git")
        os.environ["GIT_WORK_TREE"] = self.decoy
        os.environ["GIT_INDEX_FILE"] = os.path.join(self.decoy, ".git", "index")

    def _log(self, path):
        return _git(path, "log", "--format=%s").stdout.splitlines()

    def test_commit_paths_lands_in_target_not_decoy(self):
        decoy_before = self._log(self.decoy)
        with open(os.path.join(self.target, "f"), "w") as f:
            f.write("x\n")
        self.assertIsNone(gitcommit.commit_paths(self.target, ["f"], "add f"))
        self.assertEqual(self._log(self.target)[0], "add f")
        self.assertEqual(self._log(self.decoy), decoy_before)
        self.assertEqual(_git(self.decoy, "status", "--porcelain").stdout, "")


REF = "refs/heads/pm-store"
STUB_GPG = """#!/bin/sh
echo "$@" >> "$0.log"
cat > /dev/null
echo "[GNUPG:] SIG_CREATED D 1 8 00 0 0 0 0 stub" >&2
printf -- '-----BEGIN PGP SIGNATURE-----\\n\\nc3R1Yg==\\n-----END PGP SIGNATURE-----\\n'
"""


class CommitBlobToRefTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        _scoped_env(self, {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"})
        self.repo = _mkrepo(os.path.join(self.base, "r"))
        os.makedirs(os.path.join(self.repo, ".pm"))
        self.rel = ".pm/tickets.jsonl"
        self.write("one\n")

    def write(self, text):
        with open(os.path.join(self.repo, self.rel), "w") as f:
            f.write(text)

    def count(self):
        r = subprocess.run(["git", "-C", self.repo, "rev-list", "--count", REF],
                           capture_output=True, text=True,
                           env=gitcommit.clean_env())
        return int(r.stdout) if r.returncode == 0 else 0

    def test_root_commit_then_skip_if_equal_then_child(self):
        head = _git(self.repo, "rev-parse", "HEAD").stdout
        self.assertIsNone(gitcommit.commit_blob_to_ref(self.repo, self.rel, REF, "pm: a"))
        self.assertEqual(self.count(), 1)
        self.assertEqual(_git(self.repo, "show", f"{REF}:tickets.jsonl").stdout, "one\n")
        self.assertEqual(_git(self.repo, "ls-tree", "--name-only", REF).stdout,
                         "tickets.jsonl\n")
        self.assertIsNone(gitcommit.commit_blob_to_ref(self.repo, self.rel, REF, "pm: b"))
        self.assertEqual(self.count(), 1)
        self.write("two\n")
        self.assertIsNone(gitcommit.commit_blob_to_ref(self.repo, self.rel, REF, "pm: c"))
        self.assertEqual(self.count(), 2)
        self.assertEqual(_git(self.repo, "log", "-1", "--format=%s", REF).stdout, "pm: c\n")
        self.assertEqual(_git(self.repo, "rev-parse", "HEAD").stdout, head)
        self.assertEqual(_git(self.repo, "diff", "--cached", "--name-only").stdout, "")

    def test_moved_ref_fails_update_ref_as_gitfault(self):
        self.assertIsNone(gitcommit.commit_blob_to_ref(self.repo, self.rel, REF, "pm: a"))
        self.write("two\n")
        real = gitcommit.git

        def racing(repo_dir, *argv, **kw):
            if argv[0] == "update-ref":
                other = _git(repo_dir, "commit-tree", "-m", "intruder",
                             _git(repo_dir, "rev-parse", f"{REF}^{{tree}}").stdout.strip()
                             ).stdout.strip()
                _git(repo_dir, "update-ref", REF, other)
                self.moved = other
            return real(repo_dir, *argv, **kw)

        with unittest.mock.patch.object(gitcommit, "git", racing):
            fault = gitcommit.commit_blob_to_ref(self.repo, self.rel, REF, "pm: b")
        self.assertIsInstance(fault, gitcommit.GitFault)
        self.assertEqual(_git(self.repo, "rev-parse", REF).stdout.strip(), self.moved)

    def _stub_gpg(self):
        path = os.path.join(self.base, "stub-gpg")
        with open(path, "w") as f:
            f.write(STUB_GPG)
        os.chmod(path, 0o755)
        _git(self.repo, "config", "gpg.program", path)
        return path + ".log"

    def test_gpgsign_true_passes_dash_S_to_commit_tree(self):
        log = self._stub_gpg()
        _git(self.repo, "config", "commit.gpgsign", "true")
        self.assertIsNone(gitcommit.commit_blob_to_ref(self.repo, self.rel, REF, "pm: s"))
        self.assertTrue(os.path.exists(log), "gpg.program was never invoked")
        self.assertIn("gpgsig", _git(self.repo, "cat-file", "commit", REF).stdout)

    def test_gpgsign_false_does_not_sign(self):
        log = self._stub_gpg()
        self.assertIsNone(gitcommit.commit_blob_to_ref(self.repo, self.rel, REF, "pm: u"))
        self.assertFalse(os.path.exists(log))
        self.assertNotIn("gpgsig", _git(self.repo, "cat-file", "commit", REF).stdout)

    def test_non_git_dir_is_a_no_op(self):
        plain = os.path.join(self.base, "plain")
        os.makedirs(plain)
        self.assertIsNone(gitcommit.commit_blob_to_ref(plain, self.rel, REF, "pm: x"))


class Proc:
    def __init__(self, returncode=1, stderr="", stdout=""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


IDENTITY_EPERM_TEXT = (
    "fatal: unable to access '/Users/matthias/.gitconfig': "
    "Operation not permitted\n")
SIGNING_TEXT = ("error: gpg failed to sign the data:\n"
                "gpg: signing failed: No secret key\n"
                "fatal: failed to write commit object\n")
OTHER_TEXT = "error: failed to push some refs\n"


class ClassifyTest(unittest.TestCase):
    def setUp(self):
        self.env_set = {"GIT_CONFIG_GLOBAL": "/tmp/does-not-matter-here"}

    def test_identity_eperm_text_classifies_identity_missing(self):
        cls, text = gitcommit.classify(Proc(stderr=IDENTITY_EPERM_TEXT), env=self.env_set)
        self.assertEqual(cls, "identity-missing")
        self.assertIn("Operation not permitted", text)

    def test_signing_text_classifies_signing(self):
        cls, _ = gitcommit.classify(Proc(stderr=SIGNING_TEXT), env=self.env_set)
        self.assertEqual(cls, "signing")

    def test_unrelated_failure_classifies_other(self):
        cls, _ = gitcommit.classify(Proc(stderr=OTHER_TEXT), env=self.env_set)
        self.assertEqual(cls, "other")

    def test_env_unset_wins_over_signing_looking_text(self):
        cls, _ = gitcommit.classify(Proc(stderr=SIGNING_TEXT), env={"CLAUDECODE": "1"})
        self.assertEqual(cls, "identity-missing")

    def test_env_present_but_empty_counts_as_missing(self):
        self.assertTrue(gitcommit.identity_env_missing(
            {"CLAUDECODE": "1", "GIT_CONFIG_GLOBAL": ""}))
        self.assertFalse(gitcommit.identity_env_missing(
            {"CLAUDECODE": "1", "GIT_CONFIG_GLOBAL": "/x"}))

    def test_codex_marker_counts_as_agent_session(self):
        self.assertTrue(gitcommit.identity_env_missing({"CODEX_AGENT_IDENTITY": "1"}))

    def test_operator_shell_unset_is_not_a_fault(self):
        self.assertFalse(gitcommit.identity_env_missing({}))
        cls, _ = gitcommit.classify(Proc(stderr=SIGNING_TEXT), env={})
        self.assertEqual(cls, "signing")
        cls, _ = gitcommit.classify(Proc(stderr=OTHER_TEXT), env={})
        self.assertEqual(cls, "other")

    def test_success_result_still_classifies_when_asked(self):
        cls, _ = gitcommit.classify(Proc(returncode=0, stdout="clean"), env=self.env_set)
        self.assertEqual(cls, "other")


class AnnounceGuardTest(unittest.TestCase):
    def test_announce_other_class_is_a_noop(self):
        buf = io.StringIO()
        with unittest.mock.patch("sys.stderr", buf):
            self.assertIsNone(gitcommit.announce("other"))
        self.assertEqual(buf.getvalue(), "")

    def test_announce_prints_remedy_to_stderr(self):
        buf = io.StringIO()
        with unittest.mock.patch("sys.stderr", buf):
            gitcommit.announce("identity-missing")
        self.assertIn("gitfault[identity-missing]:", buf.getvalue())
        self.assertIn(gitcommit.IDENTITY_PREFIX.strip(), buf.getvalue())

    def test_guard_env_announces_and_returns_true_when_unset(self):
        buf = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"CLAUDECODE": "1"}, clear=False):
            os.environ.pop("GIT_CONFIG_GLOBAL", None)
            with unittest.mock.patch("sys.stderr", buf):
                warned = gitcommit.guard_env()
        self.assertTrue(warned)
        self.assertIn("gitfault[identity-missing]:", buf.getvalue())

    def test_guard_env_silent_in_operator_shell(self):
        buf = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            for k in ("GIT_CONFIG_GLOBAL", "CLAUDECODE", "CODEX_AGENT_IDENTITY"):
                os.environ.pop(k, None)
            with unittest.mock.patch("sys.stderr", buf):
                warned = gitcommit.guard_env()
        self.assertFalse(warned)
        self.assertEqual(buf.getvalue(), "")

    def test_guard_env_silent_when_set(self):
        buf = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": "/x"}):
            with unittest.mock.patch("sys.stderr", buf):
                warned = gitcommit.guard_env()
        self.assertFalse(warned)
        self.assertEqual(buf.getvalue(), "")

    def test_on_failure_skips_duplicate_identity_line_when_already_warned(self):
        buf = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"CLAUDECODE": "1", "GIT_CONFIG_GLOBAL": ""}):
            with unittest.mock.patch("sys.stderr", buf):
                cls = gitcommit.on_failure(Proc(stderr=IDENTITY_EPERM_TEXT),
                                           already_warned=True)
        self.assertEqual(cls, "identity-missing")
        self.assertEqual(buf.getvalue(), "")

    def test_on_failure_announces_signing_even_if_identity_already_warned(self):
        buf = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": "/x"}):
            with unittest.mock.patch("sys.stderr", buf):
                cls = gitcommit.on_failure(Proc(stderr=SIGNING_TEXT), already_warned=True)
        self.assertEqual(cls, "signing")
        self.assertIn("gitfault[signing]:", buf.getvalue())

    def test_never_raises_on_a_broken_proc(self):
        cls = gitcommit.on_failure(types.SimpleNamespace())
        self.assertIn(cls, ("identity-missing", "other"))


class CommitStoreExtraPathsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        _scoped_env(self, {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"})
        self.repo = _mkrepo(os.path.join(os.path.realpath(self._tmp.name), "r"))
        self.root = os.path.join(self.repo, ".pm")
        os.makedirs(os.path.join(self.root, "archive"))
        for name, text in (("config.json", '{"spec_version": 2, "prefix": "tt"}\n'),
                           ("tickets.jsonl", "one\n"),
                           ("archive/archive-index.jsonl", "idx\n")):
            with open(os.path.join(self.root, name), "w") as f:
                f.write(text)
        _git(self.repo, "add", ".pm/config.json")
        _git(self.repo, "commit", "-q", "-m", "cfg")
        self.extra = ".pm/archive/archive-index.jsonl"

    def files(self):
        return _git(self.repo, "show", "--name-only", "--format=", "HEAD").stdout.split()

    def test_extra_path_rides_in_the_same_commit(self):
        self.assertIsNone(gitcommit.commit_store(self.root, "pm: x", extra_paths=[self.extra]))
        self.assertEqual(sorted(self.files()), [self.extra, ".pm/tickets.jsonl"])

    def test_default_commits_the_ticket_file_alone(self):
        self.assertIsNone(gitcommit.commit_store(self.root, "pm: x"))
        self.assertEqual(self.files(), [".pm/tickets.jsonl"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
