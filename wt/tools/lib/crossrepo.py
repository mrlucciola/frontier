"""Cross-repo guard: may wt change repo TARGET on behalf of repo SOURCE?

usage: crossrepo.py SOURCE TARGET SUBCOMMAND

Exit 0 to allow. Exit 1 and print the reason to refuse. The two paths are the same
repository once linked worktrees map to their main checkout; otherwise a declared pair
in $GIT_PAIRS_FILE (default ~/.claude/git-pairs.json, {"pairs":[{"source","targets","git"}]})
must list SUBCOMMAND. A missing or unreadable pairs file declares nothing, so the
answer is refuse.
"""
import json
import os
import sys

PAIRS_FILE_DEFAULT = "~/.claude/git-pairs.json"
NEVER_PAIR = {"push", "remote", "config", "submodule", "checkout"}


def load_pairs():
    path = os.path.expanduser(os.environ.get("GIT_PAIRS_FILE") or PAIRS_FILE_DEFAULT)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [e for e in data.get("pairs", []) if isinstance(e, dict)]
    except (OSError, ValueError, AttributeError):
        return []


def repo_root(path):
    d = os.path.realpath(path)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def main_checkout(root):
    """Map a linked worktree's root to its main checkout; anything else is unchanged."""
    dotgit = os.path.join(root, ".git")
    try:
        if not os.path.isfile(dotgit):
            return root
        with open(dotgit, encoding="utf-8") as f:
            line = f.readline(4096).strip()
        if not line.startswith("gitdir:"):
            return root
        gitdir = os.path.normpath(os.path.join(root, line[len("gitdir:"):].strip()))
        with open(os.path.join(gitdir, "commondir"), encoding="utf-8") as f:
            common_rel = f.readline(4096).strip()
        with open(os.path.join(gitdir, "gitdir"), encoding="utf-8") as f:
            back = f.readline(4096).strip()
        common = os.path.normpath(os.path.join(gitdir, common_rel))
        if not common_rel or not back or not os.path.isdir(common):
            return root
        if os.path.basename(common) != ".git":
            return root
        if os.path.dirname(gitdir) != os.path.join(common, "worktrees"):
            return root
        if os.path.realpath(os.path.join(gitdir, back)) != os.path.realpath(dotgit):
            return root
        return os.path.dirname(common)
    except (OSError, ValueError):
        return root


def same_repository(a, b):
    ra, rb = repo_root(a), repo_root(b)
    if ra is None or rb is None:
        return False
    return os.path.realpath(main_checkout(ra)) == os.path.realpath(main_checkout(rb))


def forms(path):
    return {os.path.normpath(path), os.path.realpath(path)}


def pair_allows(pairs, source, target, sub):
    if sub in NEVER_PAIR:
        return False
    for p in pairs:
        src = p.get("source")
        if not src or not forms(src) & forms(source):
            continue
        if sub not in (p.get("git") or []):
            continue
        if any(forms(t) & forms(target) for t in p.get("targets") or []):
            return True
    return False


def main(argv):
    if len(argv) != 3:
        sys.stderr.write(__doc__)
        return 2
    source, target, sub = argv
    if same_repository(source, target) or pair_allows(load_pairs(), source, target, sub):
        return 0
    print("cross-repo %s into %s is not a declared git-pairs pair from %s "
          "(~/.claude/git-pairs.json); wt refuses what the git guard would refuse. "
          "Ask the operator to add the pair." % (sub, target, source))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
