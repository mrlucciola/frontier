"""Byte ceilings of the design's "Size budgets", measured on the real CLI.

    /usr/bin/python3 -B -m unittest discover -s pm/tests -v
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(os.path.dirname(HERE), "cli", "pm")
DESIGN = os.path.join(os.path.dirname(HERE), "docs", "design.md")

CEILINGS = {"help": 1600, "help verb": 700, "refusal": 300,
            "orient": 700, "session-start": 760}

TITLES = [
    "scanner misreads tabs inside string literals",
    "retry loop never backs off after a timeout",
    "export drops trailing newline in csv output",
    "cache key ignores the locale setting",
    "parser accepts duplicate headers silently",
    "upload stalls when the socket half closes",
    "migration leaves orphaned index rows behind",
    "dashboard counts archived rows as active",
    "token refresh races with logout handler",
    "build script hardcodes an absolute path",
    "search ranks stale entries above fresh ones",
    "config reload skips nested overrides",
    "webhook signature check uses wrong encoding",
]


def environment(tmp):
    return {
        "PM_NOW": "2026-01-01T00:00:00Z", "PM_ACTOR": "ada", "PM_SESSION_ID": "s1",
        "LC_ALL": "C", "HOME": os.path.join(tmp, "home"),
        "PATH": "/usr/bin:/bin", "PM_STORES": os.path.join(tmp, "stores"),
        "PM_PLUGINS": os.path.join(tmp, "plugins"), "TMPDIR": tmp,
        "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
    }


def help_verbs():
    with open(os.path.join(HERE, "t", "17-help.t")) as f:
        text = f.read()
    table = text.split("$ pm help\n", 1)[1].split("\n\n", 2)[1]
    return [line.split()[0] for line in table.splitlines() if line.strip()]


class Budgets(unittest.TestCase):
    sizes = []

    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.realpath(tempfile.mkdtemp(prefix="pm-b-"))
        for name in ("work", "home", "plugins", "bare"):
            os.mkdir(os.path.join(cls.tmp, name))
        cls.env = environment(cls.tmp)
        cls.work = os.path.join(cls.tmp, "work")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)
        print("\nmeasured sizes (bytes):")
        for line in cls.sizes:
            print("  " + line)

    def pm(self, *args, cwd=None, as_name=None, session="s1"):
        cwd = cwd or self.work
        env = dict(self.env, PM_SESSION_ID=session, PM_STORES=cwd + ".stores")
        if as_name:
            env["PM_ACTOR"] = as_name
        done = subprocess.run(["/usr/bin/python3", "-B", CLI] + list(args),
                              cwd=cwd or self.work, env=env, capture_output=True,
                              text=True, timeout=60)
        return done

    def check(self, label, text, ceiling):
        size = len(text.encode())
        Budgets.sizes.append("%-44s %4d / %d" % (label, size, ceiling))
        self.assertLessEqual(
            size, ceiling, "%s printed %d bytes, ceiling %d:\n%s"
            % (label, size, ceiling, text))

    def start(self, prefix="t"):
        self.assertEqual(self.pm("init", prefix).returncode, 0)

    def test_design_table_matches(self):
        with open(DESIGN) as f:
            text = f.read()
        section = text.split("### Size budgets", 1)[1].split("\n## ", 1)[0]
        found = [int(n) for n in re.findall(r"^\| .* \| (\d+) \|$", section, re.M)]
        self.assertEqual(found, [1600, 700, 300, 700, 760])

    def test_help(self):
        done = self.pm("help")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.check("pm help", done.stdout + done.stderr, CEILINGS["help"])

    def test_help_verbs(self):
        verbs = help_verbs()
        self.assertGreaterEqual(len(verbs), 20)
        for verb in verbs:
            done = self.pm("help", verb)
            self.assertEqual(done.returncode, 0, "pm help %s: %s" % (verb, done.stderr))
            self.check("pm help %s" % verb, done.stdout + done.stderr,
                       CEILINGS["help verb"])

    def test_refusals(self):
        work = os.path.join(self.tmp, "r")
        os.mkdir(work)
        self.start_in(work)
        for title in ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot"):
            self.assertEqual(self.pm("new", title + " " + title[::-1] + "x", cwd=work).returncode, 0)
        setup = [
            (("link", "t-2", "blocks", "t-3"), "s1"),
            (("take", "t-4", "--as", "bob"), "s2"),
            (("take", "t-5"), "s1"),
            (("done", "t-5", "--findings", "none", "-m", "checked"), "s1"),
            (("take", "t-1"), "s1"),
            (("new", "parent of work", "--epic"), "s1"),
            (("new", "child one of it", "--under", "t-7"), "s1"),
        ]
        for args, session in setup:
            done = self.pm(*args, cwd=work, session=session)
            self.assertEqual(done.returncode, 0,
                             "setup pm %s: %s" % (" ".join(args), done.stderr))

        commands = [
            ("take", "t-3"),
            ("take", "t-4"),
            ("take", "t-9"),
            ("link", "t-3", "blocks", "t-2"),
            ("unlink", "t-1", "t-6"),
            ("new",),
            ("init", "T1"),
            ("init", "t"),
            ("init", "x"),
            ("note", "-k", "verdict", "x"),
            ("edit", "t-1"),
            ("park",),
            ("park", "t-2", "-m", "x"),
            ("reopen", "t-2"),
            ("hold", "t-2", "-m", "x"),
            ("drop", "t-2"),
            ("drop", "t-4"),
            ("done", "t-5"),
            ("done", "t-4", "--findings", "none", "-m", "x"),
            ("done", "t-7"),
            ("show", "t-9"),
            ("new", "child two of it", "--under", "t-2"),
            ("clam",),
            ("xyzzy",),
        ]
        refused = 0
        for args in commands:
            done = self.pm(*args, cwd=work)
            if done.returncode == 0 or not done.stderr.startswith("pm: "):
                continue
            refused += 1
            self.check("refusal: pm %s" % " ".join(args), done.stderr,
                       CEILINGS["refusal"])
        done = self.pm("new", "too early", cwd=os.path.join(self.tmp, "bare"))
        self.assertNotEqual(done.returncode, 0)
        self.check("refusal: pm new (no store)", done.stderr, CEILINGS["refusal"])
        self.assertGreaterEqual(refused + 1, 10,
                                "only %d of the refusal commands refused" % refused)

    def start_in(self, work, prefix="t"):
        done = self.pm("init", prefix, cwd=work)
        self.assertEqual(done.returncode, 0, done.stderr)

    def busy_store(self):
        work = os.path.join(self.tmp, "busy")
        os.mkdir(work)
        self.start_in(work)
        for title in TITLES:
            done = self.pm("new", title, cwd=work)
            self.assertEqual(done.returncode, 0, done.stderr)
        for n in (3, 4, 5):
            self.assertEqual(self.pm("take", "t-%d" % n, cwd=work).returncode, 0)
            done = self.pm("park", "t-%d" % n, "-m", "waits on the release", cwd=work)
            self.assertEqual(done.returncode, 0, done.stderr)
        for n in (1, 2):
            self.assertEqual(self.pm("take", "t-%d" % n, cwd=work).returncode, 0)
        return work

    def test_orient_and_session_start(self):
        work = self.busy_store()
        done = self.pm(cwd=work)
        self.assertEqual(done.returncode, 0, done.stderr)
        for word in ("yours:", "ready:", "parked:"):
            self.assertIn(word, done.stdout)
        self.check("pm (2 held, 8 ready, 3 parked)", done.stdout + done.stderr,
                   CEILINGS["orient"])
        done = self.pm("hook", "session-start", cwd=work)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.check("pm hook session-start (same store)", done.stdout + done.stderr,
                   CEILINGS["session-start"])


if __name__ == "__main__":
    unittest.main()
