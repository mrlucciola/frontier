"""pm ticket archive: move closed rows to archive/tickets-<yyyy>.jsonl."""
import json
import os
from datetime import datetime

import gitcommit
import store as st
from store import TicketError

INDEX_REL = os.path.join(st.STORE_DIR, "archive", "archive-index.jsonl")


def register(subparsers):
    sp = subparsers.add_parser(
        "archive", help="move closed rows to archive/tickets-<yyyy>.jsonl")
    sp.add_argument("ids", nargs="*", metavar="id", help="closed tickets to archive")
    sp.add_argument("--closed-before", metavar="YYYY-MM-DD",
                    help="optional filter: only rows last updated before this date "
                         "(alone, selects every such closed row)")
    sp.add_argument("--dry-run", action="store_true")


def year_filename(year):
    return f"tickets-{year}.jsonl"


def closed_before(tickets, cutoff_date):
    return [t for t in tickets
            if t.get("status") == "closed" and t.get("updated", "")[:10] < cutoff_date]


def live_children(store, moving):
    """{parent id: [live child ids]} for parents in `moving` that a row staying
    live still names as `parent`."""
    blocked = {}
    for t in store.tickets:
        if not isinstance(t, dict):
            continue
        p = t.get("parent")
        if p in moving and t.get("id") not in moving:
            blocked.setdefault(p, []).append(t.get("id"))
    return blocked


def fixed_point(store, rows, on_skip):
    """`rows` without every row a live row still names as `parent`, to a fixed
    point (dropping a parent can strand its own parent)."""
    while True:
        blocked = live_children(store, {t["id"] for t in rows})
        if not blocked:
            return rows
        on_skip(blocked)
        rows = [t for t in rows if t["id"] not in blocked]


def parent_reason(pid, kids):
    return (f"is parent of live {', '.join(sorted(kids))}; "
            "reparent or archive them together")


def select(store, ids, cutoff_date):
    """Rows to archive: the named ids (each closed, and before the cutoff when
    one is given), or every closed row before the cutoff. Any bad id refuses
    the whole call."""
    if not ids and not cutoff_date:
        raise TicketError(
            "archive needs ticket ids, or --closed-before YYYY-MM-DD to select by date")
    if not ids:
        def report(blocked):
            for pid, kids in sorted(blocked.items()):
                print(f"skipped {pid}: {parent_reason(pid, kids)}")
        return fixed_point(store, closed_before(store.tickets, cutoff_date), report)
    in_cutoff = ({t["id"] for t in closed_before(store.tickets, cutoff_date)}
                 if cutoff_date else None)
    rows, bad, seen = [], [], set()
    for raw in ids:
        tid = st.local_id(raw)
        if tid in seen:
            continue
        seen.add(tid)
        t = store.by_id.get(tid)
        if t is None and tid in store.compacted:
            store.get(tid)
        if t is None and tid in store.archived_ids():
            bad.append(f"{raw}: already archived")
        elif t is None:
            bad.append(f"{raw}: unknown ticket")
        elif t.get("status") != "closed":
            bad.append(f"{tid} is {t.get('status')}, not closed; "
                       f"run `pm ticket close {tid}` first")
        elif in_cutoff is not None and tid not in in_cutoff:
            bad.append(f"{tid} was updated {t.get('updated', '')[:10]}, "
                       f"not before {cutoff_date}")
        else:
            rows.append(t)
    if not bad:
        blocked = live_children(store, {t["id"] for t in rows})
        bad = [f"{pid} {parent_reason(pid, kids)}" for pid, kids in sorted(blocked.items())]
    if bad:
        raise TicketError("; ".join(bad) + "; nothing archived")
    return rows


def move(store, to_move):
    """Append `to_move` to the year files and the index, then drop it from the
    live rows. The year file is appended to, never rewritten; an epic's
    `subtasks` entries get their own index rows. A row the index already holds
    (a save that failed after the appends) is only dropped from the live rows."""
    archive_dir = os.path.join(store.root, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    store._archive_index = None
    done = store.archived_ids()
    moved_ids = {t["id"] for t in to_move}
    fresh = [t for t in to_move if t["id"] not in done]
    by_year = {}
    for t in fresh:
        by_year.setdefault(t["updated"][:4], []).append(t)
    for year, rows in sorted(by_year.items()):
        path = os.path.join(archive_dir, year_filename(year))
        lead = ""
        if os.path.exists(path) and os.path.getsize(path):
            with open(path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                lead = "" if f.read(1) == b"\n" else "\n"
        with open(path, "a") as f:
            f.write(lead)
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    archived_at = st.now()
    with open(os.path.join(archive_dir, "archive-index.jsonl"), "a") as f:
        for t in sorted(fresh, key=lambda t: t["id"]):
            path = year_filename(t["updated"][:4])
            row = {"id": t["id"], "title": t["title"], "source": "self",
                   "closed": t.get("updated"), "path": path,
                   "archived": archived_at, "meta": {}}
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            for e in t.get("subtasks") or []:
                sub = {"id": e["id"], "title": e.get("title"), "source": "self",
                       "closed": e.get("closed"), "path": path,
                       "archived": archived_at,
                       "meta": {"compacted_into": t["id"]}}
                f.write(json.dumps(sub, ensure_ascii=False, sort_keys=True) + "\n")

    store.tickets = [t for t in store.tickets
                     if not (isinstance(t, dict) and t.get("id") in moved_ids)]
    store.by_id = {t["id"]: t for t in store.tickets
                   if isinstance(t, dict) and isinstance(t.get("id"), str)}
    store._archive_index = None


def index_is_ignored(store):
    """True when git ignores the index (or the store is not in a checkout), so
    it cannot ride on the ticket file's commit."""
    repo_dir = os.path.dirname(os.path.abspath(store.root))
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        return True
    try:
        return gitcommit.git(repo_dir, "check-ignore", "-q", "--", INDEX_REL).returncode == 0
    except Exception:
        return True


def show_plan(rows, apply):
    if not rows:
        print("pm ticket archive: nothing to archive")
        return
    for t in sorted(rows, key=lambda t: t["id"]):
        print(f"archived {t['id']}" if apply
              else f"would archive {t['id']} (updated {t['updated']})")


def run(args):
    if args.dry_run:
        store = st.open_store(args.repo)
        show_plan(select(store, args.ids, args.closed_before), apply=False)
        return
    moved = []
    with st.locked_store(args.repo,
                         message=lambda: f"pm: archive {len(moved)}") as store:
        rows = select(store, args.ids, args.closed_before)
        moved.extend(rows)
        if rows:
            move(store, rows)
            if not index_is_ignored(store):
                store.extra_commit_paths.append(INDEX_REL)
        show_plan(rows, apply=True)
