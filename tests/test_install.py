"""Exercise vendor/claude/install.py against a temporary home directory.

Checks: dry-run changes nothing; install copies skills, tool and hooks, merges the
settings fragment without disturbing existing hooks or allow rules, appends the
instruction sections once, creates the store; a second install is a no-op for
settings and instructions; --link produces symlinks; --uninstall removes what was
installed and leaves the store, cards and instructions. Run: python3 tests/test_install.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
INSTALL = ROOT / "vendor/claude/install.py"
FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def run(home, *args):
    env = dict(os.environ, CONCEPT_GRAPH_ROOT=str(home / "concepts"))
    r = subprocess.run([sys.executable, str(INSTALL), "--home", str(home)] + list(args),
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        FAILS.append("install %s: exit %d %r %r" % (args, r.returncode, r.stdout[-300:], r.stderr[-300:]))
    return r


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home = pathlib.Path(tmp) / "dot-claude"
        home.mkdir()
        existing = {
            "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo other", "timeout": 1}]}]},
            "permissions": {"allow": ["Bash(ls:*)"]},
            "model": "keep-me",
        }
        (home / "settings.json").write_text(json.dumps(existing))
        (home / "CLAUDE.md").write_text("# mine\n\nkeep this line\n")

        run(home, "--dry-run")
        check(json.loads((home / "settings.json").read_text()) == existing, "dry-run leaves settings untouched")
        check(not (home / "skills").exists(), "dry-run copies nothing")

        r = run(home)
        for rel in ("skills/feynman/SKILL.md", "skills/icm-run/SKILL.md", "skills/icm-architect/SKILL.md",
                    "tools/concept-graph/cg.py", "hooks/concept-graph/recall.sh", "hooks/icm-detect.sh",
                    "concepts/index.json"):
            check((home / rel).exists(), "installed %s" % rel)
        check(not (home / "tools/concept-graph/tests").exists(), "tests are not installed")
        check(os.access(home / "hooks/concept-graph/recall.sh", os.X_OK), "hook is executable")
        s = json.loads((home / "settings.json").read_text())
        ups = [h["command"] for g in s["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        check("echo other" in ups and any("recall.sh" in c for c in ups), "UPS hooks merged: %r" % ups)
        check(any("icm-detect.sh" in h["command"] for g in s["hooks"]["SessionStart"] for h in g["hooks"]),
              "SessionStart hook added")
        check("Bash(ls:*)" in s["permissions"]["allow"] and
              "Bash(python3 ~/.claude/tools/concept-graph/cg.py:*)" in s["permissions"]["allow"],
              "allow rules merged: %r" % s["permissions"]["allow"])
        check(s.get("model") == "keep-me", "unrelated settings preserved")
        check(list(home.glob("settings.json.bak-*")), "settings backup written")
        md = (home / "CLAUDE.md").read_text()
        check("keep this line" in md and "## Recalled concepts" in md and "## ICM workspaces" in md,
              "instructions appended")

        r = run(home)
        check("already up to date" in r.stdout and "already present" in r.stdout, "second run is a no-op: %r" % r.stdout)
        s2 = json.loads((home / "settings.json").read_text())
        check(s2 == s, "settings unchanged on rerun")
        check((home / "CLAUDE.md").read_text().count("## Recalled concepts") == 1, "instructions appended once")

        r = run(home, "--link")
        check((home / "skills/feynman").is_symlink() and (home / "hooks/icm-detect.sh").is_symlink(), "--link symlinks")

        # a card survives uninstall; installed dirs and settings entries go away
        env = dict(os.environ, CONCEPT_GRAPH_ROOT=str(home / "concepts"))
        subprocess.run([sys.executable, str(home / "tools/concept-graph/cg.py"), "add", "x", "--allow-empty"],
                       check=True, capture_output=True, env=env)
        r = run(home, "--uninstall")
        check(not (home / "skills/feynman").exists() and not (home / "hooks/concept-graph").exists()
              and not (home / "tools/concept-graph").exists(), "uninstall removed installed paths")
        check((home / "concepts/cards/x.md").exists(), "uninstall keeps cards")
        s3 = json.loads((home / "settings.json").read_text())
        ups = [h["command"] for g in s3["hooks"].get("UserPromptSubmit", []) for h in g["hooks"]]
        check(ups == ["echo other"], "uninstall removed only our hook: %r" % ups)
        check("SessionStart" not in s3["hooks"], "empty event list removed")
        check(s3["permissions"]["allow"] == ["Bash(ls:*)"], "uninstall removed only our allow rules")

        # foreign directory in the way is reported, not deleted
        home2 = pathlib.Path(tmp) / "home2"
        (home2 / "skills/feynman").mkdir(parents=True)
        (home2 / "skills/feynman/theirs.txt").write_text("x")
        r = subprocess.run([sys.executable, str(INSTALL), "--home", str(home2)], capture_output=True, text=True)
        check(r.returncode == 1 and "PROBLEM" in r.stdout and (home2 / "skills/feynman/theirs.txt").exists(),
              "foreign dir protected: %r" % r.stdout[-200:])

    if FAILS:
        print("\n".join("FAIL " + f for f in FAILS))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
