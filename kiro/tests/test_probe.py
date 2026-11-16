import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # kiro/
PROBE = ROOT / "cli" / "kiro-probe"
STATUSES = ("PASS", "FAIL", "SKIP", "INFO")


def stub(tmp, body):
    d = Path(tempfile.mkdtemp(dir=str(tmp)))
    exe = d / "kiro-cli"
    exe.write_text("#!/bin/sh\n%s\n" % body)
    exe.chmod(0o755)
    return str(d)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.home = self.tmp / "home"
        self.home.mkdir()

    def run_probe(self, stub_path, *args):
        env = {**os.environ, "HOME": str(self.home),
               "PATH": stub_path + os.pathsep + "/bin:/usr/bin"}
        return subprocess.run([sys.executable, str(PROBE), *args],
                              capture_output=True, text=True, env=env)

    def check_grammar(self, rc, stdout):
        lines = stdout.splitlines()
        self.assertLessEqual(len(lines), 40)
        self.assertEqual(lines[-1], "PROBE-END")
        for line in lines[:-1]:
            tokens = line.split()
            self.assertIn(tokens[0], STATUSES, line)
            self.assertGreaterEqual(len(tokens), 3, line)
        self.assertEqual(1 if any(l.startswith("FAIL ") for l in lines) else 0, rc)

    def test_default_mode_v2_grammar_and_findings(self):
        (self.home / ".kiro").mkdir()
        (self.home / ".kiro" / "settings.json").write_text("{}\n")
        (self.home / ".kiro" / "agents").mkdir()
        rc = self.run_probe(stub(self.tmp, 'echo "kiro-cli 2.17.0"'))
        self.check_grammar(rc.returncode, rc.stdout)
        self.assertEqual(rc.returncode, 0)
        out = rc.stdout
        self.assertIn("PASS kiro-version 2.17.0", out)
        self.assertIn("INFO symlink-fs", out)
        self.assertIn("~/.kiro/settings.json", out)
        self.assertIn("~/.kiro/agents/", out)
    def test_v3_stub_fails_version(self):
        rc = self.run_probe(stub(self.tmp, 'echo "kiro-cli 3.0.0"'))
        self.check_grammar(rc.returncode, rc.stdout)
        self.assertEqual(rc.returncode, 1)
        self.assertIn("FAIL kiro-version 3.0.0", rc.stdout)

    def test_absent_kiro_skips_and_exits_zero(self):
        empty = Path(tempfile.mkdtemp(dir=str(self.tmp)))  # no kiro-cli
        rc = self.run_probe(str(empty))
        self.check_grammar(rc.returncode, rc.stdout)
        self.assertEqual(rc.returncode, 0)
        self.assertIn("SKIP kiro-present", rc.stdout)
        self.assertNotIn("FAIL kiro-version", rc.stdout)

    def test_smoke_passes_with_echoing_stub(self):
        body = ('if [ "$1" = chat ]; then echo "answer: FRONTIER-PING-7412"; '
                'else echo "kiro-cli 2.17.0"; fi')
        rc = self.run_probe(stub(self.tmp, body), "--smoke")
        self.check_grammar(rc.returncode, rc.stdout)
        self.assertEqual(rc.returncode, 0)
        self.assertIn("PASS smoke-token", rc.stdout)

    def test_smoke_fails_without_token(self):
        body = 'if [ "$1" = chat ]; then echo "I decline"; else echo "kiro-cli 2.17.0"; fi'
        rc = self.run_probe(stub(self.tmp, body), "--smoke")
        self.check_grammar(rc.returncode, rc.stdout)
        self.assertEqual(rc.returncode, 1)
        self.assertIn("FAIL smoke-token", rc.stdout)

    def test_smoke_skips_without_kiro(self):
        empty = Path(tempfile.mkdtemp(dir=str(self.tmp)))
        rc = self.run_probe(str(empty), "--smoke")
        self.assertEqual(rc.returncode, 0)
        self.assertIn("SKIP smoke-token", rc.stdout)

    def test_unknown_flag_exits_two(self):
        rc = self.run_probe(stub(self.tmp, 'echo "kiro-cli 2.17.0"'), "--bogus")
        self.assertEqual(rc.returncode, 2)
        self.assertEqual(rc.stdout, "")
        self.assertEqual(len(rc.stderr.strip().splitlines()), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
