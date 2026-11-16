import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # kiro/
DEPLOY = ROOT / "deploy.sh"
ZSH = shutil.which("zsh") or "/bin/zsh"
SNIPPET = (ROOT / "instructions" / "kiro.steering.md").read_text()
BEGIN, END = "<!-- KIRO:BEGIN -->", "<!-- KIRO:END -->"
OTHER = b"# My steering\nkeep this\n"


def stub_dir(tmp, body):
    d = Path(tempfile.mkdtemp(dir=str(tmp)))
    exe = d / "kiro-cli"
    exe.write_text("#!/bin/sh\n%s\n" % body)
    exe.chmod(0o755)
    return d


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.steering = self.home / ".kiro/steering/frontier.md"

    def deploy(self, path):
        return subprocess.run([ZSH, str(DEPLOY)], capture_output=True, text=True,
                              env={**os.environ, "HOME": str(self.home), "PATH": path})

    def snapshot(self):
        state = []
        for p in sorted(self.home.rglob("*")):
            if p.is_symlink():
                state.append((str(p.relative_to(self.home)), os.readlink(str(p))))
            elif p.is_file():
                state.append((str(p.relative_to(self.home)), p.read_bytes()))
        return state

    def test_v2_double_run_and_markers(self):
        self.steering.parent.mkdir(parents=True)
        self.steering.write_bytes(OTHER)
        path = str(stub_dir(self.tmp, 'echo "kiro-cli 2.17.0"')) + os.pathsep + os.environ["PATH"]
        first = self.deploy(path)
        self.assertEqual(first.returncode, 0, first.stderr)
        snap = self.snapshot()
        data = self.steering.read_bytes()
        self.assertTrue(data.startswith(OTHER))
        self.assertEqual(data.count(BEGIN.encode()), 1)
        self.assertEqual(data.count(END.encode()), 1)
        self.assertIn(SNIPPET.strip(), data.decode())
        link = self.home / ".local/bin/kiro-probe"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(str(link)), str(ROOT / "cli/kiro-probe"))
        second = self.deploy(path)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.snapshot(), snap)

    def test_text_outside_markers_survives_edit_then_rerun(self):
        path = str(stub_dir(self.tmp, 'echo "kiro-cli 2.17.0"')) + os.pathsep + os.environ["PATH"]
        self.assertEqual(self.deploy(path).returncode, 0)
        body = self.steering.read_bytes()
        self.steering.write_bytes(b"before\n" + body + b"after\n\n")
        self.assertEqual(self.deploy(path).returncode, 0)
        data = self.steering.read_bytes()
        self.assertTrue(data.startswith(b"before\n"))
        self.assertTrue(data.endswith(b"after\n\n"))
        self.assertEqual(data.count(BEGIN.encode()), 1)

    def test_v3_refused_before_any_write(self):
        path = str(stub_dir(self.tmp, 'echo "kiro-cli 3.0.0"')) + os.pathsep + os.environ["PATH"]
        rc = self.deploy(path)
        self.assertEqual(rc.returncode, 1)
        self.assertIn("3.0.0", rc.stderr)
        self.assertEqual(self.snapshot(), [])

    def test_missing_kiro_cli_refused_before_any_write(self):
        empty = Path(tempfile.mkdtemp(dir=str(self.tmp)))  # no kiro-cli here
        rc = self.deploy(str(empty))
        self.assertEqual(rc.returncode, 1)
        self.assertIn("kiro-cli --version", rc.stderr)
        self.assertEqual(self.snapshot(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
