"""Exercise icm/install.py against a temporary home directory.

Checks: dry-run changes nothing; install copies the skills and the hook, merges the
fragment without disturbing existing hooks or allow rules, appends the instruction
section once; a second run is a no-op; --link symlinks; --uninstall removes what was
installed and nothing else; a foreign directory in the way is reported, not deleted.
Run: python3 icm/tests/test_install.py
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
        existing = {
            "hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "echo other", "timeout": 1}]}]},
            "permissions": {"allow": ["Bash(ls:*)"]},
            "model": "keep-me",
        }
        (home / "settings.json").write_text(json.dumps(existing))
        (home / "CLAUDE.md").write_text("# mine\n\nkeep this line\n")

        run(home, "--dry-run")
        check(json.loads((home / "settings.json").read_text()) == existing, "dry-run leaves settings untouched")
        check(not (home / "skills").exists(), "dry-run copies nothing")

        run(home)
        for rel in ("skills/icm-architect/SKILL.md", "skills/icm-run/SKILL.md", "hooks/icm-detect.sh"):
            check((home / rel).exists(), "installed %s" % rel)
        check(os.access(home / "hooks/icm-detect.sh", os.X_OK), "hook is executable")
        s = json.loads((home / "settings.json").read_text())
        starts = [h["command"] for g in s["hooks"]["SessionStart"] for h in g["hooks"]]
        check("echo other" in starts and any("icm-detect.sh" in c for c in starts), "hooks merged: %r" % starts)
        check("Bash(ls:*)" in s["permissions"]["allow"] and "Bash(python3 _tools/*)" in s["permissions"]["allow"],
              "allow rules merged: %r" % s["permissions"]["allow"])
        check(s.get("model") == "keep-me", "unrelated settings preserved")
        check(list(home.glob("settings.json.bak-*")), "settings backup written")
        md = (home / "CLAUDE.md").read_text()
        check("keep this line" in md and "## ICM workspaces" in md, "instruction appended")

        r = run(home)
        check("already up to date" in r.stdout and "already present" in r.stdout, "second run is a no-op: %r" % r.stdout)
        check(json.loads((home / "settings.json").read_text()) == s, "settings unchanged on rerun")
        check((home / "CLAUDE.md").read_text().count("## ICM workspaces") == 1, "instruction appended once")

        run(home, "--link")
        check((home / "skills/icm-run").is_symlink() and (home / "hooks/icm-detect.sh").is_symlink(), "--link symlinks")

        run(home, "--uninstall")
        check(not (home / "skills/icm-run").exists() and not (home / "hooks/icm-detect.sh").exists(),
              "uninstall removed installed paths")
        s2 = json.loads((home / "settings.json").read_text())
        starts = [h["command"] for g in s2["hooks"].get("SessionStart", []) for h in g["hooks"]]
        check(starts == ["echo other"], "uninstall removed only our hook: %r" % starts)
        check(s2["permissions"]["allow"] == ["Bash(ls:*)"], "uninstall removed only our allow rule")
        check("## ICM workspaces" in (home / "CLAUDE.md").read_text(), "instruction section kept")

        home2 = pathlib.Path(tmp) / "home2"
        (home2 / "skills/icm-run").mkdir(parents=True)
        (home2 / "skills/icm-run/theirs.txt").write_text("x")
        r = run(home2, expect=1)
        check("PROBLEM" in r.stdout and (home2 / "skills/icm-run/theirs.txt").exists(),
              "foreign dir protected: %r" % r.stdout[-200:])

    if FAILS:
        print("\n".join("FAIL " + f for f in FAILS))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
