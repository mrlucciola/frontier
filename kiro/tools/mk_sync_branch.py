#!/usr/bin/env python3
"""Refresh the LOCAL orphan branch kiro-sync from the current worktree.

The branch holds exactly the mk_sync.py default file list, so its raw views
on the public GitHub repo are the paste source for a firewalled machine.
Plumbing only: a temporary GIT_INDEX_FILE, write-tree, a parentless
commit-tree, and update-ref. It never checks out, never touches main, and
never pushes; the operator runs the printed push command themselves.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mk_sync import DEFAULT_FROM, ROOT, collect  # one default list, no drift

BRANCH = "kiro-sync"


def git(env=None, *args):
    p = subprocess.run(("git", "-C", str(ROOT)) + args, env=env,
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr.strip() or "git %s failed\n" % " ".join(args))
        raise SystemExit(1)
    return p.stdout.strip()


def main():
    top = Path(git(None, "rev-parse", "--show-toplevel")).resolve()
    if top != ROOT:
        sys.stderr.write("mk_sync_branch: must run inside %s\n" % ROOT)
        return 1
    fd, index = tempfile.mkstemp(prefix="kiro-sync-index-")
    os.close(fd)
    os.unlink(index)  # git creates the index file itself
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = index
    try:
        git(env, "read-tree", "--empty")
        files = collect(DEFAULT_FROM)
        for rel, path in files:
            git(env, "add", "--", str(path))
        tree = git(env, "write-tree")
        commit = git(None, "commit-tree", tree, "-m", "kiro: sync snapshot")
        git(None, "update-ref", "refs/heads/" + BRANCH, commit)
    finally:
        if os.path.exists(index):
            os.unlink(index)
    print("branch %s -> %s (%d files, worktree copies)" % (BRANCH, commit, len(files)))
    print("push when ready: git push --force origin kiro-sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
