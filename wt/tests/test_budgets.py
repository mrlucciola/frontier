"""Byte ceilings for what wt prints to teach: help, one verb's help, a failure line.

    /usr/bin/python3 -B -m unittest discover -s wt/tests -p 'test_budgets.py' -v

Help and the usage failures are measured on the real CLI. Failure lines that need a
broken repository are measured from the message templates in tools/: each `$name`,
`${...}` and `$(...)` is replaced by NOMINAL bytes, a fault-report path is added where
wt_fail adds one, and the result must stay under the ceiling.
"""
import glob
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
COMPONENT = os.path.dirname(HERE)
CLI = os.path.join(COMPONENT, "cli", "wt")

CEILINGS = {"help": 1200, "help verb": 700, "failure": 400}
NOMINAL = 24
FAULT_PATH = 90


def run(*args, cwd=None):
    env = {"PATH": "/usr/bin:/bin", "HOME": cwd or "/", "LC_ALL": "C",
           "WT_FAULT_REPORT_DIR": os.path.join(cwd or "/", "faults")}
    return subprocess.run([CLI] + list(args), capture_output=True, text=True, cwd=cwd,
                          env=env, timeout=60)


def quoted(stmt):
    out, i = [], 0
    while i < len(stmt):
        if stmt[i] != '"':
            i += 1
            continue
        j, buf = i + 1, []
        while j < len(stmt) and stmt[j] != '"':
            if stmt[j] == "\\" and j + 1 < len(stmt):
                buf.append(stmt[j + 1])
                j += 2
            else:
                buf.append(stmt[j])
                j += 1
        out.append("".join(buf))
        i = j + 1
    return out


def expand(text):
    text = re.sub(r"\$\([^)]*\)", "x" * NOMINAL, text)
    text = re.sub(r"\$\{[^}]*\}", "x" * NOMINAL, text)
    return re.sub(r"\$[A-Za-z_][A-Za-z_0-9]*", "x" * NOMINAL, text)


def templates():
    """(file, line text) for every wt_say and wt_fail call in tools/."""
    found = []
    for path in sorted(glob.glob(COMPONENT + "/tools/**/*.zsh", recursive=True)):
        with open(path) as f:
            text = f.read().replace("\\\n", " ")
        for m in re.finditer(r"^[ \t]*(?:[^\n#]*?\b)?(wt_say|wt_fail)\b([^\n]*)", text, re.M):
            call, rest = m.groups()
            parts = quoted(rest)
            if not parts:
                continue
            if call == "wt_say":
                msg = "wt: " + expand(parts[0])
            else:
                msg = expand(parts[0]) + (" " + expand(parts[1]) if len(parts) > 1 else "")
                if rest.split()[:1] == ["infra"]:
                    msg += (". Recorded in " + "x" * FAULT_PATH + ". This is infrastructure, "
                            "not a finding: file no ticket and write no retro.")
                else:
                    msg += " (reported: " + "x" * FAULT_PATH + ")"
                msg = "wt: " + msg
            found.append((os.path.relpath(path, COMPONENT), msg))
    return found


class Budgets(unittest.TestCase):
    sizes = []

    @classmethod
    def tearDownClass(cls):
        print("\nmeasured sizes (bytes):")
        for line in cls.sizes:
            print("  " + line)

    def check(self, label, text, ceiling):
        size = len(text.encode())
        Budgets.sizes.append("%-52s %4d / %d" % (label, size, ceiling))
        self.assertLessEqual(size, ceiling,
                             "%s is %d bytes, ceiling %d:\n%s" % (label, size, ceiling, text))

    def verbs(self):
        done = run("help")
        self.assertEqual(done.returncode, 0, done.stderr)
        return [l.split()[0] for l in done.stdout.splitlines() if l.startswith("  ")]

    def test_help(self):
        done = run("help")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.check("wt help", done.stdout + done.stderr, CEILINGS["help"])

    def test_help_verbs(self):
        verbs = self.verbs()
        self.assertGreaterEqual(len(verbs), 7)
        for verb in verbs:
            done = run("help", verb)
            self.assertEqual(done.returncode, 0, "wt help %s: %s" % (verb, done.stderr))
            self.assertTrue(done.stdout.startswith("wt ") or verb == "land", done.stdout)
            self.check("wt help %s" % verb, done.stdout + done.stderr, CEILINGS["help verb"])

    def test_every_verb_has_a_file(self):
        for verb in self.verbs():
            name = "finish" if verb == "land" else verb
            self.assertTrue(os.path.isfile(
                os.path.join(COMPONENT, "tools", "verbs", name + ".zsh")), verb)

    def test_usage_failures(self):
        with tempfile.TemporaryDirectory(prefix="wt-b-") as tmp:
            tmp = os.path.realpath(tmp)
            cases = [(), ("bogus",), ("pending",), ("help", "bogus"), ("help", "pending"),
                     ("start",), ("start", "a", "b"), ("start", "--bogus"),
                     ("start", "a", "--as"), ("finish",), ("finish", "a", "b"),
                     ("finish", "--bogus"), ("land", "--bogus"), ("park",),
                     ("park", "a", "b"), ("park", "--bogus"), ("status", "x"),
                     ("prune", "x"), ("start", "tk-1", "--as", "a"),
                     ("finish", "tk-1"), ("park", "tk-1"), ("status",), ("prune",)]
            lines = 0
            for args in cases:
                done = run(*args, cwd=tmp)
                for line in done.stderr.splitlines():
                    if line.startswith("wt: "):
                        lines += 1
                        self.check("failure: wt %s" % " ".join(args), line,
                                   CEILINGS["failure"])
            self.assertGreaterEqual(lines, 15)

    def test_failure_templates(self):
        found = templates()
        self.assertGreaterEqual(len(found), 50)
        for path, msg in found:
            self.assertLessEqual(
                len(msg.encode()), CEILINGS["failure"],
                "%s: %d bytes with %d-byte values, ceiling %d:\n%s"
                % (path, len(msg.encode()), NOMINAL, CEILINGS["failure"], msg))
        Budgets.sizes.append("%-52s %4d / %d" % (
            "failure templates (%d), longest" % len(found),
            max(len(m.encode()) for _, m in found), CEILINGS["failure"]))


if __name__ == "__main__":
    unittest.main()
