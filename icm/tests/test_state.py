"""Black-box checks of icm-run's state.py and record.py against fixture workspaces.

Each case builds a workspace in a temporary directory, runs the real scripts and reads
their output and exit status. Standard library only. Run: python3 -B icm/tests/test_state.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills/icm-run/scripts"

STAGE_A = """# 01-draft - write the draft

## Inputs
- Reference (every run): `../../_shared/rules.md`

## Process
1. Write the draft.

## Outputs
- `draft.md` -> `output/`

## Check
A person reads the draft.
"""

STAGE_B = """# 02-edit - edit the draft

## Inputs
- Working (this run): `../01-draft/output/`

## Process
1. Edit it.

## Outputs
- `{slug}-final.md` -> `output/`

## Check
{check}
"""


def run(script, *args, cwd=None):
    p = subprocess.run([sys.executable, "-B", str(SCRIPTS / script), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def tree_digest(root: Path):
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        h.update(str(p.relative_to(root)).encode())
        if p.is_file() and not p.is_symlink():
            h.update(p.read_bytes())
    return h.hexdigest()


class Workspace:
    def __init__(self, base: Path, check_b="A person reads it.", entry=True):
        self.root = base
        (base / "stages/01-draft/output").mkdir(parents=True)
        (base / "stages/02-edit/output").mkdir(parents=True)
        (base / "_shared").mkdir()
        (base / "_shared/rules.md").write_text("Be brief.\n")
        (base / "CONTEXT.md").write_text("# Pipeline\n\n01-draft then 02-edit.\n")
        if entry:
            (base / "AGENTS.md").write_text("# Demo\n\nRoute: stages in order.\n")
        (base / "stages/01-draft/CONTEXT.md").write_text(STAGE_A)
        (base / "stages/02-edit/CONTEXT.md").write_text(STAGE_B.replace("{check}", check_b))

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def state(self, where=None):
        code, out, err = run("state.py", str(where or self.root), "--json")
        doc = json.loads(out)
        doc["_code"] = code
        doc["by_stage"] = {r["stage"]: r for r in doc.get("stages", [])}
        return doc

    def record(self, stage, *args):
        return run("record.py", str(self.root), stage, *args)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def ws(self, **kw):
        return Workspace(self.base / "ws", **kw)

    def test_non_icm_directories(self):
        plain = self.base / "plain"
        plain.mkdir()
        code, out, _ = run("state.py", str(plain))
        self.assertEqual((code, out.strip()[:20]), (1, "not an ICM workspace"))
        unnumbered = self.base / "unnumbered"
        (unnumbered / "stages/research").mkdir(parents=True)
        (unnumbered / "CONTEXT.md").write_text("x\n")
        self.assertEqual(run("state.py", str(unnumbered))[0], 1)

    def test_fresh_workspace_runs_stage_one_only(self):
        w = self.ws()
        st = w.state()
        self.assertEqual(st["next"], "run 01-draft")
        self.assertTrue(st["by_stage"]["01-draft"]["may_run"])
        self.assertFalse(st["by_stage"]["02-edit"]["may_run"])
        self.assertEqual(st["by_stage"]["02-edit"]["waiting_on"], "01-draft")

    def test_dotfiles_check_only_and_partial_are_unproduced(self):
        w = self.ws()
        w.write("stages/01-draft/output/.gitkeep", "")
        w.write("stages/01-draft/output/check.md", "pass\n")
        self.assertEqual(w.state()["by_stage"]["01-draft"]["state"], "unproduced")
        w.write("stages/01-draft/output/notes.md", "other\n")
        row = w.state()["by_stage"]["01-draft"]
        self.assertEqual(row["state"], "unproduced")
        self.assertIn("draft.md missing", row["detail"][0])
        w.write("stages/01-draft/output/draft.md", "")
        self.assertIn("draft.md empty", w.state()["by_stage"]["01-draft"]["detail"][0])

    def test_produced_output_waits_for_human_review(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        st = w.state()
        self.assertEqual(st["by_stage"]["01-draft"]["state"], "pending")
        self.assertTrue(st["next"].startswith("review 01-draft (human check)"))
        self.assertFalse(any(r["may_run"] for r in st["stages"]))

    def test_unbound_pass_is_not_acceptance(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        w.write("stages/01-draft/output/check.md", "pass\n\nLooks good.\n")
        self.assertEqual(w.state()["by_stage"]["01-draft"]["state"], "pending")

    def test_human_pass_accepts_then_edit_makes_it_stale(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        code, out, err = w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        self.assertEqual(code, 0, err)
        st = w.state()
        self.assertEqual(st["by_stage"]["01-draft"]["state"], "accepted")
        self.assertEqual(st["next"], "run 02-edit")
        w.write("stages/01-draft/output/draft.md", "Draft, edited by hand.\n")
        st = w.state()
        self.assertEqual(st["by_stage"]["01-draft"]["state"], "stale")
        self.assertIn("outputs changed since review: draft.md", st["by_stage"]["01-draft"]["detail"][0])
        self.assertFalse(st["by_stage"]["02-edit"]["may_run"])

    def test_factory_or_contract_change_makes_review_stale(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        w.write("_shared/rules.md", "Be very brief.\n")
        self.assertIn("inputs changed", w.state()["by_stage"]["01-draft"]["detail"][0])
        w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        w.write("stages/01-draft/CONTEXT.md", STAGE_A + "\nOne more rule.\n")
        self.assertEqual(w.state()["by_stage"]["01-draft"]["detail"], ["stage CONTEXT.md changed since review"])

    def test_human_fail_is_rejected_and_needs_a_reason(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        code, _, err = w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "fail")
        self.assertEqual(code, 2)
        self.assertIn("needs --reason", err)
        w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "fail", "--reason", "too long")
        st = w.state()
        self.assertEqual(st["by_stage"]["01-draft"]["state"], "rejected")
        self.assertEqual(st["next"], "revise 01-draft, then review it again")
        self.assertTrue(st["by_stage"]["01-draft"]["may_run"])

    def test_reviewer_kind_cannot_be_downgraded(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        before = tree_digest(w.root)
        code, _, err = w.record("01", "--reviewer", "model", "--by", "reviewer", "--decision", "pass")
        self.assertEqual(code, 2)
        self.assertIn("declares a human check", err)
        self.assertEqual(tree_digest(w.root), before)
        code, _, err = w.record("01", "--reviewer", "script")
        self.assertEqual(code, 2)

    def test_hand_written_evidence_of_another_kind_stays_pending(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        check = w.root / "stages/01-draft/output/check.md"
        check.write_text(check.read_text().replace("reviewer: human", "reviewer: model"))
        self.assertIn("from a model reviewer", w.state()["by_stage"]["01-draft"]["detail"][0])

    def accept_stage_one(self, w):
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        self.assertEqual(w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")[0], 0)

    def test_script_gate_pass_and_fail(self):
        w = self.ws(check_b="Reviewer: script `python3 _tools/check.py`")
        w.write("_tools/check.py", "import sys, pathlib\n"
                "ok = any(pathlib.Path('stages/02-edit/output').glob('*-final.md'))\n"
                "print('final present' if ok else 'no final file')\nsys.exit(0 if ok else 1)\n")
        self.accept_stage_one(w)
        w.write("stages/02-edit/output/notes.md", "wip\n")
        self.assertEqual(w.record("02", "--reviewer", "script")[0], 0)
        row = w.state()["by_stage"]["02-edit"]
        self.assertEqual((row["state"], row["kind"]), ("rejected", "script"))
        self.assertIn("no final file", row["detail"][0])
        w.write("stages/02-edit/output/demo-final.md", "Final.\n")
        self.assertEqual(w.record("02", "--reviewer", "script")[0], 0)
        st = w.state()
        self.assertEqual(st["by_stage"]["02-edit"]["state"], "accepted")
        self.assertTrue(st["next"].startswith("pipeline accepted"))
        code, _, err = w.record("02", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        self.assertEqual(code, 2)

    def test_upstream_change_invalidates_downstream(self):
        w = self.ws()
        self.accept_stage_one(w)
        w.write("stages/02-edit/output/demo-final.md", "Final.\n")
        w.record("02", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        # Re-recording the upstream verdict for unchanged bytes leaves the downstream review current.
        w.record("01", "--reviewer", "human", "--by", "lee", "--decision", "pass")
        self.assertEqual(w.state()["by_stage"]["02-edit"]["state"], "accepted")
        w.write("stages/01-draft/output/draft.md", "New draft.\n")
        st = w.state()
        self.assertEqual(st["by_stage"]["01-draft"]["state"], "stale")
        self.assertEqual(st["by_stage"]["02-edit"]["state"], "stale")
        self.assertTrue(st["next"].startswith("re-run or re-review 01-draft"))

    def test_entry_routing(self):
        w = self.ws()
        w.write("CLAUDE.md", "@AGENTS.md\n")
        self.assertEqual(w.state()["entry"], "ok")
        w.write("CLAUDE.md", "# Demo\n\nOwn routing table.\n")
        st = w.state()
        self.assertTrue(st["entry"].startswith("conflict: CLAUDE.md"))
        self.assertTrue(st["next"].startswith("stop: entry conflict"))
        self.assertFalse(any(r["may_run"] for r in st["stages"]))
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        self.assertEqual(w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")[0], 2)
        (w.root / "AGENTS.md").unlink()
        self.assertTrue(w.state()["entry"].startswith("legacy: CLAUDE.md"))
        (w.root / "CLAUDE.md").unlink()
        self.assertTrue(w.state()["entry"].startswith("missing"))
        w.write("AGENTS.md", "Read CLAUDE.md first.\n")
        w.write("CLAUDE.md", "# Demo\n\nRouting.\n")
        self.assertTrue(w.state()["entry"].startswith("conflict: AGENTS.md points"))

    def test_nested_stage_directory_resolves_its_root(self):
        w = self.ws()
        st = w.state(w.root / "stages/02-edit/output")
        self.assertEqual(Path(st["root"]), w.root.resolve())
        outside = self.base / "ws-sibling"
        outside.mkdir()
        self.assertIsNone(w.state(outside)["root"])

    def test_symlinks_cannot_widen_scope(self):
        w = self.ws()
        secret = self.base / "secret.txt"
        secret.write_text("outside\n")
        os.symlink(secret, w.root / "stages/01-draft/output/draft.md")
        row = w.state()["by_stage"]["01-draft"]
        self.assertEqual(row["state"], "blocked")
        self.assertIn("resolves outside output/", row["detail"][0])
        (w.root / "stages/01-draft/output/draft.md").unlink()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        os.symlink(secret, w.root / "stages/01-draft/output/check.md")
        code, _, err = w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        self.assertEqual(code, 2)
        self.assertIn("symlink", err)
        self.assertEqual(secret.read_text(), "outside\n")

    def test_missing_input_blocks_the_stage(self):
        w = self.ws()
        (w.root / "_shared/rules.md").unlink()
        st = w.state()
        self.assertEqual(st["next"], "blocked: 01-draft is missing inputs ../../_shared/rules.md")
        self.assertFalse(st["by_stage"]["01-draft"]["may_run"])

    def test_record_refuses_an_unproduced_stage(self):
        w = self.ws()
        code, _, err = w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")
        self.assertEqual(code, 2)
        self.assertIn("run the stage first", err)

    def test_state_writes_nothing(self):
        w = self.ws()
        w.write("stages/01-draft/output/draft.md", "Draft.\n")
        before = tree_digest(w.root)
        run("state.py", str(w.root))
        run("state.py", str(w.root), "--json")
        self.assertEqual(tree_digest(w.root), before)

    def test_text_output_names_the_next_action(self):
        w = self.ws()
        code, out, _ = run("state.py", str(w.root))
        self.assertEqual(code, 0)
        self.assertIn("01-draft  unproduced", out)
        self.assertTrue(out.rstrip().endswith("next: run 01-draft"))


class TextBudget(unittest.TestCase):
    """Text an agent reads on every step or every ICM turn has a byte ceiling."""

    def test_skill_and_state_output_sizes(self):
        skill = (SCRIPTS.parent / "SKILL.md").read_text()
        description = skill.split("description:", 1)[1].split("\n", 1)[0].strip()
        self.assertLessEqual(len(description), 300, "the catalog carries this on every step")
        self.assertLessEqual(len(skill.encode()), 5200)
        with tempfile.TemporaryDirectory() as tmp:
            w = Workspace(Path(tmp) / "ws")
            w.write("stages/01-draft/output/draft.md", "Draft.\n")
            w.record("01", "--reviewer", "human", "--by", "dana", "--decision", "pass")
            self.assertLessEqual(len(run("state.py", str(w.root))[1].encode()), 600)


if __name__ == "__main__":
    unittest.main()
