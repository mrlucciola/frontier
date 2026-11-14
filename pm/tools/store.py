"""The ticket store: find it, load it, lock it, write it, commit it.

Layout and row format are spec v2 (pm/docs/spec/v2/SPEC.md); this module never
changes them. Verbs read through `open_store` and mutate through `locked_store`.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import shlex
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

import gitcommit

STORE_DIR = ".pm"
TICKET_FILE = "tickets.jsonl"
NO_SUCH_TICKET_HINT = ("`pm ticket list` shows this store's ids, "
                       "`pm ticket create` files a new one")
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
        r = gitcommit._git(gitdir, "rev-parse", "--git-common-dir")
    except (OSError, subprocess.TimeoutExpired):
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
        self.rows = []
        self.by_id = {}
        self.extra_commit_paths = []
        self._archive_index = None
        self.cross_cache = {"targets": {}, "stores": {}, "ctx": {}}
        if os.path.exists(self.ticket_path):
            with open(self.ticket_path) as f:
                for lineno, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    self.rows.append((lineno, row))
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
        raise TicketError(f"no such ticket: {tid}; {NO_SUCH_TICKET_HINT}")

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
        raise TicketError(f"no such ticket: {tid}; {NO_SUCH_TICKET_HINT}")

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

    def blockers_of(self, tid):
        """Rows carrying a blocks-edge to `tid`."""
        return [t for t in self.tickets
                if any(e["type"] == "blocks" and e["to"] == tid for e in t["edges"])]

    def children(self, tid):
        return [t for t in self.tickets if t.get("parent") == tid]

    def walk(self, start, step):
        """Ids reached transitively from `start` by `step(id) -> [id]`, in
        discovery order, each once. Its own visited set ends a parent cycle."""
        seen, order, stack = set(), [], [start]
        while stack:
            for nxt in step(stack.pop()):
                if nxt not in seen:
                    seen.add(nxt)
                    order.append(nxt)
                    stack.append(nxt)
        return order

    def subtree(self, tid):
        """Ids under `tid` by parent edges, in discovery order."""
        return self.walk(tid, lambda i: [c["id"] for c in self.children(i)])

    def is_ready(self, t):
        import routing
        return (t["kind"] == "task" and t["status"] == "open"
                and all(b["status"] == "closed" for b in self.blockers_of(t["id"]))
                and not routing.unsatisfied_cross(self, t))


TITLE_MAX = 200
LABEL_MAX = 80
ID_RE = re.compile(r"^[a-z][a-z0-9]{1,7}-[0-9a-f]{6,11}$")
LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9:_./-]*$")


def priority_type(raw):
    """argparse type: 0-4 or P0-P4, case-insensitive."""
    s = raw[1:] if raw and raw[0] in "Pp" else raw
    try:
        n = int(s)
    except ValueError:
        n = -1
    if n not in range(5):
        raise argparse.ArgumentTypeError(
            f"invalid priority: {raw!r} (expected 0-4 or P0-P4)")
    return n


def would_cycle(store, src, dst):
    """True if adding src --blocks--> dst creates a blocks-cycle."""
    seen, stack = set(), [dst]
    while stack:
        cur = stack.pop()
        if cur == src:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        row = store.by_id.get(cur)
        if row is None and (cur in store.archived_ids() or cur in store.compacted):
            continue
        stack.extend(e["to"] for e in (row or store.get(cur))["edges"]
                     if e["type"] == "blocks")
    return False


def title_problem(title):
    """Why `title` is not a valid row title, else None."""
    if title == "" or "\n" in title or "\r" in title:
        return "title must be a non-empty single line"
    if len(title) > TITLE_MAX:
        return f"title is {len(title)} chars; the limit is {TITLE_MAX}"
    return None


def label_problem(label):
    """Why `label` is not a valid row label, else None."""
    if not isinstance(label, str):
        return f"label {label!r} is not a string"
    if not LABEL_RE.match(label):
        return f"label {label!r} does not match {LABEL_RE.pattern}"
    if len(label) > LABEL_MAX:
        return f"label {label!r} is {len(label)} chars; the limit is {LABEL_MAX}"
    return None


def make_note(text, kind=None, ts=None):
    """A note row; `kind` is omitted when None."""
    note = {"ts": ts or now(), "text": text}
    if kind:
        note["kind"] = kind
    return note


def session_token(explicit=None):
    """First 8 hex of sha256 of the session id (explicit, PM_SESSION_ID, then
    CLAUDE_CODE_SESSION_ID), or None when there is none."""
    sid = explicit or os.environ.get("PM_SESSION_ID") \
        or os.environ.get("CLAUDE_CODE_SESSION_ID")
    return hashlib.sha256(sid.encode()).hexdigest()[:8] if sid else None


def _agent_provider():
    pm_agent = os.environ.get("PM_AGENT")
    if pm_agent:
        return pm_agent.partition("/")[0] or None
    if os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("CODEX_AGENT_IDENTITY"):
        return "codex"
    return None


def session_assignee(name, explicit=None):
    """`agent:<provider>/<name>#<token>` when a provider and a session id are
    known, else `human:<name>` (spec v2 section 4)."""
    tok = session_token(explicit)
    provider = _agent_provider()
    if provider and tok:
        return f"agent:{provider}/{name}#{tok}"
    return f"human:{name}"


def owned_prefixes(config):
    out = []
    if isinstance(config.get("prefix"), str):
        out.append(config["prefix"])
    legacy = config.get("legacy_prefixes")
    if isinstance(legacy, list):
        out += [p for p in legacy if isinstance(p, str) and p not in out]
    return out


def ref_prefix(ref):
    """Prefix of `lin-559399` or `lin/lin-559399`; None when neither shape."""
    head, sep, _ = ref.partition("/")
    if sep:
        return head or None
    head, sep, _ = ref.partition("-")
    return head if sep and head else None


def local_id(ref):
    """`<prefix>/<id>` -> `<id>`; a bare id is returned unchanged."""
    if ":" in ref:
        head, _, tid = ref.partition(":")
        raise TicketError(
            f"{ref!r}: write a cross-store id as <prefix>/<id> "
            f"({head}/{tid}), not <prefix>:<id>")
    head, sep, tid = ref.partition("/")
    if not sep:
        return ref
    if not head or ref_prefix(tid) != head:
        raise TicketError(
            f"{ref!r}: the part before '/' must be the id's own prefix "
            f"(expected '{ref_prefix(tid) or '<prefix>'}/{tid}')")
    return tid


def is_remote_ref(store, raw):
    """True when `raw` names a row outside `store`: a prefix the store does not
    own, or a legacy prefix whose row the store does not hold."""
    tid = local_id(raw)
    pfx = ref_prefix(tid)
    if not pfx:
        return False
    if pfx not in owned_prefixes(store.config):
        return True
    return pfx != store.config.get("prefix") and tid not in store.by_id


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
    import routing
    root = _located(repo)
    routing.refuse_if_frozen(root)
    with open(os.path.join(root, "lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        store = Store(root)
        yield store
        store.save()
        if message:
            commit(root, message() if callable(message) else message, repo,
                   store.extra_commit_paths)


def each_id(args):
    """The bulk ids of a verb, deduped with order kept: a repeated id is one
    ticket, so it takes one transition and one note."""
    return list(dict.fromkeys(args.id))


@contextlib.contextmanager
def locked_verb(args, cmd):
    """`locked_store` for an id-taking verb; the commit subject is
    `pm: <cmd> <ids>`, cut at 120 characters."""
    ids = args.id if isinstance(args.id, list) else [args.id]
    subject = " ".join(["pm:", cmd, *dict.fromkeys(ids)])[:120]
    with locked_store(getattr(args, "repo", None), subject) as store:
        yield store


HOLD_STALE_SECONDS = 12 * 3600


def hold_state_dir():
    return os.environ.get("PM_HOLD_STATE_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude", ".tmp", "pm-holds")


def touch_session_seen(token):
    """Heartbeat for a session token; best effort, never raises."""
    path = os.path.join(hold_state_dir(), f"{token}.seen")
    try:
        os.makedirs(hold_state_dir(), exist_ok=True)
        with open(path, "a"):
            pass
        os.utime(path, None)
    except OSError:
        pass


def hold_is_stale(hold):
    """True when the holding session's token has no recent heartbeat."""
    stale_after = float(os.environ.get("PM_HOLD_STALE_SECONDS") or HOLD_STALE_SECONDS)
    try:
        mtime = os.path.getmtime(os.path.join(hold_state_dir(), f"{hold['token']}.seen"))
    except (OSError, KeyError, TypeError):
        return True
    return (time.time() - mtime) > stale_after


