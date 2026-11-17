"""Byte ceilings on the text an agent carries on every step: the skill catalog and the instruction block.

The harness lists every skill's name and description each step, and the block sits in the
global instructions, so both are a fixed cost whether or not CWF is used. Raising a ceiling is
allowed; do it in the same change that grows the text, with the measured bytes in the commit.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_CEILING = 544
BLOCK_CEILING = 762


def catalog_bytes():
    total = 0
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        head = skill.read_text().split("---")[1]
        name = re.search(r"(?m)^name:\s*(.+)$", head).group(1).strip()
        description = re.search(r"(?m)^description:\s*(.+)$", head).group(1).strip().strip('"')
        total += len(name.encode()) + len(description.encode())
    return total


class BudgetTests(unittest.TestCase):
    def test_skill_catalog_within_ceiling(self):
        size = catalog_bytes()
        self.assertLessEqual(size, CATALOG_CEILING,
                             "skill names and descriptions are %d bytes, ceiling %d: shorten them, or raise "
                             "CATALOG_CEILING in cwf/tests/test_budgets.py with the measured cost" % (size, CATALOG_CEILING))

    def test_instruction_block_within_ceiling(self):
        size = len((ROOT / "instructions/opencode.AGENTS.md").read_bytes())
        self.assertLessEqual(size, BLOCK_CEILING,
                             "instructions/opencode.AGENTS.md is %d bytes, ceiling %d: shorten it, or raise "
                             "BLOCK_CEILING in cwf/tests/test_budgets.py with the measured cost" % (size, BLOCK_CEILING))


if __name__ == "__main__":
    unittest.main(verbosity=2)
