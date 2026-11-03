"""Exercise quiz/install.py against a temporary home directory.

Checks: dry-run changes nothing; install copies the skill (tests excluded), merges the
allow rule without disturbing existing settings; the installed quiz.py works; a second
run is a no-op; --link symlinks; --uninstall removes the skill and the rule and keeps
the data directory; a foreign directory in the way is reported, not deleted.
Run: python3 quiz/tests/test_install.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

COMPONENT = pathlib.Path(__file__).resolve().parents[1]
INSTALL = COMPONENT / "install.py"
RULE = "Bash(python3 ~/.claude/skills/adaptive-quiz/scripts/quiz.py:*)"
FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def run(home, *args, expect=0):
    r = subprocess.run([sys.executable, str(INSTALL), "--home", str(home)] + list(args),
                       capture_output=True, text=True)
    if r.returncode != expect:
        FAILS.append("install %s: exit %d (want %d) %r %r" % (args, r.returncode, expect,
                                                              r.stdout[-300:], r.stderr[-300:]))
    return r


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home = pathlib.Path(tmp) / "dot-claude"
        home.mkdir()
        existing = {"permissions": {"allow": ["Bash(ls:*)"]}, "model": "keep-me"}
        (home / "settings.json").write_text(json.dumps(existing))

        run(home, "--dry-run")
        check(json.loads((home / "settings.json").read_text()) == existing, "dry-run leaves settings untouched")
        check(not (home / "skills").exists(), "dry-run copies nothing")

        run(home)
        for rel in ("skills/adaptive-quiz/SKILL.md", "skills/adaptive-quiz/scripts/quiz.py",
                    "skills/adaptive-quiz/catalog.json", "skills/adaptive-quiz/references/workflow.md"):
            check((home / rel).exists(), "installed %s" % rel)
        s = json.loads((home / "settings.json").read_text())
        check(RULE in s["permissions"]["allow"] and "Bash(ls:*)" in s["permissions"]["allow"],
              "allow rule merged: %r" % s["permissions"]["allow"])
        check(s.get("model") == "keep-me", "unrelated settings preserved")
        check("hooks" not in s or s["hooks"] == {}, "no hooks registered: %r" % s.get("hooks"))

        knowledge = home / "knowledge"
        env = dict(os.environ, KNOWLEDGE_HOME=str(knowledge))
        r = subprocess.run([sys.executable, str(home / "skills/adaptive-quiz/scripts/quiz.py"), "doctor"],
                           capture_output=True, text=True, env=env)
        doc = json.loads(r.stdout)
        check(r.returncode == 0 and doc["database_exists"] is False and doc["questions"] == 24,
              "installed quiz.py doctor works: %r" % r.stdout[:120])
        r = subprocess.run([sys.executable, str(home / "skills/adaptive-quiz/scripts/quiz.py"),
                            "start", "--count", "2"], capture_output=True, text=True, env=env)
        check(r.returncode == 0 and len(json.loads(r.stdout)["questions"]) == 2,
              "installed quiz.py starts a session: %r %r" % (r.stdout[:80], r.stderr[:120]))

        r = run(home)
        check("already up to date" in r.stdout, "second run is a no-op: %r" % r.stdout)

        run(home, "--link")
        check((home / "skills/adaptive-quiz").is_symlink(), "--link symlinks")

        run(home, "--uninstall")
        check(not (home / "skills/adaptive-quiz").exists(), "uninstall removed the skill")
        check((knowledge / "quiz.sqlite3").exists(), "uninstall keeps the data")
        s2 = json.loads((home / "settings.json").read_text())
        check(s2["permissions"]["allow"] == ["Bash(ls:*)"], "uninstall removed only our rule")

        home2 = pathlib.Path(tmp) / "home2"
        (home2 / "skills/adaptive-quiz").mkdir(parents=True)
        (home2 / "skills/adaptive-quiz/theirs.txt").write_text("x")
        r = run(home2, expect=1)
        check("PROBLEM" in r.stdout and (home2 / "skills/adaptive-quiz/theirs.txt").exists(),
              "foreign dir protected: %r" % r.stdout[-200:])

    if FAILS:
        print("\n".join("FAIL " + f for f in FAILS))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