def split_assignee(assignee):
    """(provider, base, token) of an assignee string of any shape: `human:<name>`,
    `legacy:<name>[#tok]`, `agent:<provider>/<name>#<tok>`, or a bare name."""
    def base_tok(s):
        if "#" in s:
            base, _, tok = s.rpartition("#")
            return base, tok
        return s, None
    if assignee is None:
        return None, None, None
    if assignee.startswith("human:"):
        return "human", assignee[len("human:"):], None
    if assignee.startswith("legacy:"):
        base, tok = base_tok(assignee[len("legacy:"):])
        return None, base, tok
    if assignee.startswith("agent:"):
        provider, _, rest = assignee[len("agent:"):].partition("/")
        base, tok = base_tok(rest)
        return provider, base, tok
    base, tok = base_tok(assignee)
    return None, base, tok


def hold_marker(reason, explicit_session):
    """The in-flight marker `{token, reason, since}` of the acting session, or
    TicketError; the token tells the Stop hook whose hold it is."""
    if not reason or not reason.strip():
        raise TicketError("hold needs a non-empty reason")
    tok = session_token(explicit_session)
    if not tok:
        raise TicketError("hold needs a session id (--session, PM_SESSION_ID or "
                          "CLAUDE_CODE_SESSION_ID)")
    touch_session_seen(tok)
    return {"token": tok, "reason": reason.strip(), "since": now()}


