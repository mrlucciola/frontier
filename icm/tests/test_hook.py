"""Run hooks/icm-detect.sh against fixture workspaces.

Checks: exit 0 always, silent outside an ICM workspace, valid JSON inside one,
CLAUDE.md preferred as the entry file, paths with quotes survive escaping, and
the settings fragment registers the hook at its path in this component.
Standard library only. Run: python3 -B icm/tests/test_hook.py
"""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks/icm-detect.sh"
FRAGMENT = ROOT / "config/settings.icm.fragment.json"

CASES = [
    # name, entries, expect_output, expected substrings
    ("both-entries", ["CONTEXT.md", "AGENTS.md", "CLAUDE.md", "stages/01-research/", "stages/02_script/"],
     True, ["Entry file: CLAUDE.md", "AGENTS.md also present"]),
    ("claude-only", ["CONTEXT.md", "CLAUDE.md", "stages/01-research/"], True, ["Entry file: CLAUDE.md"]),
    ("agents-only", ["CONTEXT.md", "AGENTS.md", "stages/01_research/"], True, ["Entry file: AGENTS.md"]),
    ("no-entry", ["CONTEXT.md", "stages/01-a/"], True, ["Entry file: none"]),
    ("stages-but-no-context", ["stages/01-a/"], False, []),
    ("context-but-unnumbered-stages", ["CONTEXT.md", "stages/research/"], False, []),
    ('quote "in" path', ["CONTEXT.md", "stages/01-a/"], True, ['quote \\"in\\" path']),
]


def build(base: pathlib.Path, entries):
    for e in entries:
        p = base / e
        if e.endswith("/"):
            p.mkdir(parents=True, exist_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x\n")


class HookTests(unittest.TestCase):
    def test_fixture_workspaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, entries, expect_output, needles in CASES:
                with self.subTest(name):
                    d = pathlib.Path(tmp) / name
                    build(d, entries)
                    r = subprocess.run(["bash", str(HOOK)], cwd=d, capture_output=True, text=True)
                    out = r.stdout.strip()
                    self.assertEqual(r.returncode, 0)
                    self.assertEqual(r.stderr.strip(), "")
                    if not expect_output:
                        self.assertEqual(out, "")
                        continue
                    doc = json.loads(out)
                    self.assertEqual(doc["hookSpecificOutput"]["hookEventName"], "SessionStart")
                    for n in needles:
                        self.assertIn(n, out)

    def test_fragment_registers_the_hook_in_this_component(self):
        frag = json.loads(FRAGMENT.read_text())
        cmds = [h["command"] for grp in frag["hooks"]["SessionStart"] for h in grp["hooks"]]
        self.assertEqual(cmds, ['"$HOME/projects/frontier-clean/icm/hooks/icm-detect.sh"'])
        self.assertTrue(os.access(HOOK, os.X_OK), "the fragment runs the hook directly")


if __name__ == "__main__":
    unittest.main()
