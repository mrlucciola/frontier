"""pm ticket history: keep ticket history on refs/heads/pm-store instead of main."""
import argparse
import contextlib
import fcntl
import json
import os
import subprocess
import sys

import gitcommit
import routing
import store as st
from store import TicketError

HISTORY_REF = "pm-store"
HISTORY_BRANCH_REF = f"refs/heads/{HISTORY_REF}"

SUBVERBS = (
    ("status", "print legacy|migrating|on|behind|missing"),
    ("enable", "move history to pm-store (idempotent; default branch, clean index)"),
    ("disable", "move history back to main (keeps the pm-store ref)"),
    ("sync", "record the current working file on pm-store"),
    ("restore", "rewrite a missing working file from pm-store"),
)


def register(subparsers):
    sp = subparsers.add_parser(
        "history", help="keep ticket history on refs/heads/pm-store instead of "
                        "main (status|enable|disable|sync|restore)")
    hsub = sp.add_subparsers(dest="hcmd", required=True)
    for name, text in SUBVERBS:
        hp = hsub.add_parser(name, help=text)
        hp.add_argument("--store", dest="repo", default=argparse.SUPPRESS,
                        help="repo root holding the .pm store")
        hp.add_argument("--repo", dest="repo", default=argparse.SUPPRESS,
                        help=argparse.SUPPRESS)


class Ctx:
    """One store and its repo, with the paths every sub-verb needs."""

    def __init__(self, args):
        self.root = st.find_store(getattr(args, "repo", None))
        if not self.root:
            raise TicketError("no ticket store found (run: pm ticket init)")
        with open(os.path.join(self.root, "config.json")) as f:
            self.cfg = json.load(f)
        self.repo = os.path.dirname(os.path.abspath(self.root))
        self.dirname = os.path.basename(self.root)
        self.entry = st.TICKET_FILE
        self.rel = f"{self.dirname}/{self.entry}"
        self.cfg_rel = f"{self.dirname}/config.json"
        self.path = os.path.join(self.root, self.entry)
        self.marker = os.path.join(self.root, st.HISTORY_PENDING)
        self.has_git = os.path.exists(os.path.join(self.repo, ".git"))

    def write_config(self):
        tmp = os.path.join(self.root, "config.json.tmp")
        with open(tmp, "w") as f:
            json.dump(self.cfg, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, os.path.join(self.root, "config.json"))

    def clear_marker(self):
        with contextlib.suppress(OSError):
            os.remove(self.marker)


