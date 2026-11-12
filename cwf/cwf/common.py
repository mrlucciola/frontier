from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import VERSION, SCHEMA_VERSION

DOMAINS = ["product", "design", "docs", "plan", "build", "maintain"]
EXIT = {"ok": 0, "skipped": 0, "invalid": 2, "blocked": 3,
        "failed": 4, "partial": 5, "error": 6}


class Fault(Exception):
    def __init__(self, message, code="invalid", details=None):
        super().__init__(message)
        self.code, self.details = code, details


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    if not isinstance(value, bytes):
        value = canonical(value).encode()
    return hashlib.sha256(value).hexdigest()


def result(data=None, status="ok", reason="complete"):
    return {"schema_version": SCHEMA_VERSION, "tool_version": VERSION,
            "status": status, "reason": reason, "data": data or {}}


def read_json(path, limit=1_048_576):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise Fault(f"Not a regular input file: {path}")
    if path.stat().st_size > limit:
        raise Fault("Input exceeds byte limit")
    try:
        return json.loads(path.read_bytes())
    except (ValueError, UnicodeError) as exc:
        raise Fault(f"Invalid JSON: {path.name}") from exc


def private_dir(path):
    path = Path(path)
    # Never follow a symlink in an owned state/config destination.
    for parent in [*reversed(path.parents), path]:
        if parent.is_symlink():
            raise Fault(f"Symlink in writable destination: {parent}", "blocked")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise Fault("Owned destination is not a directory", "blocked")
    return path


def atomic_write(path, data, mode=0o600):
    path = Path(path)
    private_dir(path.parent)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise Fault(f"Refusing non-file destination: {path}", "blocked")
    if isinstance(data, str):
        data = data.encode()
    fd, tmp = tempfile.mkstemp(prefix=".cwf-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path, data):
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def within(root, relative):
    root = Path(root).resolve()
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts:
        raise Fault("Expected an in-scope relative path", "blocked")
    candidate = root / p
    for part in [candidate, *candidate.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise Fault("Symlink source is excluded", "blocked")
    if not candidate.resolve().is_relative_to(root):
        raise Fault("Path escapes selected scope", "blocked")
    return candidate


def git(root, *args, timeout=10, check=True):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                           timeout=timeout, env=env)
    except FileNotFoundError as exc:
        raise Fault("Git unavailable", "blocked") from exc
    except subprocess.TimeoutExpired as exc:
        raise Fault("Git command timed out", "partial") from exc
    if check and p.returncode:
        raise Fault("Git operation failed", "blocked",
                    p.stderr.decode(errors="replace")[-2000:])
    return p


def scope_info(root):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise Fault("Scope must be an existing directory")
    try:
        probe = git(root, "rev-parse", "--show-toplevel", check=False)
    except Fault as exc:
        if exc.code != "blocked":
            raise
        probe = None
    if probe and probe.returncode == 0:
        top = Path(probe.stdout.decode().strip()).resolve()
        # Explicit subfolder stays the search boundary; Git identity is separate.
        common = git(top, "rev-parse", "--git-common-dir").stdout.decode().strip()
        common = (top / common).resolve()
        head = git(top, "rev-parse", "HEAD", check=False)
        return {"root": str(root), "git_root": str(top), "identity": str(common),
                "worktree": str(top), "head": head.stdout.decode().strip() or None}
    return {"root": str(root), "git_root": None, "identity": str(root),
            "worktree": str(root), "head": None}


def valid_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", value):
        raise Fault("Invalid identifier")
    return value
