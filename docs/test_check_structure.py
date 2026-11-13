#!/usr/bin/env python3
"""Black-box tests for check_structure.py against a throwaway repository."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_structure.py"

ROOT_README = """# Fixture

## Behavioral contract

Text.

## Components

| Component | Purpose | Development instructions |
| --- | --- | --- |
| [Alpha](/alpha/README.md) | Example | [Alpha maintenance](/alpha/AGENTS.md) |
"""

CONTRIBUTING = """# Standards

## Exemptions

| Component | Rule | Reason |
| --- | --- | --- |
"""

AGENTS = """# Alpha maintenance

This component owns the alpha tool.

| Change | Read |
| --- | --- |
| Tool behavior | [Tests](/alpha/tests/test_a.py) |

Run the alpha checks from the repository root.

```sh
python3 -B alpha/tests/test_a.py
```
"""
COMMAND = "python3 -B alpha/tests/test_a.py"
COMMAND_LINE = 12
RUN_LINE = 9

ALPHA_README = "# Alpha\n\nSee [maintenance](/alpha/AGENTS.md).\n"


class CheckStructureTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Agents\n\nUse the [index](/README.md#components).\n")
        self.write("README.md", ROOT_README)
        self.write("docs/contributing.md", CONTRIBUTING)
        self.write("alpha/README.md", ALPHA_README)
        self.write("alpha/CLAUDE.md", "@AGENTS.md\n")
        self.write("alpha/AGENTS.md", AGENTS)
        self.write("alpha/tests/test_a.py", "")
        (self.root / "docs").mkdir(exist_ok=True)
        shutil.copy(SCRIPT, self.root / "docs" / "check_structure.py")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def replace(self, name, old, new):
        text = (self.root / name).read_text()
        self.assertIn(old, text)
        self.write(name, text.replace(old, new))

    def track(self):
        for args in (["init", "-q"], ["add", "--", "."]):
            subprocess.run(["git", "-C", str(self.root)] + args, check=True, capture_output=True)

    def check(self, *args, track=True):
        if track:
            self.track()
        return subprocess.run([sys.executable, "-B", str(self.root / "docs" / "check_structure.py")]
                              + list(args), capture_output=True, text=True)

    def assert_flags(self, expected, track=True):
        result = self.check(track=track)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout)
        return result.stdout

    def assert_passes(self, track=True):
        result = self.check(track=track)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def exempt(self, row):
        self.write("docs/contributing.md", CONTRIBUTING + row + "\n")

    def test_valid_fixture_passes(self):
        out = self.assert_passes()
        self.assertTrue(out.splitlines()[-1].startswith("check_structure: ok (1 components, 0 exempted)"))

    def test_violation_line_format(self):
        (self.root / "alpha/CLAUDE.md").unlink()
        self.replace("alpha/AGENTS.md", "# Alpha maintenance", "# Alpha")
        lines = self.assert_flags("A-TITLE").splitlines()
        self.assertEqual(lines[-1], "check_structure: 2 violations (1 components, 0 exempted)")
        for line in lines[:-1]:
            self.assertRegex(line, r"^\S+?(:\d+)?: [A-Z]-[A-Z-]+ .+$")

    def test_root_files(self):
        self.write("CLAUDE.md", "x\n")
        (self.root / "AGENTS.md").unlink()
        out = self.assert_flags("AGENTS.md: R-FILE missing required root file")
        self.assertIn("CLAUDE.md: R-CLAUDE", out)

    def test_index_table_missing(self):
        self.replace("README.md", "## Components", "## Parts")
        self.assert_flags("README.md: I-TABLE")

    def test_index_row_and_missing_directory(self):
        self.replace("README.md", "[Alpha maintenance](/alpha/AGENTS.md)", "[Alpha maintenance](/beta/AGENTS.md)")
        self.write("README.md", (self.root / "README.md").read_text()
                   + "| [Gamma](/gamma/README.md) | Gone | [Gamma maintenance](/gamma/AGENTS.md) |\n")
        out = self.assert_flags("README.md:11: I-ROW")
        self.assertIn("README.md:12: I-MISSING indexed component gamma/ does not exist", out)

    def test_unindexed_tracked_directory(self):
        self.write("beta/x.txt", "x\n")
        self.assert_flags("beta/: I-UNINDEXED")

    def test_untracked_ignored_and_excluded_directories_pass(self):
        self.write(".gitignore", "rem/\n")
        self.write("rem/x.txt", "x\n")
        self.write(".hidden/x", "x\n")
        self.write("docs/x.md", "# X\n")
        self.track()
        self.write("pm/x.txt", "x\n")
        self.assert_passes(track=False)

    def test_component_claude_shim(self):
        self.write("alpha/CLAUDE.md", "@README.md\n")
        self.assert_flags("alpha/CLAUDE.md: C-CLAUDE")
        (self.root / "alpha/CLAUDE.md").unlink()
        self.assert_flags("alpha/CLAUDE.md: C-CLAUDE")

    def test_component_readme_missing(self):
        (self.root / "alpha/README.md").unlink()
        self.assert_flags("alpha/README.md: C-README missing required component file")

    def test_install_required_only_with_integration(self):
        self.write("alpha/tools/t.py", "")
        self.assert_passes()
        self.write("alpha/skills/s/SKILL.md", "# S\n")
        self.assert_flags("alpha/INSTALL.md: C-INSTALL missing; required because alpha/skills/ exists")

    def test_readme_routes(self):
        self.write("alpha/INSTALL.md", "# Setup\n")
        self.assert_flags("alpha/README.md: C-README-ROUTE does not link /alpha/INSTALL.md")
        self.write("alpha/README.md", "# Alpha\n\nSee [setup](/alpha/INSTALL.md).\n")
        self.assert_flags("alpha/README.md: C-README-ROUTE does not link /alpha/AGENTS.md")

    def test_agents_title(self):
        self.replace("alpha/AGENTS.md", "# Alpha maintenance", "# Alpha")
        self.replace("alpha/AGENTS.md", "owns", "has")
        out = self.assert_flags("alpha/AGENTS.md:1: A-TITLE")
        self.assertEqual(len(out.splitlines()), 2)

    def test_agents_route_table(self):
        row = "| Tool behavior | [Tests](/alpha/tests/test_a.py) |"
        failing = (
            ("| Change | Read |", "| Change | See |"),
            ("| Change | Read |\n| --- | --- |\n" + row,
             "| Change | Read | Why |\n| --- | --- | --- |\n" + row + " x |"),
            (row, "| Tool behavior | |"),
        )
        for old, new in failing:
            with self.subTest(new=new):
                self.write("alpha/AGENTS.md", AGENTS.replace(old, new))
                self.assert_flags("alpha/AGENTS.md:5: A-TABLE")
        self.write("alpha/AGENTS.md", AGENTS.replace("| Change | Read |", "| Work | Read |"))
        self.assert_passes()

    def test_run_paragraph_may_span_lines(self):
        self.replace("alpha/AGENTS.md", "Run the alpha checks from the repository root.",
                     "Run the alpha checks from the\nrepository root. `-k` narrows to\none test name.")
        self.assert_passes()
        self.replace("alpha/AGENTS.md", "Run the alpha checks", "Use the alpha checks")
        self.assert_flags("alpha/AGENTS.md:%d: A-RUN" % RUN_LINE)

    def test_agents_without_sh_fence(self):
        self.replace("alpha/AGENTS.md", "```sh\n" + COMMAND + "\n```\n", "")
        self.assert_flags("alpha/AGENTS.md:1: A-RUN")

    def test_component_directory_run_line_flags_only_cwd(self):
        self.replace("alpha/AGENTS.md", "from the repository root", "from this component directory")
        self.replace("alpha/AGENTS.md", COMMAND, "python3 -B tests/test_a.py")
        out = self.assert_flags("alpha/AGENTS.md:%d: A-CWD" % RUN_LINE)
        self.assertNotIn("A-TARGET", out)
        self.assertEqual(len(out.splitlines()), 2)

    def test_validation_targets(self):
        failing = (
            "python3 -B alpha/tests/missing.py",
            "python3 -B -m unittest discover -s alpha/nope",
            "python3 -B -m unittest discover -s alpha/tests -p x_*.py",
            "node x.js",
        )
        for command in failing:
            with self.subTest(command=command):
                self.write("alpha/AGENTS.md", AGENTS.replace(COMMAND, command))
                self.assert_flags("alpha/AGENTS.md:%d: A-TARGET" % COMMAND_LINE)
        passing = (
            "python3 -B -W error::ResourceWarning -m unittest discover -s alpha/tests",
            "/usr/bin/python3 -B alpha/tests/test_a.py --cli alpha/nope",
        )
        for command in passing:
            with self.subTest(command=command):
                self.write("alpha/AGENTS.md", AGENTS.replace(COMMAND, command))
                self.assert_passes()

    def test_only_first_sh_fence_is_checked(self):
        self.write("alpha/AGENTS.md", AGENTS + "\n```sh\npython3 -B /elsewhere/missing.py\n```\n")
        self.assert_passes()

    def test_links(self):
        failing = (
            ("[a](AGENTS.md)", "L-ROOT", '"/alpha/AGENTS.md"'),
            ("[a](/alpha/nope.md)", "L-TARGET", "does not exist"),
            ("[a](/../x.md)", "L-TARGET", "outside the repository"),
            ("[a](/README.md#nope)", "L-ANCHOR", 'no heading for "#nope" in README.md'),
            ("[a](#nope)", "L-ANCHOR", "alpha/README.md"),
        )
        for link, rule, detail in failing:
            with self.subTest(link=link):
                self.write("alpha/README.md", ALPHA_README + "\n" + link + "\n")
                lines = self.assert_flags("alpha/README.md:5: " + rule).splitlines()
                self.assertEqual(len(lines), 2)
                self.assertIn(detail, lines[0])
        passing = (
            "[a](/README.md#behavioral-contract)",
            "## Notes\n\n## Notes\n\n[a](#notes-1)",
            "```text\n[a](/alpha/nope.md)\n```",
            "Write `[a](/alpha/nope.md)` by hand.",
        )
        for body in passing:
            with self.subTest(body=body):
                self.write("alpha/README.md", ALPHA_README + "\n" + body + "\n")
                self.assert_passes()

    def test_exemption_applies_and_goes_stale(self):
        self.exempt("| `alpha` | `A-TITLE` | The fixture keeps the old title. |")
        self.assert_flags("docs/contributing.md:7: X-STALE exemption alpha A-TITLE matches no violation")
        self.replace("alpha/AGENTS.md", "# Alpha maintenance", "# Alpha")
        self.assertIn("(1 components, 1 exempted)", self.assert_passes())

    def test_exemption_row_errors(self):
        rows = (
            ("| alpha | Z-NO | reason |", 'unknown rule "Z-NO"'),
            ("| alpha | R-FILE | reason |", 'rule "R-FILE" cannot be exempted'),
            ("| zeta | A-TABLE | reason |", 'unknown component "zeta"'),
            ("| alpha | A-TABLE | |", "reason is empty"),
        )
        for row, detail in rows:
            with self.subTest(row=row):
                self.exempt(row)
                self.assert_flags("docs/contributing.md:7: X-ROW exemption row: " + detail)

    def test_usage_and_non_git_root(self):
        result = self.check(track=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a git work tree", result.stderr)
        result = self.check("extra")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
