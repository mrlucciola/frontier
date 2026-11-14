"""The ticket store: find it, load it, lock it, write it, commit it.

Layout and row format are spec v2 (pm/docs/spec/v2/SPEC.md); this module never
changes them. Verbs read through `open_store` and mutate through `locked_store`.
"""
import contextlib
import fcntl
import hashlib
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone

import gitcommit

STORE_DIR = ".pm"
TICKET_FILE = "tickets.jsonl"
HISTORY_PENDING = "history-pending"
UNBUILT_EXIT = 70
GIT_COMMIT_FAILED_EXIT = 3


class TicketError(Exception):
    """A refusal: the entry prints `pm: <message>` on stderr and exits 1."""


class GitCommitFailed(Exception):
    """The store's own git commit failed; the row is saved. The entry exits 3."""


def unbuilt(name):
    """Mark a verb or call site the rewrite has not built yet (exit 70)."""
    log = os.environ.get("PM_UNBUILT_LOG")
    if log:
        with open(log, "a") as f:
            f.write(name + "\n")
    print(f"pm: '{name}' is not built yet", file=sys.stderr)
    sys.exit(UNBUILT_EXIT)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)


def _worktree_main(gitfile):
    """Main checkout owning the linked worktree whose `.git` file is `gitfile`,
    or None. Its `gitdir:` line points into the main checkout's `.git/worktrees`."""
    try:
        with open(gitfile) as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    gitdir = next((ln[len("gitdir:"):].strip() for ln in lines
                   if ln.startswith("gitdir:")), None)
    if not gitdir:
        return None
    if not os.path.isabs(gitdir):
        gitdir = os.path.join(os.path.dirname(os.path.abspath(gitfile)), gitdir)
    try:
        r = _git(gitdir, "rev-parse", "--git-common-dir")
    except OSError:
        return None
    common = r.stdout.strip()
    if r.returncode != 0 or not common:
        return None
    if not os.path.isabs(common):
        common = os.path.join(gitdir, common)
    return os.path.dirname(os.path.normpath(common))


def find_store(start=None):
    """Walk up from `start` (default cwd) to the nearest `.pm` directory.

    The walk stops at a `.git` directory, so it never reaches a parent repo's
    store. A `.git` file marks a linked worktree, which owns no store: the walk
    goes sideways to the main checkout's.
    """
    d = os.path.abspath(start or os.getcwd())
    while True:
        gitmarker = os.path.join(d, ".git")
        if os.path.isfile(gitmarker):
            main = _worktree_main(gitmarker)
            cand = os.path.join(main, STORE_DIR) if main else None
            return cand if cand and os.path.isdir(cand) else None
        cand = os.path.join(d, STORE_DIR)
        if os.path.isdir(cand):
            return cand
        if os.path.exists(gitmarker) or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def synthesize_tombstone(tid, parent, entry):
    """The closed row a `subtasks` entry on an epic stands for."""
    closed = entry.get("closed")
    row = {"id": tid, "title": entry.get("title"), "kind": "task",
           "status": "closed", "parent": parent,
           "closure_reason": entry.get("reason"), "created": closed,
           "updated": closed, "assignee": None, "body": "", "labels": [],
           "edges": [], "priority": 2, "compacted": True,
           "notes": [{"ts": closed, "text": entry["note"]}]
           if entry.get("note") else []}
    for key in ("findings", "closed_by"):
        if key in entry:
            row[key] = entry[key]
    return row


