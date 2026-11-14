"""Every git call the store makes: the commit policy, the mechanics, the fault classifier.

A commit is bookkeeping, never the operation: every function here returns None
(done, or nothing to do) or a one-line skip reason, and never raises. A reason
that is a `GitFault` is a real git failure; a plain `str` is a policy skip.
"""
import json
import os
import re
import subprocess
import sys

#: Seconds a commit may take before it is skipped: long enough for a pinentry
#: prompt run by hand, short enough that an agent never hangs on a signing agent.
COMMIT_TIMEOUT = 120
NULL_OID = "0" * 40

#: The pinned agent identity: a session without it has every git call fail, because
#: the sandbox denies ~/.gitconfig.
IDENTITY_VAR = "GIT_CONFIG_GLOBAL"
IDENTITY_PREFIX = "GIT_CONFIG_GLOBAL=/Users/matthias/.config/claude-agent/gitconfig "
AGENT_MARKERS = ("CLAUDECODE", "CODEX_AGENT_IDENTITY")

IDENTITY_EPERM = re.compile(
    r"unable to access '(?:/Users/matthias/\.gitconfig|~/\.gitconfig)': "
    r"Operation not permitted")
SIGNING = re.compile(
    r"gpg: (?:signing failed|.{0,80}?)"
    r".{0,120}?(?:Operation not permitted|IPC connect call failed"
    r"|No such file or directory)"
    r"|gpg: signing failed(?:: No secret key)?"
    r"|(?:error: )?gpg failed to sign the data"
    r"|ssh-keygen -Y sign|error: Load key |Couldn't load public key"
    r"|error: unable to (?:start|sign) .{0,40}ssh-keygen"
    r"|fatal: failed to write commit object", re.S)

REMEDY = {
    "identity-missing": (
        "no agent git identity for this session: git fell back to ~/.gitconfig, "
        "which the sandbox denies. Re-run the SAME git command once, prefixed "
        f"exactly: {IDENTITY_PREFIX}-- or open a fresh session."),
    "signing": (
        "signing failed: infrastructure fault, not the task's. Re-run the SAME "
        "git command with `-c commit.gpgsign=false` inserted right after `git`; "
        "if it writes a commit message, add a trailing `Unsigned-Commit: "
        "<report id>` trailer."),
}


class GitFault(str):
    """A skip reason that is a genuine git failure (non-zero exit or a timeout),
    not a policy choice. A `str`, so a caller that only prints the reason works
    unchanged. `.stderr_tail` carries git's own, possibly multi-line, output."""

    def __new__(cls, reason, stderr_tail=""):
        obj = str.__new__(cls, reason)
        obj.stderr_tail = stderr_tail
        return obj


# --- fault classifier ---

def identity_env_missing(env=None):
    """True in an agent session (AGENT_MARKERS) with GIT_CONFIG_GLOBAL unset or
    empty. Never true in the operator's own shell."""
    env = os.environ if env is None else env
    return any(env.get(m) for m in AGENT_MARKERS) and not env.get(IDENTITY_VAR)


def _text(proc):
    parts = [getattr(proc, a, None) for a in ("stderr", "stdout")]
    return "\n".join(p for p in parts if isinstance(p, str) and p)


def classify(proc, env=None):
    """(class, text) for a failed git result: "identity-missing", "signing" or
    "other". An unset identity wins over the text, since it fails every call."""
    text = _text(proc)
    if identity_env_missing(env) or IDENTITY_EPERM.search(text):
        return "identity-missing", text
    if SIGNING.search(text):
        return "signing", text
    return "other", text


def announce(cls):
    """One stderr line naming the class and its remedy; nothing for "other"."""
    if cls in REMEDY:
        print(f"gitfault[{cls}]: {REMEDY[cls]}", file=sys.stderr)


def guard_env():
    """Call before the first git call: announce a missing identity now, so the
    remedy prints ahead of the failure it explains. True when it announced."""
    if identity_env_missing():
        announce("identity-missing")
        return True
    return False


def on_failure(proc, already_warned=False):
    """Classify and announce a failed git result; returns the class. An
    identity-missing line already printed by `guard_env` is not repeated."""
    try:
        cls, _ = classify(proc)
    except Exception:
        return "other"
    if not (cls == "identity-missing" and already_warned):
        announce(cls)
    return cls


# --- mechanics ---

def _clean_git_env():
    """Every GIT_* var dropped except the two naming a config file. A caller run
    from inside a git hook has GIT_DIR and friends set for the real commit, and
    those override `-C repo_dir`."""
    safe = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")
    return {k: v for k, v in os.environ.items()
            if not k.startswith("GIT_") or k in safe}


def _git(repo_dir, *argv, timeout=COMMIT_TIMEOUT, input=None):
    return subprocess.run(["git", "-C", repo_dir, *argv], capture_output=True,
                          text=True, timeout=timeout, env=_clean_git_env(),
                          input=input)


def _fault(result, step, warned, fallback=None):
    on_failure(result, already_warned=warned)
    tail = result.stderr.strip() or result.stdout.strip()
    lines = tail.splitlines()
    return GitFault(lines[-1] if lines else fallback or
                    f"git {step} exited {result.returncode}", tail)


def _timeout_fault():
    return GitFault(f"git took longer than {COMMIT_TIMEOUT}s (signing prompt?)")


