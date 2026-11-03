#!/usr/bin/env python3
"""Install the Feynman component (skill + concept graph) into ~/.claude.
Standard library only, Python 3.9+.

    python3 feynman/install.py              # install or update
    python3 feynman/install.py --dry-run    # show every action, change nothing
    python3 feynman/install.py --link       # symlink instead of copy (git pull = live update)
    python3 feynman/install.py --uninstall  # remove what this script installed; keeps your cards

What it does, in order:
  1. skills/feynman        -> ~/.claude/skills/feynman
  2. tools/concept-graph   -> ~/.claude/tools/concept-graph (cg.py + recall.sh; tests excluded)
  3. merges config/settings.feynman.fragment.json into ~/.claude/settings.json
     (hook entries by command string, allow rules by value; backup first)
  4. appends instructions/feynman.md to ~/.claude/CLAUDE.md when its heading is
     absent (backup first)
  5. creates the concept store ~/.claude/concepts/

Idempotent: a second run replaces only what it installed (marker file
.installed-from inside copied dirs). A target that exists without the marker is
left alone unless --force is given. This script knows nothing about any other
component in this repo.
"""
import argparse
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys

COMPONENT = pathlib.Path(__file__).resolve().parent
MARKER = ".installed-from"

DIRS = [
    ("skills/feynman", "skills/feynman"),
    ("tools/concept-graph", "tools/concept-graph"),
]
FRAGMENT = COMPONENT / "config/settings.feynman.fragment.json"
INSTRUCTIONS = [
    ("instructions/feynman.md", "## Recalled concepts"),
]
IGNORE = shutil.ignore_patterns("tests", "__pycache__", ".tmp", "*.pyc")


def stamp():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


