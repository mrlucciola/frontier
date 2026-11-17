import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- CWF:BEGIN -->", "<!-- CWF:END -->"
OTHER = b"# My rules\n\nKeep this.\n\n\n"


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.steering = self.home / ".kiro/steering/frontier.md"
        self.steering.parent.mkdir(parents=True)
        self.steering.write_bytes(OTHER)

    def deploy(self):
        subprocess.run(["zsh", str(ROOT / "deploy.sh")], check=True,
                       env={**os.environ, "HOME": str(self.home)}, capture_output=True)

    def snapshot(self):
        links = sorted(p for p in self.home.rglob("*") if p.is_symlink())
        return self.steering.read_bytes(), [(p, os.readlink(p)) for p in links]

    def test_links_block_and_idempotence(self):
        self.deploy()
        first = self.snapshot()
        skills = sorted((ROOT / "skills").glob("cwf-*"))
        self.assertEqual(len(skills), 6)
        for s in skills:
            link = self.home / ".kiro/skills" / s.name
            self.assertEqual(link.resolve(), s.resolve())
        self.assertEqual((self.home / ".local/bin/cwf").resolve(), (ROOT / "cwf.py").resolve())
        data = first[0]
        self.assertEqual(data.count(BEGIN.encode()), 1)
        self.assertEqual(data.count(END.encode()), 1)
        self.assertTrue(data.startswith(OTHER))
        snippet = (ROOT / "instructions/kiro.steering.md").read_text()
        self.assertIn(snippet.strip(), data.decode())
        self.deploy()
        self.assertEqual(self.snapshot(), first)

    def test_text_outside_markers_survives_a_rerun_after_edit(self):
        self.deploy()
        body = self.steering.read_bytes()
        self.steering.write_bytes(b"before\n" + body + b"after\n\n")
        self.deploy()
        data = self.steering.read_bytes()
        self.assertTrue(data.startswith(b"before\n"))
        self.assertTrue(data.endswith(b"after\n\n"))
        self.assertEqual(data.count(BEGIN.encode()), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
