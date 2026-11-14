"""pm ticket ready: unblocked, unclaimed tasks by priority."""
import json

import routing
import store as st
from store import TicketError


def register(subparsers):
    sp = subparsers.add_parser("ready", help="unblocked, unclaimed tasks by priority")
    sp.add_argument("--scope", metavar="EPIC|LABEL",
                    help="only rows in this epic's subtree, or carrying this label "
                         "(a scope that is neither is an error, not an empty list)")
    sp.add_argument("--limit", type=int, metavar="N",
                    help="at most N rows (the lowest-priority tail is cut)")
    sp.add_argument("--json", action="store_true")


def scope_filter(store, scope):
    """An existing ticket id scopes to that ticket's subtree (the root itself
    excluded); anything else is a label every kept row must carry. A scope that
    is neither is an error, so a typo never reads as an empty queue."""
    try:
        ref = st.local_id(scope)
    except TicketError:
        ref = scope
    if ref in store.by_id:
        ids = set(store.subtree(ref))
        return lambda t: t["id"] in ids
    if not any(scope in (t.get("labels") or []) for t in store.tickets):
        raise TicketError(f"--scope {scope!r} is neither a ticket id in this store "
                          "nor a label any row carries")
    return lambda t: scope in t["labels"]


def run(args):
    store = st.open_store(getattr(args, "repo", None))
    if args.limit is not None and args.limit < 1:
        raise TicketError("--limit must be at least 1")
    keep = scope_filter(store, args.scope) if args.scope else (lambda t: True)
    rows = sorted((t for t in store.tickets if store.is_ready(t) and keep(t)),
                  key=lambda t: (t["priority"], t["created"]))
    if args.limit is not None:
        rows = rows[:args.limit]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(routing.frozen_notice(store.root)
          or "\n".join(st.fmt_line(t) for t in rows) or "nothing ready")
