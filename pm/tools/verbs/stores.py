"""pm ticket stores: list the store registry; --check reports its problems."""
import os
import sys

import routing
import store as st
from store import TicketError


def register(subparsers):
    sp = subparsers.add_parser("stores", help="list the store registry")
    sp.add_argument("--check", action="store_true",
                    help="report a bad registry, missing paths, bad configs, "
                         "unreadable tickets, rows with a foreign prefix, "
                         "dangling cross-store edges, cross-store blocks edges "
                         "held on the blocker, and live or frozen-only prefix "
                         "collisions (exit 2 on any)")


def run(args):
    try:
        entries = routing.load_registry()
    except TicketError as e:
        if not args.check:
            raise
        print(f"problem: {e}")
        sys.exit(2)
    problems = []
    for e in entries:
        prefixes = st.owned_prefixes(e["config"]) if e["config"] else []
        shown = ",".join(prefixes) if prefixes else "-"
        print(f"{e['path']}  {shown}  {e['role']}"
              + (f"  ERROR: {e['error']}" if e["error"] else ""))
        if args.check:
            problems.extend(_entry_problems(e, prefixes))
    if not args.check:
        return
    for pfx, owners in sorted(routing.owners_by_prefix(entries).items()):
        live, frozen = owners["live"], owners["frozen"]
        if len(live) > 1:
            problems.append(f"live prefix '{pfx}' is owned by "
                            f"{', '.join(o['path'] for o in live)}")
        if not live and len(frozen) > 1:
            problems.append(f"frozen prefix '{pfx}' is owned by "
                            f"{', '.join(o['path'] for o in frozen)} and no live store")
    if problems:
        for msg in problems:
            print(f"problem: {msg}")
        sys.exit(2)
    print(f"OK: {len(entries)} stores")


def _entry_problems(e, prefixes):
    out = []
    succ = e["successor"]
    if succ is not None:
        if e["role"] != "frozen":
            out.append(f"{e['path']}: successor is only meaningful on a frozen store")
        if not isinstance(succ, str) or not succ:
            out.append(f"{e['path']}: successor must be a non-empty string path")
        elif not os.path.isdir(os.path.expanduser(succ)):
            out.append(f"{e['path']}: successor {succ} is not a directory")
    if e["error"]:
        out.append(e["error"])
        return out
    try:
        store = st.Store(e["store"])
        rows = store.tickets
    except (TicketError, OSError, ValueError) as ex:
        out.append(f"cannot read tickets of {e['path']}: {ex}")
        return out
    for t in rows:
        tid = t.get("id") if isinstance(t, dict) else None
        if not isinstance(tid, str) or st.ref_prefix(tid) not in prefixes:
            out.append(f"{e['path']}: ticket {tid!r} has a prefix its store "
                       f"does not own ({','.join(prefixes)})")
        if not isinstance(tid, str):
            continue
        for edge in t.get("edges") or []:
            to = edge.get("to") if isinstance(edge, dict) else None
            if not isinstance(to, str) or "/" not in to:
                continue
            if edge.get("type") == "blocks":
                out.append(f"{e['path']}: {tid} holds a cross-store blocks edge "
                           f"to {to}; a cross-store block belongs on the blocked "
                           f"ticket as blocked-by (pm ticket dep)")
                continue
            reason = routing.cross_target(store, to)["reason"]
            if reason:
                out.append(f"{e['path']}: {tid} {edge.get('type')} edge to {to} "
                           f"dangles ({reason})")
    return out