@contextlib.contextmanager
def flocked(root):
    with open(os.path.join(root, "lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        yield


def raise_fault(fault):
    """A plain-str skip is a refusal; a GitFault prints like `st.commit` and exits 3."""
    if not isinstance(fault, gitcommit.GitFault):
        raise TicketError(str(fault))
    print(f"pm: {fault}", file=sys.stderr)
    if fault.stderr_tail:
        print(fault.stderr_tail, file=sys.stderr)
    raise st.GitCommitFailed(fault)


def git(ctx, *argv, ok=(0,), input=None):
    """Run git in the repo; a result code outside `ok` is a fault."""
    r = gitcommit._git(ctx.repo, *argv, input=input)
    if r.returncode not in ok:
        raise_fault(gitcommit._fault(r, argv[0], False))
    return r


def probe(ctx, *argv):
    """Run git and return its exit code; a probe never faults."""
    return gitcommit._git(ctx.repo, *argv).returncode


def blobs(ctx):
    """(working blob oid or None, pm-store tip entry oid or None); reads only."""
    work = None
    if os.path.exists(ctx.path):
        r = gitcommit._git(ctx.repo, "hash-object", "--no-filters", "--", ctx.rel)
        if r.returncode == 0:
            work = r.stdout.strip()
    r = gitcommit._git(ctx.repo, "rev-parse", "-q", "--verify",
                       f"{HISTORY_BRANCH_REF}:{ctx.entry}")
    return work, (r.stdout.strip() if r.returncode == 0 else None)


def is_behind(ctx):
    work, tip = blobs(ctx)
    return work is not None and work != tip


def staged_set(ctx):
    r = git(ctx, "diff", "--cached", "--no-renames", "--name-status")
    staged = {}
    for line in r.stdout.splitlines():
        status, _, path = line.partition("\t")
        staged[path] = status
    return staged


def precheck(ctx):
    """Default branch, and nothing staged except a crashed run's own staging:
    `D tickets.jsonl`, and config.json/.gitignore whose staged content equals
    the working tree."""
    if not ctx.has_git:
        raise TicketError(f"{ctx.repo} is not a git repository")
    branch = git(ctx, "branch", "--show-current").stdout.strip()
    default = gitcommit._default_branch(ctx.repo)
    if not branch or (default and branch != default):
        raise TicketError(
            f"{ctx.repo} is on {branch or 'a detached HEAD'}, not "
            f"{default or 'its default branch'}; run this from the default branch")
    staged = staged_set(ctx)
    extra = []
    for p, status in sorted(staged.items()):
        if p == ctx.rel and status == "D":
            continue
        if p in (ctx.cfg_rel, ".gitignore") and probe(
                ctx, "diff", "--quiet", "--", p) == 0:
            continue
        extra.append(p)
    if extra:
        raise TicketError(
            "the index is not empty; pm never resets it. Staged: "
            + ", ".join(f"{staged[p]} {p}" for p in extra)
            + ". Commit or unstage them, then re-run")
    return staged


def set_gitignore(ctx, present):
    """Add or remove the two history lines: the working file and the
    `history-pending` marker."""
    path = os.path.join(ctx.repo, ".gitignore")
    existing = ""
    if os.path.exists(path):
        with open(path) as f:
            existing = f.read()
    stripped = [ln.strip() for ln in existing.splitlines()]
    wanted = [ctx.rel, f"{ctx.dirname}/{st.HISTORY_PENDING}"]
    if present:
        missing = [w for w in wanted if w not in stripped]
        if missing:
            with open(path, "a") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write("".join(w + "\n" for w in missing))
    elif any(w in stripped for w in wanted):
        with open(path, "rb") as f:
            raw = f.read()
        kept = [ln for ln in raw.splitlines(keepends=True)
                if ln.decode("utf-8", "surrogateescape").strip() not in wanted]
        with open(path, "wb") as f:
            f.write(b"".join(kept))


def missing_msg(ctx):
    return (f"{ctx.rel} is missing but this store keeps history on "
            f"{HISTORY_REF}; run: pm ticket history restore")


def state(ctx):
    if not ctx.cfg.get("history_ref"):
        return "legacy"
    if not os.path.exists(ctx.path):
        return "missing"
    if ctx.has_git and probe(ctx, "cat-file", "-e", f"HEAD:{ctx.rel}") == 0:
        return "migrating"
    if probe(ctx, "check-ignore", "-q", "--", ctx.rel) != 0:
        return "migrating"
    return "behind" if is_behind(ctx) else "on"


def require_key(ctx):
    if not ctx.cfg.get("history_ref"):
        raise TicketError(
            f"{ctx.dirname}/config.json has no history_ref; this store keeps "
            "history on its checked-out branch (run: pm ticket history enable)")


def do_status(ctx):
    print(state(ctx))


def do_sync(ctx):
    require_key(ctx)
    with flocked(ctx.root):
        if not os.path.exists(ctx.path):
            raise TicketError(missing_msg(ctx))
        fault = gitcommit.commit_blob_to_ref(
            ctx.repo, ctx.rel, HISTORY_BRANCH_REF, "pm: history sync")
        if fault:
            raise_fault(fault)
        ctx.clear_marker()
    print(f"OK: {ctx.repo} ticket history synced to {HISTORY_BRANCH_REF}")


def do_restore(ctx):
    require_key(ctx)
    with flocked(ctx.root):
        r = subprocess.run(
            ["git", "-C", ctx.repo, "cat-file", "blob",
             f"{HISTORY_BRANCH_REF}:{ctx.entry}"],
            capture_output=True, env=gitcommit._clean_git_env(),
            timeout=gitcommit.COMMIT_TIMEOUT)
        if r.returncode != 0:
            raise TicketError(
                f"{HISTORY_BRANCH_REF} has no {ctx.entry}; nothing to restore")
        if os.path.exists(ctx.path):
            with open(ctx.path, "rb") as f:
                same = f.read() == r.stdout
            if not same:
                raise TicketError(
                    f"{ctx.rel} exists and differs from the {HISTORY_REF} tip; "
                    "it may hold newer rows. Run: pm ticket history sync")
            ctx.clear_marker()
            print(f"OK: {ctx.rel} already matches {HISTORY_BRANCH_REF}")
            return
        tmp = ctx.path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(r.stdout)
        os.replace(tmp, ctx.path)
        ctx.clear_marker()
    print(f"OK: restored {ctx.rel} from {HISTORY_BRANCH_REF}")


def do_enable(ctx):
    precheck(ctx)
    with flocked(ctx.root):
        if not os.path.exists(ctx.path):
            raise TicketError(missing_msg(ctx) if ctx.cfg.get("history_ref") else
                              f"{ctx.rel} does not exist; nothing to move")
        # 1. Flush (skipped when a crashed run already staged the removal).
        if staged_set(ctx).get(ctx.rel) != "D":
            if git(ctx, "status", "--porcelain", "--", ctx.rel).stdout.strip():
                skipped = gitcommit.commit_store(
                    ctx.root, "pm: flush before history move", legacy=True)
                if skipped:
                    raise_fault(skipped)
        in_head = probe(ctx, "cat-file", "-e", f"HEAD:{ctx.rel}") == 0
        # 2. Seed, or sync when the ref already exists.
        if probe(ctx, "rev-parse", "-q", "--verify",
                 f"{HISTORY_BRANCH_REF}^{{commit}}") == 0:
            message = "pm: history sync"
        else:
            short = gitcommit._git(ctx.repo, "rev-parse", "--short", "HEAD")
            message = ("pm: seed pm-store from "
                       + (short.stdout.strip() if short.returncode == 0
                          else "an unborn HEAD"))
        fault = gitcommit.commit_blob_to_ref(
            ctx.repo, ctx.rel, HISTORY_BRANCH_REF, message)
        if fault:
            raise_fault(fault)
        # 3. Config.
        if ctx.cfg.get("history_ref") != HISTORY_REF:
            ctx.cfg["history_ref"] = HISTORY_REF
            ctx.write_config()
        # 4. Ignore.
        set_gitignore(ctx, True)
        # 5. Stage.
        if probe(ctx, "ls-files", "--error-unmatch", "--", ctx.rel) == 0:
            git(ctx, "rm", "--cached", "-q", "--", ctx.rel)
        git(ctx, "add", "--", ctx.cfg_rel, ".gitignore")
        # 6. Assert the exact staged set.
        staged = staged_set(ctx)
        problems = []
        for path, status in sorted(staged.items()):
            if path == ctx.rel:
                if status != "D":
                    problems.append(f"{status} {path} (expected D)")
            elif path in (ctx.cfg_rel, ".gitignore"):
                if status not in ("M", "A"):
                    problems.append(f"{status} {path} (expected M or A)")
            else:
                problems.append(f"{status} {path} (unexpected)")
        if in_head and staged and staged.get(ctx.rel) != "D":
            problems.append(f"{ctx.rel} is not staged as deleted")
        if not in_head and ctx.rel in staged:
            problems.append(f"{ctx.rel} staged but not in HEAD")
        if problems:
            raise TicketError("staged set is not the expected one; nothing "
                              "committed: " + "; ".join(problems))
        # 7. Commit (porcelain: hooks and signing run).
        if staged:
            git(ctx, "commit", "-q", "-m",
                "pm: move ticket history to refs/heads/pm-store")
        # 8. Verify.
        failed = []
        if probe(ctx, "ls-files", "--error-unmatch", "--", ctx.rel) != 1:
            failed.append(f"{ctx.rel} is still tracked")
        if probe(ctx, "check-ignore", "-q", "--", ctx.rel) != 0:
            failed.append(f"{ctx.rel} is not ignored")
        work, tip = blobs(ctx)
        if work is None or work != tip:
            failed.append(f"{HISTORY_REF}:{ctx.entry} differs from the working file")
        if failed:
            raise TicketError("verify failed: " + "; ".join(failed))
    print(f"OK: {ctx.repo} ticket history on {HISTORY_BRANCH_REF}")


def do_disable(ctx):
    allowed = {ctx.cfg_rel, ".gitignore", ctx.rel}
    precheck(ctx)
    with flocked(ctx.root):
        tracked = probe(ctx, "ls-files", "--error-unmatch", "--", ctx.rel) == 0
        if not ctx.cfg.get("history_ref") and tracked and not staged_set(ctx):
            print(f"OK: {ctx.repo} ticket history already on its branch")
            return
        if not os.path.exists(ctx.path):
            raise TicketError(missing_msg(ctx))
        set_gitignore(ctx, False)
        if "history_ref" in ctx.cfg:
            del ctx.cfg["history_ref"]
            ctx.write_config()
        git(ctx, "add", "--", ctx.rel, ctx.cfg_rel, ".gitignore")
        staged = staged_set(ctx)
        in_head = probe(ctx, "cat-file", "-e", f"HEAD:{ctx.rel}") == 0
        problems = []
        for path, status in sorted(staged.items()):
            if path not in allowed:
                problems.append(f"{status} {path} (unexpected)")
            elif status not in ("M", "A"):
                problems.append(f"{status} {path} (expected M or A)")
        if ctx.rel not in staged and not in_head:
            problems.append(f"{ctx.rel} is not staged")
        if problems:
            raise TicketError("staged set is not the expected one; nothing "
                              "committed: " + "; ".join(problems))
        if staged:
            git(ctx, "commit", "-q", "-m", "pm: move ticket history back to main")
        if probe(ctx, "ls-files", "--error-unmatch", "--", ctx.rel) != 0:
            raise TicketError(f"verify failed: {ctx.rel} is not tracked")
        ctx.clear_marker()
    print(f"OK: {ctx.repo} ticket history back on its branch "
          f"({HISTORY_BRANCH_REF} kept)")


ACTIONS = {"status": do_status, "enable": do_enable, "disable": do_disable,
           "sync": do_sync, "restore": do_restore}


def run(args):
    try:
        ctx = Ctx(args)
        if args.hcmd != "status":
            routing.refuse_if_frozen(ctx.root)
        ACTIONS[args.hcmd](ctx)
    except subprocess.TimeoutExpired:
        raise TicketError("git took longer than "
                          f"{gitcommit.COMMIT_TIMEOUT}s (signing prompt?)")
