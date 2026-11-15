"""Run the OpenCode setup and removal commands from INSTALL.md in a disposable home.

The commands are read from INSTALL.md itself, so this checks the guide as written: a
fresh link, a repeated run that changes nothing, a foreign entry left alone, removal of
only this setup's links, and the no-agent verification step. bash and the standard
library only. Run: python3 -B icm/tests/test_opencode_setup.py
"""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

COMPONENT = Path(__file__).resolve().parent.parent
REPO = COMPONENT.parent
GUIDE = (COMPONENT / "INSTALL.md").read_text()
SKILLS = ("icm-architect", "icm-run")


def block(heading):
    """The sh fence(s) under one '### <heading>' of the OpenCode section, joined."""
    section = GUIDE.split("\n## OpenCode\n", 1)[1].split("\n## ", 1)[0]
    part = section.split(f"\n### {heading}\n", 1)[1].split("\n### ", 1)[0]
    fences = re.findall(r"```sh\n(.*?)```", part, re.S)
    assert fences, heading
    return fences


def tree(path: Path):
    return sorted((str(p.relative_to(path)), os.readlink(p) if p.is_symlink() else p.is_dir())
                  for p in path.rglob("*")) if path.exists() else []


class OpenCodeSetup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        (self.home / "projects").mkdir(parents=True)
        os.symlink(REPO, self.home / "projects/frontier-clean")
        self.dest = self.home / ".agents/skills"
        self.source_before = tree(COMPONENT / "skills")

    def tearDown(self):
        self.assertEqual(tree(COMPONENT / "skills"), self.source_before, "setup wrote into the component")
        self.tmp.cleanup()

    def sh(self, script, subst=None):
        for old, new in (subst or {}).items():
            script = script.replace(old, new)
        env = {"HOME": str(self.home), "PATH": os.environ["PATH"]}
        return subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)

    def links(self):
        return {n: os.readlink(self.dest / n) for n in SKILLS if (self.dest / n).is_symlink()}

    def expected(self):
        return {n: str(self.home / f"projects/frontier-clean/icm/skills/{n}") for n in SKILLS}

    def test_fresh_link_repeat_and_remove(self):
        (check,) = block("1. Check the destinations")
        (link,) = block("2. Link the skills")
        (remove,) = block("Disable and remove")
        self.assertEqual(self.sh(check).stderr.count("No such file or directory"), 2)
        r = self.sh(link)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.links(), self.expected())
        self.assertEqual(r.stdout.split(), list(self.expected().values()))
        self.assertTrue((self.dest / "icm-run/SKILL.md").is_file())
        (self.dest / "pm").mkdir()
        (self.dest / "pm/SKILL.md").write_text("user skill\n")
        before = tree(self.home / ".agents")
        r = self.sh(link)
        self.assertEqual(r.stdout.count("already present, left alone"), 2, r.stdout)
        self.assertEqual(tree(self.home / ".agents"), before)
        r = self.sh(remove)
        self.assertEqual(r.stderr.count("No such file or directory"), 2, r.stderr)
        self.assertEqual(self.links(), {})
        self.assertEqual((self.dest / "pm/SKILL.md").read_text(), "user skill\n")

    def test_foreign_entry_is_reported_and_kept(self):
        (check,) = block("1. Check the destinations")
        (link,) = block("2. Link the skills")
        (remove,) = block("Disable and remove")
        foreign = self.dest / "icm-run"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("someone else's icm-run\n")
        self.assertIn(str(foreign), self.sh(check).stdout)
        self.assertIn("left alone: ~/.agents/skills/icm-run", self.sh(link).stdout)
        self.assertEqual(sorted(p.name for p in foreign.iterdir()), ["SKILL.md"])
        self.assertEqual(self.links(), {"icm-architect": self.expected()["icm-architect"]})
        r = self.sh(remove)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((foreign / "SKILL.md").read_text(), "someone else's icm-run\n")
        self.assertFalse((self.dest / "icm-architect").exists())

    def test_verify_without_agent(self):
        (link,) = block("2. Link the skills")
        demo, _checks = block("4. Verify without an agent")
        self.sh(link)
        where = str(Path(self.tmp.name) / "icm-demo")
        r = self.sh(demo, {"/tmp/icm-demo": where})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("01-draft  unproduced", r.stdout)
        self.assertEqual(r.stdout.strip().splitlines()[-1], "next: run 01-draft")

    def test_named_checks_exist(self):
        _demo, checks = block("4. Verify without an agent")
        for path in re.findall(r"~/projects/frontier-clean/(\S+\.py)", checks):
            self.assertTrue((REPO / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
