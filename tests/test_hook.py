"""Run vendor/claude/hooks/icm-detect.sh against fixture workspaces.

Checks: exit 0 always, silent outside an ICM workspace, valid JSON inside one,
CLAUDE.md preferred as the entry file, and paths with quotes survive escaping.
Standard library only. Run: python3 tests/test_hook.py
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / "vendor/claude/hooks/icm-detect.sh"
FRAGMENT = ROOT / "vendor/claude/settings.fragment.json"

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


def main() -> int:
    failures = []
    json.loads(FRAGMENT.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        for name, entries, expect_output, needles in CASES:
            d = pathlib.Path(tmp) / name
            build(d, entries)
            r = subprocess.run(["bash", str(HOOK)], cwd=d, capture_output=True, text=True)
            out = r.stdout.strip()
            if r.returncode != 0:
                failures.append(f"{name}: exit {r.returncode}")
            if r.stderr.strip():
                failures.append(f"{name}: stderr {r.stderr.strip()!r}")
            if not expect_output:
                if out:
                    failures.append(f"{name}: expected silence, got {out!r}")
                continue
            try:
                doc = json.loads(out)
            except ValueError as ex:
                failures.append(f"{name}: invalid JSON ({ex}): {out!r}")
                continue
            ctx = doc.get("hookSpecificOutput", {}).get("additionalContext", "")
            if doc.get("hookSpecificOutput", {}).get("hookEventName") != "SessionStart":
                failures.append(f"{name}: wrong hookEventName")
            for n in needles:
                if n not in out:
                    failures.append(f"{name}: missing {n!r} in {ctx!r}")
    if failures:
        print("\n".join(failures))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