def fmt_line(t):
    flags = []
    if t["assignee"]:
        flags.append(f"@{t['assignee']}")
    if t.get("hold"):
        flags.append("held")
    if t["kind"] == "epic":
        flags.append("epic")
    tail = f" [{' '.join(flags)}]" if flags else ""
    return f"{t['id']}  P{t['priority']}  {t['status']:<13} {t['title']}{tail}"


def claim_veto(t, reopen=False):
    """Why `t` may not be claimed, ignoring readiness, else None. One rule set for
    `claim` and `create --claim-as`, so a write cannot produce a claimed epic.
    `reopen` lets `claim --reopen` take a done-unmerged ticket back."""
    if t["kind"] == "epic":
        return "epics aggregate work and cannot be claimed; claim a child task"
    if t["status"] == "claimed":
        return (f"already claimed by {t['assignee']}; "
                f"`pm ticket release {t['id']}` first if the claim is yours to drop")
    if t["status"] == "done-unmerged" and reopen:
        return None
    if t["status"] == "done-unmerged":
        return (f"cannot claim a done-unmerged ticket; resume it with "
                f"`pm ticket claim {t['id']} --as <name> --reopen` (or `wt start {t['id']}`)")
    if t["status"] != "open":
        return f"cannot claim a {t['status']} ticket; {status_hint(t)}"
    return None


def status_hint(t):
    """The verb that moves `t` on from its status, for a refusal's tail."""
    tid = t.get("id", "<id>")
    if t["status"] == "open":
        return f"`pm ticket claim {tid} --as <name>` takes it"
    if t["status"] == "claimed":
        return f"`pm ticket release {tid}` gives the claim up"
    return f"`pm ticket reopen {tid}` reopens it"


def refuse_if_unclaimed(t):
    """`release`'s status refusal; `where --mutate --verb release` shares it."""
    if t["status"] != "claimed" and t["assignee"] is None:
        raise TicketError(f"not claimed (status: {t['status']}); {status_hint(t)}")


def refuse_if_closed(t):
    """`close`'s status refusal; `where --mutate --verb close` shares it."""
    if t["status"] == "closed":
        raise TicketError(f"already closed; {status_hint(t)}")


def close_open_children(store, t, force, detach):
    """`close`'s epic guard: the open children to reparent when `detach`, [] when
    none or `force`; refuses when there are open children and neither flag is
    given. `where --mutate` shares it."""
    if t["kind"] != "epic" or force:
        return []
    open_children = [c for c in store.children(t["id"])
                     if c["status"] not in ("closed", "done-unmerged")]
    if open_children and not detach:
        lines = "\n".join(f"  {c['id']}  {c['status']}  {c['title']}"
                          for c in open_children)
        raise TicketError(
            f"{t['id']} has open children:\n{lines}\n"
            "close them first, or pass --detach to reparent them to "
            "(none), or --force to close anyway")
    return open_children