class Store:
    def __init__(self, root):
        self.root = root
        with open(os.path.join(root, "config.json")) as f:
            self.config = json.load(f)
        version = self.config.get("spec_version")
        if not isinstance(version, int) or version < 2:
            raise TicketError(
                f"{root} is below spec v2 and this pm cannot read it; migrate it "
                "with the old `pm ticket upgrade` in ~/frontier/runtime-tools/pm")
        self.ticket_path = os.path.join(root, TICKET_FILE)
        history_ref = self.config.get("history_ref")
        if history_ref and not os.path.exists(self.ticket_path):
            raise TicketError(
                f"{STORE_DIR}/{TICKET_FILE} is missing but this store keeps history "
                f"on {history_ref}; run: pm ticket history restore")
        self.tickets = []
        self.by_id = {}
        self._archive_index = None
        if os.path.exists(self.ticket_path):
            with open(self.ticket_path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    self.tickets.append(row)
                    if isinstance(row, dict) and isinstance(row.get("id"), str):
                        self.by_id.setdefault(row["id"], row)

    def save(self):
        tmp = self.ticket_path + ".tmp"
        with open(tmp, "w") as f:
            for row in self.tickets:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(tmp, self.ticket_path)

    @property
    def compacted(self):
        """{id: (epic id, subtasks entry)} for every compacted child task."""
        out = {}
        for row in self.tickets:
            subs = row.get("subtasks") if isinstance(row, dict) else None
            for entry in subs if isinstance(subs, list) else []:
                if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                    out.setdefault(entry["id"], (row.get("id"), entry))
        return out

    def archive_index(self):
        """Parsed rows of archive/archive-index.jsonl; none when it is absent."""
        if self._archive_index is None:
            rows = []
            path = os.path.join(self.root, "archive", "archive-index.jsonl")
            if os.path.exists(path):
                with open(path) as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(obj, dict):
                            rows.append(obj)
            self._archive_index = rows
        return self._archive_index

    def archived_ids(self):
        return {r["id"] for r in self.archive_index()
                if r.get("source") == "self" and isinstance(r.get("id"), str)}

    def get(self, tid):
        """The live row for a mutation. A compacted or archived id is refused."""
        row = self.by_id.get(tid)
        if row:
            return row
        if tid in self.compacted:
            parent, entry = self.compacted[tid]
            raise TicketError(
                f"{tid} was compacted into {parent} when it closed "
                f"({entry.get('closed')}); it cannot be changed. File a new ticket.")
        if tid in self.archived_ids():
            raise TicketError(f"{tid} is archived; it cannot be changed. File a new ticket.")
        raise TicketError(f"no such ticket: {tid}")

    def read(self, tid):
        """The row for a read: live, the synthesized closed row of a compacted
        id, or the row of an archived id (plus `archived: true`)."""
        if tid in self.by_id:
            return self.by_id[tid]
        if tid in self.compacted:
            parent, entry = self.compacted[tid]
            return synthesize_tombstone(tid, parent, entry)
        for idx in self.archive_index():
            if idx.get("id") == tid and idx.get("source") == "self":
                return self._read_archived(tid, idx)
        raise TicketError(f"no such ticket: {tid}")

    def _read_archived(self, tid, idx):
        path = idx.get("path")
        meta = idx.get("meta") if isinstance(idx.get("meta"), dict) else {}
        epic = meta.get("compacted_into")
        want = epic if isinstance(epic, str) else tid
        row = None
        full = os.path.join(self.root, "archive", str(path))
        if isinstance(path, str) and os.path.isfile(full):
            with open(full) as f:
                for line in f:
                    if want in line:
                        try:
                            cand = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(cand, dict) and cand.get("id") == want:
                            row = cand
                            break
        if row is not None and isinstance(epic, str):
            entry = next((e for e in row.get("subtasks") or []
                          if isinstance(e, dict) and e.get("id") == tid), None)
            row = synthesize_tombstone(tid, epic, entry) if entry else None
        if row is None:
            raise TicketError(f"{tid} is archived in {path} but that file is not on this machine")
        return dict(row, archived=True, archive_path=path)

    def new_id(self, title):
        seed = (title + now() + os.urandom(8).hex()).encode()
        for n in range(6, 12):
            tid = f"{self.config['prefix']}-{hashlib.sha256(seed).hexdigest()[:n]}"
            if tid not in self.by_id and tid not in self.compacted \
                    and tid not in self.archived_ids():
                return tid
        raise TicketError("could not allocate a unique id")


def _located(repo):
    root = find_store(repo)
    if not root:
        raise TicketError("no ticket store found (run: pm ticket init)")
    return root


def open_store(repo=None):
    """Load the store read-only."""
    return Store(_located(repo))


@contextlib.contextmanager
def locked_store(repo=None, message=None):
    """Lock, load, yield the store, then write and commit.

    An exception skips the write and leaves the store byte-unchanged. `message`
    is a string, or a callable run after the op so it can name minted ids.
    """
    root = _located(repo)
    with open(os.path.join(root, "lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        store = Store(root)
        yield store
        store.save()
        if message:
            commit(root, message() if callable(message) else message)


def commit(root, message):
    """Record the saved store in git; the row is saved either way.

    A policy skip prints one stderr line and the by-hand command, and returns. A
    git failure prints the same plus git's own output, then raises
    GitCommitFailed (exit 3); on a `history_ref` store it only marks the snapshot
    owed, so the next write catches up.
    """
    skipped = gitcommit.commit_store(root, message)
    if not skipped:
        with contextlib.suppress(OSError):
            os.remove(os.path.join(root, HISTORY_PENDING))
        return
    print(f"pm: store saved, commit skipped: {skipped}", file=sys.stderr)
    fault = isinstance(skipped, gitcommit.GitFault)
    if fault and skipped.stderr_tail:
        print(skipped.stderr_tail, file=sys.stderr)
    repo = os.path.dirname(os.path.abspath(root))
    rel = os.path.join(os.path.basename(root), TICKET_FILE)
    ref = _history_ref(root)
    if ref:
        print(f"pm: the row above is saved but NOT yet recorded on {ref}; the next "
              "pm write or summary that can commit records it, or run: "
              "pm ticket history sync", file=sys.stderr)
        if fault:
            with contextlib.suppress(OSError), \
                    open(os.path.join(root, HISTORY_PENDING), "w") as f:
                f.write(f"{skipped}\n")
        return
    print("pm: the row above is saved but NOT committed; commit it by hand: "
          f"git -C {shlex.quote(repo)} add -- {shlex.quote(rel)} && git -C "
          f"{shlex.quote(repo)} commit -q -o -m {shlex.quote(message)} -- "
          f"{shlex.quote(rel)}", file=sys.stderr)
    if fault:
        raise GitCommitFailed(skipped)


def _history_ref(root):
    try:
        with open(os.path.join(root, "config.json")) as f:
            return json.load(f).get("history_ref")
    except (OSError, ValueError):
        return None
