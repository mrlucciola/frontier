"""Exercise feynman/install.py against a temporary home directory.

Checks: dry-run changes nothing; install copies the skill and the tool (tests
excluded, recall.sh executable), merges the fragment without disturbing existing
hooks or allow rules, appends the instruction section once, creates the store; a
second run is a no-op; --link symlinks; --uninstall removes what was installed and
keeps the cards; a foreign directory in the way is reported, not deleted.
Run: python3 feynman/tests/test_install.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

COMPONENT = pathlib.Path(__file__).resolve().parent.parent
INSTALL = COMPONENT / "install.py"
FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def run(home, *args, expect=0):
    env = dict(os.environ, CONCEPT_GRAPH_ROOT=str(home / "concepts"))
    r = subprocess.run([sys.executable, str(INSTALL), "--home", str(home)] + list(args),
                       capture_output=True, text=True, env=env)
    if r.returncode != expect:
        FAILS.append("install %s: exit %d (want %d) %r %r" % (args, r.returncode, expect,
                                                              r.stdout[-300:], r.stderr[-300:]))
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
        check(not (home / "skills").exists() and not (home / "concepts").exists(), "dry-run creates nothing")

        run(home)
        for rel in ("skills/feynman/SKILL.md", "tools/concept-graph/cg.py",
                    "tools/concept-graph/recall.sh", "concepts/index.json"):
            check((home / rel).exists(), "installed %s" % rel)
        check(not (home / "tools/concept-graph/tests").exists(), "tool tests are not installed")
        check(os.access(home / "tools/concept-graph/recall.sh", os.X_OK), "hook is executable")
        s = json.loads((home / "settings.json").read_text())
        ups = [h["command"] for g in s["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        check("echo other" in ups and any("tools/concept-graph/recall.sh" in c for c in ups),
              "hooks merged, registration points into tools/: %r" % ups)
        check("Bash(ls:*)" in s["permissions"]["allow"] and
              "Bash(python3 ~/.claude/tools/concept-graph/cg.py:*)" in s["permissions"]["allow"],
              "allow rules merged: %r" % s["permissions"]["allow"])
        check(s.get("model") == "keep-me", "unrelated settings preserved")
        md = (home / "CLAUDE.md").read_text()
        check("keep this line" in md and "## Recalled concepts" in md, "instruction appended")

        # the installed tree works end to end: card, then the hook recalls it
        env = dict(os.environ, CONCEPT_GRAPH_ROOT=str(home / "concepts"))
        subprocess.run([sys.executable, str(home / "tools/concept-graph/cg.py"), "add", "wal-mode",
                        "--title", "SQLite WAL mode", "--alias", "wal", "--explain", "e",
                        "--analogy", "a", "--breaks", "b", "--pitch", "p"],
                       check=True, capture_output=True, env=env)
        r = subprocess.run(["bash", str(home / "tools/concept-graph/recall.sh")],
                           input=json.dumps({"session_id": "t", "cwd": tmp, "prompt": "how does WAL work?"}),
                           capture_output=True, text=True, env=env)
        check(r.returncode == 0 and r.stdout.startswith("{"),
              "installed hook recalls via sibling cg.py: %r %r" % (r.stdout[:60], r.stderr[:120]))

        r = run(home)
        check("already up to date" in r.stdout and "already present" in r.stdout, "second run is a no-op: %r" % r.stdout)
        check((home / "CLAUDE.md").read_text().count("## Recalled concepts") == 1, "instruction appended once")

        run(home, "--link")
        check((home / "skills/feynman").is_symlink() and (home / "tools/concept-graph").is_symlink(),
              "--link symlinks")

        run(home, "--uninstall")
        check(not (home / "skills/feynman").exists() and not (home / "tools/concept-graph").exists(),
              "uninstall removed installed paths")
        check((home / "concepts/cards/wal-mode.md").exists(), "uninstall keeps cards")
        s2 = json.loads((home / "settings.json").read_text())
        ups = [h["command"] for g in s2["hooks"].get("UserPromptSubmit", []) for h in g["hooks"]]
        check(ups == ["echo other"], "uninstall removed only our hook: %r" % ups)
        check(s2["permissions"]["allow"] == ["Bash(ls:*)"], "uninstall removed only our allow rules")

        home2 = pathlib.Path(tmp) / "home2"
        (home2 / "tools/concept-graph").mkdir(parents=True)
        (home2 / "tools/concept-graph/theirs.txt").write_text("x")
        r = run(home2, expect=1)
        check("PROBLEM" in r.stdout and (home2 / "tools/concept-graph/theirs.txt").exists(),
              "foreign dir protected: %r" % r.stdout[-200:])

    if FAILS:
        print("\n".join("FAIL " + f for f in FAILS))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