class Installer:
    def __init__(self, home, dry, link, force):
        self.home = home
        self.dry = dry
        self.link = link
        self.force = force
        self.problems = []

    def say(self, msg):
        print(("DRY  " if self.dry else "     ") + msg)

    # ---- files

    def _owned(self, target):
        if target.is_symlink():
            return True
        return (target / MARKER).exists() if target.is_dir() else False

    def put_dir(self, src_rel, dst_rel):
        src, dst = COMPONENT / src_rel, self.home / dst_rel
        if dst.exists() or dst.is_symlink():
            if not self._owned(dst) and not self.force:
                self.problems.append("%s exists and was not installed by this script (use --force)" % dst)
                return
            self.say("remove %s" % dst)
            if not self.dry:
                if dst.is_symlink() or dst.is_file():
                    dst.unlink()
                else:
                    shutil.rmtree(dst)
        if self.link:
            self.say("link   %s -> %s" % (dst, src))
            if not self.dry:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(src, target_is_directory=True)
        else:
            self.say("copy   %s -> %s" % (src_rel, dst))
            if not self.dry:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst, ignore=IGNORE)
                (dst / MARKER).write_text(str(COMPONENT) + "\n")

    def remove(self, dst_rel):
        dst = self.home / dst_rel
        if not (dst.exists() or dst.is_symlink()):
            return
        if dst.is_dir() and not dst.is_symlink() and not self._owned(dst) and not self.force:
            self.problems.append("%s was not installed by this script; left in place" % dst)
            return
        self.say("remove %s" % dst)
        if self.dry:
            return
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)

    # ---- settings

    def _settings(self):
        path = self.home / "settings.json"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return path, json.load(fh)
        return path, {}

    def _write_settings(self, path, data):
        if self.dry:
            return
        if path.exists():
            shutil.copy2(path, path.with_name("settings.json.bak-%s" % stamp()))
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)

    @staticmethod
    def _commands(group):
        return [h.get("command", "") for h in group.get("hooks", [])]

    def merge_settings(self):
        frag = json.loads(FRAGMENT.read_text())
        path, data = self._settings()
        changed = False
        hooks = data.setdefault("hooks", {})
        for event, groups in frag.get("hooks", {}).items():
            existing = hooks.setdefault(event, [])
            present = {c for g in existing for c in self._commands(g)}
            for g in groups:
                cmds = self._commands(g)
                if all(c in present for c in cmds):
                    continue
                self.say("settings: add %s hook %s" % (event, cmds))
                existing.append(g)
                changed = True
        allow = data.setdefault("permissions", {}).setdefault("allow", [])
        for rule in frag.get("permissions", {}).get("allow", []):
            if rule not in allow:
                self.say("settings: allow %s" % rule)
                allow.append(rule)
                changed = True
        if changed:
            self._write_settings(path, data)
        else:
            self.say("settings: already up to date")

    def unmerge_settings(self):
        frag = json.loads(FRAGMENT.read_text())
        path, data = self._settings()
        if not data:
            return
        ours = {c for groups in frag.get("hooks", {}).values() for g in groups for c in self._commands(g)}
        rules = frag.get("permissions", {}).get("allow", [])
        changed = False
        for event, groups in list(data.get("hooks", {}).items()):
            kept = [g for g in groups if not any(c in ours for c in self._commands(g))]
            if len(kept) != len(groups):
                self.say("settings: remove %s hook(s) from %s" % (len(groups) - len(kept), event))
                changed = True
                if kept:
                    data["hooks"][event] = kept
                else:
                    del data["hooks"][event]
        allow = data.get("permissions", {}).get("allow", [])
        kept = [r for r in allow if r not in rules]
        if len(kept) != len(allow):
            self.say("settings: remove %d allow rule(s)" % (len(allow) - len(kept)))
            data["permissions"]["allow"] = kept
            changed = True
        if changed:
            self._write_settings(path, data)

    # ---- instructions

    def append_instructions(self):
        path = self.home / "CLAUDE.md"
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        additions = []
        for rel, heading in INSTRUCTIONS:
            if heading in current:
                continue
            additions.append((COMPONENT / rel).read_text(encoding="utf-8").strip() + "\n")
            self.say("instructions: append %s to %s" % (rel, path))
        if not additions:
            self.say("instructions: already present")
            return
        if self.dry:
            return
        if path.exists():
            shutil.copy2(path, path.with_name("CLAUDE.md.bak-%s" % stamp()))
        with open(path, "a", encoding="utf-8") as fh:
            if current and not current.endswith("\n"):
                fh.write("\n")
            fh.write("\n" + "\n".join(additions))

    # ---- flows

    def install(self):
        for s, d in DIRS:
            self.put_dir(s, d)
        if self.problems:
            return
        if not self.dry and not self.link:
            # copy2 preserves modes, but make the hook's exec bit unconditional
            (self.home / "tools/concept-graph/recall.sh").chmod(0o755)
        self.merge_settings()
        self.append_instructions()
        self.say("store: %s" % (self.home / "concepts"))
        if not self.dry:
            env = dict(os.environ)
            env.setdefault("CONCEPT_GRAPH_ROOT", str(self.home / "concepts"))
            subprocess.run([sys.executable, str(self.home / "tools/concept-graph/cg.py"), "init"],
                           check=False, env=env)

    def uninstall(self):
        for _, d in DIRS:
            self.remove(d)
        self.unmerge_settings()
        self.say("left in place: %s (your cards) and the '## Recalled concepts' section in %s" % (
            self.home / "concepts", self.home / "CLAUDE.md"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--home", default="~/.claude")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--link", action="store_true", help="symlink dirs instead of copying")
    ap.add_argument("--force", action="store_true", help="replace targets this script did not install")
    ap.add_argument("--uninstall", action="store_true")
    a = ap.parse_args()
    home = pathlib.Path(os.path.expanduser(a.home))
    inst = Installer(home, a.dry_run, a.link, a.force)
    inst.uninstall() if a.uninstall else inst.install()
    if inst.problems:
        print("\n".join("PROBLEM " + p for p in inst.problems))
        return 1
    if not a.uninstall:
        print("\nverify:")
        print("  python3 %s status" % (home / "tools/concept-graph/cg.py"))
        print("  python3 %s" % (COMPONENT / "tests/test_recall_hook.py"))
        print("  %s has the first live test" % (COMPONENT / "INSTALL.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
