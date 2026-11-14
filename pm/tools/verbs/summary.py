"""pm ticket summary: the session-start briefing. Reads only; never writes."""
import contextlib
import fcntl
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone

import gitcommit
import routing
import store as st

PILOT_LABEL = "pilot"
REVIEW_BY_RE = re.compile(r"^\s*review_by:[ \t]*(\S*)", re.M)
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def register(subparsers):
    sp = subparsers.add_parser("summary", help="session-start briefing")
    sp.add_argument("--limit", type=int, default=5)
    sp.add_argument("--json", action="store_true")


def review_by(body):
    """The date of the first `review_by:` body line, else None."""
    m = REVIEW_BY_RE.search(str(body or ""))
    if not m or not ISO_DATE_RE.match(m.group(1)):
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def overdue_pilots(store):
    """Ids of open `pilot` tickets whose `review_by:` date is past."""
    today = datetime.now(timezone.utc).date()
    out = []
    for t in store.tickets:
        if not isinstance(t, dict) or PILOT_LABEL not in (t.get("labels") or []) \
                or t.get("status") == "closed":
            continue
        due = review_by(t.get("body"))
        if due is not None and due < today:
            out.append(t.get("id"))
    return out


def archive_hint(store):
    size = os.path.getsize(store.ticket_path) if os.path.exists(store.ticket_path) else 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    reasons = []
    if size > 1_000_000:
        reasons.append(f"{os.path.basename(store.ticket_path)} is {size} bytes (> 1 MB)")
    if any(t.get("status") == "closed" and t.get("updated", "") < cutoff
           for t in store.tickets):
        reasons.append("closed rows older than 90 days")
    if not reasons:
        return None
    return "hint: " + "; ".join(reasons) + " -- consider `pm ticket archive <id> [<id> ...]`"


def history_behind(repo_dir, rel, ref):
    """True when the working file's blob is not the one at the tip of `ref`."""
    entry = os.path.basename(rel)
    work = None
    if os.path.exists(os.path.join(repo_dir, rel)):
        r = gitcommit.git(repo_dir, "hash-object", "--no-filters", "--", rel)
        if r.returncode == 0:
            work = r.stdout.strip()
    r = gitcommit.git(repo_dir, "rev-parse", "-q", "--verify", f"refs/heads/{ref}:{entry}")
    tip = r.stdout.strip() if r.returncode == 0 else None
    return work is not None and work != tip


def store_dirty_line(store):
    """One line when the ticket file is uncommitted in the repo that owns the
    store (a skipped commit made visible), or when history is owed or behind.
    None for a non-repo store, a git failure or a timeout."""
    repo_dir = os.path.dirname(os.path.abspath(store.root))
    rel = os.path.join(os.path.basename(store.root), os.path.basename(store.ticket_path))
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        return None
    ref = store.config.get("history_ref")
    if ref:
        if os.path.exists(os.path.join(store.root, st.HISTORY_PENDING)):
            with open(os.path.join(store.root, "lock"), "w") as lk:
                fcntl.flock(lk, fcntl.LOCK_EX)
                failed = gitcommit.commit_store(store.root, "pm: history sync")
                if not failed:
                    with contextlib.suppress(OSError):
                        os.remove(os.path.join(store.root, st.HISTORY_PENDING))
            if failed:
                return ("note: ticket history is pending (a snapshot to "
                        f"{ref} failed); retried on "
                        "every write and summary, or run: pm ticket history sync")
        try:
            behind = history_behind(repo_dir, rel, ref)
        except (OSError, subprocess.SubprocessError):
            return None
        return ("note: ticket history is behind the working file; "
                "run: pm ticket history sync") if behind else None
    try:
        r = gitcommit.git(repo_dir, "status", "--porcelain", "--", rel, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    # An untracked ('??') store is a fresh init no op has committed yet, not a skip.
    if not any(line[:2] != "??" for line in r.stdout.splitlines() if line):
        return None
    return (f"note: {rel} has uncommitted changes in {repo_dir} -- the last "
            f"store commit was skipped (see stderr); the next op on the "
            f"default branch sweeps it in")


def run(args):
    store = st.open_store(args.repo)
    active = [t for t in store.tickets if t["status"] != "closed"]
    ready = sorted((t for t in store.tickets
                    if store.is_ready(t) and t["priority"] != 4),
                   key=lambda t: (t["priority"], t["created"]))
    obj = {
        "semaphores": [t for t in active
                       if t["priority"] == 0 or "semaphore" in t["labels"]],
        "claimed": [t for t in active if t["status"] == "claimed"],
        "unmerged": [t for t in active if t["status"] == "done-unmerged"],
        "ready": ready[:args.limit],
        "open_total": len(active),
    }
    if args.json:
        print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
        return
    notice = routing.frozen_notice(store.root)
    if notice:
        print(notice)
        return
    stale = [t for t in obj["claimed"] if t.get("hold") and st.hold_is_stale(t["hold"])]
    lines = [f"ticket store: {obj['open_total']} active tickets"]
    for label, ts in (("SEMAPHORES (read before starting work)", obj["semaphores"]),
                      ("in-flight (claimed)", obj["claimed"]),
                      ("stale holds (holding session gone; release or re-hold)", stale),
                      ("done-unmerged (blocked merges)", obj["unmerged"]),
                      (f"ready (top {args.limit})", obj["ready"])):
        if ts:
            lines.append(f"{label}:")
            lines.extend(f"  {st.fmt_line(t)}" for t in ts)
    waiting = []
    for t in sorted(store.tickets, key=lambda r: (r["priority"], r["created"])):
        if t["status"] != "closed":
            pending = routing.unsatisfied_cross(store, t)
            if pending:
                waiting.append(f"  {t['id']} <- "
                               + ", ".join(routing.cross_label(b) for b in pending))
    if waiting:
        lines.append("waiting on other stores:")
        lines.extend(waiting)
    overdue = overdue_pilots(store)
    if overdue:
        lines.append("pilots overdue: " + ", ".join(overdue))
    hint = archive_hint(store)
    if hint:
        lines.append(hint)
    dirty = store_dirty_line(store)
    if dirty:
        lines.append(dirty)
    print("\n".join(lines))