def parse_findings(raw, store):
    """`--findings none|<id>[,<id>...]` -> ["none"] or the deduped bare id list.

    An id whose prefix this store owns must be a row of this store; any other id,
    bare or `<prefix>/<id>`, is routed read-only through `routing.resolve_store`
    and must be a row there."""
    import routing
    items = [s.strip() for s in raw.split(",")]
    if not all(items):
        raise TicketError(f"--findings {raw!r}: empty entry; use none or id[,id...]")
    if "none" in items:
        if items != ["none"]:
            raise TicketError("--findings: 'none' cannot be combined with ticket ids")
        return ["none"]
    items = list(dict.fromkeys(items))
    owned = owned_prefixes(store.config)
    repo = os.path.dirname(os.path.abspath(store.root))
    unknown, bare = [], []
    archived = store.archived_ids()
    for i in items:
        if i in store.by_id or i in store.compacted or i in archived:
            bare.append(i)
            continue
        try:
            tid = local_id(i)
            if ref_prefix(i) in owned:
                if (tid not in store.by_id and tid not in store.compacted
                        and tid not in archived):
                    unknown.append(i)
                bare.append(tid)
                continue
            r = routing.resolve_store(i, None, repo, read=True,
                                      _ctx=store.cross_cache["ctx"])
            foreign = store.cross_cache["stores"]
            key = os.path.realpath(r.root)
            other = foreign.get(key)
            if other is None:
                other = foreign[key] = Store(r.root)
        except (TicketError, OSError, ValueError) as e:
            raise TicketError(f"--findings: {i}: {e}")
        if tid not in other.by_id:
            raise TicketError(f"--findings: no ticket {tid} in store {r.repo} (from {i})")
        bare.append(tid)
    if unknown:
        raise TicketError(f"--findings: unknown ticket id(s) in {store.config['prefix']} "
                          f"store: {', '.join(unknown)}")
    return list(dict.fromkeys(bare))


def edge_target(store, raw, edge_type=None):
    """Stored `to` for an edge to `raw` in this store: the bare id for a row this
    store holds, else `<prefix>/<id>` once the target resolves read-only. A
    discovered-from edge may name a compacted or archived id of this store."""
    import routing
    tid = local_id(raw)
    pfx = ref_prefix(tid)
    if pfx is not None and is_remote_ref(store, raw):
        ref = f"{pfx}/{tid}"
        if not ID_RE.match(tid):
            raise TicketError(f"no such ticket: {tid}; {NO_SUCH_TICKET_HINT}")
        reason = routing.cross_target(store, ref)["reason"]
        if reason:
            raise TicketError(
                f"cannot add an edge to {ref}: {reason}; check the registry with "
                "`pm ticket stores` (source: runtime-tools/pm/stores.json)")
        return ref
    if (edge_type == "discovered-from" and tid not in store.by_id
            and (tid in store.compacted or tid in store.archived_ids())):
        return tid
    store.get(tid)
    return tid


def commit(root, message, repo=None, extra_paths=()):
    """Record the saved store in git; the row is saved either way.
    `repo` is the store the caller named (`--store`/`--repo`), if any.

    A policy skip prints one stderr line and the by-hand command, and returns. A
    git failure prints the same plus git's own output, then raises
    GitCommitFailed (exit 3); on a `history_ref` store it only marks the snapshot
    owed, so the next write catches up.
    """
    skipped = gitcommit.commit_store(root, message, extra_paths=extra_paths)
    if not skipped:
        with contextlib.suppress(OSError):
            os.remove(os.path.join(root, HISTORY_PENDING))
        return
    print(f"pm: store saved, commit skipped: {skipped}", file=sys.stderr)
    fault = isinstance(skipped, gitcommit.GitFault)
    if fault and skipped.stderr_tail:
        print(skipped.stderr_tail, file=sys.stderr)
    repo_dir = os.path.dirname(os.path.abspath(root))
    rel = os.path.join(os.path.basename(root), TICKET_FILE)
    ref = _history_ref(root)
    if ref:
        by_hand = "pm ticket history sync"
        if repo is not None:
            by_hand += f" --repo {shlex.quote(repo_dir)}"
        print(f"pm: the row above is saved but NOT yet recorded on {ref}; the next "
              "pm write or summary that can commit records it, or run: "
              f"{by_hand}", file=sys.stderr)
        if fault:
            with contextlib.suppress(OSError), \
                    open(os.path.join(root, HISTORY_PENDING), "w") as f:
                f.write(f"{skipped}\n")
        return
    print("pm: the row above is saved but NOT committed; commit it by hand: "
          f"git -C {shlex.quote(repo_dir)} add -- {shlex.quote(rel)} && git -C "
          f"{shlex.quote(repo_dir)} commit -q -o -m {shlex.quote(message)} -- "
          f"{shlex.quote(rel)}", file=sys.stderr)
    if fault:
        raise GitCommitFailed(skipped)


def _history_ref(root):
    try:
        with open(os.path.join(root, "config.json")) as f:
            return json.load(f).get("history_ref")
    except (OSError, ValueError):
        return None
