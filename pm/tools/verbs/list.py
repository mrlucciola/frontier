"""pm ticket list: tickets by priority, optionally filtered or across stores."""
import json
import sys

import routing
import store as st
from store import TicketError

STATUSES = ("open", "claimed", "done-unmerged", "closed")


def register(subparsers):
    sp = subparsers.add_parser("list", help="list tickets")
    sp.add_argument("--status", action="append", choices=STATUSES)
    sp.add_argument("--label")
    sp.add_argument("--all-stores", action="store_true",
                    help="list every live registered store (rows gain a 'store' field)")
    sp.add_argument("--json", action="store_true")


def rows_of(store, status, label):
    ts = store.tickets
    if status:
        ts = [t for t in ts if t["status"] in status]
    if label:
        ts = [t for t in ts if label in t["labels"]]
    return sorted(ts, key=lambda t: (t["priority"], t["created"]))


def all_store_rows(status, label):
    """Rows of every live registered store, each tagged with its repo root in
    `store`. Frozen and unreadable stores are named on stderr and left out."""
    rows = []
    for e in routing.load_registry():
        if e["role"] == "frozen":
            print(f"skipped {e['path']}: frozen", file=sys.stderr)
            continue
        if e["error"]:
            print(f"skipped {e['path']}: {e['error']}", file=sys.stderr)
            continue
        try:
            store = st.open_store(e["path"])
        except (TicketError, OSError, ValueError) as ex:
            print(f"skipped {e['path']}: {ex}", file=sys.stderr)
            continue
        rows += [dict(t, store=e["path"]) for t in rows_of(store, status, label)]
    return rows


def run(args):
    if args.all_stores:
        ts = all_store_rows(args.status, args.label)
    else:
        ts = rows_of(st.open_store(getattr(args, "repo", None)), args.status, args.label)
    if args.json:
        print(json.dumps(ts, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("\n".join(st.fmt_line(t) for t in ts) or "no tickets")