def commit_paths(repo_dir, rel_paths, message):
    """Commit only `rel_paths` (repo-relative) in one commit, `git commit -o`, so
    nothing else staged or dirty is swept in."""
    warned = False
    try:
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            return None
        warned = guard_env()
        status = _git(repo_dir, "status", "--porcelain", "--", *rel_paths)
        if status.returncode != 0:
            return _fault(status, "status", warned, "git status failed")
        if not status.stdout.strip():
            return None
        add = _git(repo_dir, "add", "--", *rel_paths)
        if add.returncode != 0:
            return _fault(add, "add", warned, "git add failed")
        r = _git(repo_dir, "commit", "-q", "-o", "-m", message, "--", *rel_paths)
        if r.returncode != 0:
            return _fault(r, "commit", warned)
        return None
    except subprocess.TimeoutExpired:
        return _timeout_fault()
    except OSError as e:
        return str(e)


def commit_blob_to_ref(repo_dir, rel_path, ref, message):
    """Record `rel_path`'s bytes as one new commit on `ref` by plumbing only:
    never the index, HEAD, the working tree or any other ref. The tree holds
    one entry, basename(rel_path); an unchanged blob commits nothing; the ref
    moves by compare-and-swap; `-S` exactly when commit.gpgsign is true."""
    warned = False
    entry = os.path.basename(rel_path)
    try:
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            return None
        warned = guard_env()
        r = _git(repo_dir, "hash-object", "-w", "--no-filters", "--", rel_path)
        if r.returncode != 0:
            return _fault(r, "hash-object", warned)
        blob = r.stdout.strip()
        r = _git(repo_dir, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}")
        tip = r.stdout.strip() if r.returncode == 0 else ""
        if tip:
            r = _git(repo_dir, "rev-parse", "-q", "--verify", f"{ref}:{entry}")
            if r.returncode == 0 and r.stdout.strip() == blob:
                return None
        r = _git(repo_dir, "mktree", input=f"100644 blob {blob}\t{entry}\n")
        if r.returncode != 0:
            return _fault(r, "mktree", warned)
        tree = r.stdout.strip()
        r = _git(repo_dir, "config", "--bool", "commit.gpgsign")
        sign = r.returncode == 0 and r.stdout.strip() == "true"
        argv = ["commit-tree", tree]
        if tip:
            argv += ["-p", tip]
        if sign:
            argv.append("-S")
        argv += ["-m", message]
        r = _git(repo_dir, *argv)
        if r.returncode != 0:
            return _fault(r, "commit-tree", warned)
        commit = r.stdout.strip()
        r = _git(repo_dir, "update-ref", "-m", message, ref, commit, tip or NULL_OID)
        if r.returncode != 0:
            return _fault(r, "update-ref", warned)
        return None
    except subprocess.TimeoutExpired:
        return _timeout_fault()
    except OSError as e:
        return str(e)


# --- store commit policy ---

def _default_branch(repo_dir):
    r = _git(repo_dir, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if r.returncode == 0:
        return r.stdout.strip().split("/", 1)[-1]
    r = _git(repo_dir, "config", "--get", "init.defaultBranch")
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    for name in ("main", "master"):
        if _git(repo_dir, "rev-parse", "--verify", "-q",
                f"refs/heads/{name}").returncode == 0:
            return name
    return None


def _off_default_branch(repo_dir, warned):
    """A reason when the checkout is not on its default branch (or is detached)."""
    branch = _git(repo_dir, "branch", "--show-current")
    if branch.returncode != 0:
        on_failure(branch, already_warned=warned)
    current = branch.stdout.strip()
    default = _default_branch(repo_dir)
    if not current or (default and current != default):
        return (f"{repo_dir} is on {current or 'a detached HEAD'}, "
                f"not {default or 'its default branch'} (cl-111ef6)")
    return None


def commit_store(root, message, ticket_file="tickets.jsonl", extra_paths=(),
                 legacy=False):
    """Commit the store's ticket file in the repo owning `root` (the `.pm` dir).
    `extra_paths` (repo-relative) ride on the same commit on the branch path.
    `legacy=True` forces the branch path even on a `history_ref` store: `history
    enable` flushes the tracked copy that way before it stops being tracked.

    A store whose config.json sets `history_ref` records the file on that ref by
    plumbing, with no branch skip. Otherwise the file is committed on the
    checked-out branch, but only when that is the default branch: elsewhere the
    row stays saved, uncommitted, and the reason comes back as a plain `str`. A
    fresh untracked config.json rides on the same commit. Returns None on
    success or when there is nothing to commit, else a skip reason (`GitFault`
    for a real git failure). Never raises."""
    repo_dir = os.path.dirname(os.path.abspath(root))
    try:
        with open(os.path.join(root, "config.json")) as f:
            config = json.load(f)
    except (OSError, ValueError):
        config = {}
    rel = os.path.join(os.path.basename(root), ticket_file)
    if config.get("history_ref") and not legacy:
        return commit_blob_to_ref(
            repo_dir, rel, f"refs/heads/{config['history_ref']}", message)
    warned = False
    try:
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            return None
        warned = guard_env()
        status = _git(repo_dir, "status", "--porcelain", "--", rel)
        if status.returncode != 0:
            return _fault(status, "status", warned, "git status failed")
        if not status.stdout.strip():
            return None
        off = _off_default_branch(repo_dir, warned)
        if off:
            return off
    except subprocess.TimeoutExpired:
        return _timeout_fault()
    except OSError as e:
        return str(e)
    paths = [rel, *extra_paths]
    cfg_rel = os.path.join(os.path.basename(root), "config.json")
    try:
        cfg = _git(repo_dir, "status", "--porcelain", "--", cfg_rel)
        if cfg.stdout.startswith("??"):
            paths.append(cfg_rel)
    except (subprocess.TimeoutExpired, OSError):
        pass
    return commit_paths(repo_dir, paths, message)
