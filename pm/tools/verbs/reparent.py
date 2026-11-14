"""pm ticket reparent: move a ticket under another epic, or detach it."""
import store as st
from store import TicketError

_KEEP = object()


def register(subparsers):
    sp = subparsers.add_parser("reparent",
                               help="move a ticket under another epic (or none)")
    sp.add_argument("id")
    # Omitting the target is an error, not a silent detach; --none has its own
    # dest because argparse re-applies a nargs="?" positional's default over a
    # flag that shares it.
    sp.add_argument("to_epic", nargs="?", metavar="EPIC", default=_KEEP,
                    help="target epic id (or pass --none to detach)")
    sp.add_argument("--none", dest="detach", action="store_true",
                    help="detach from any epic")


def run(args):
    with st.locked_store(getattr(args, "repo", None),
                         lambda: f"pm: reparent {args.id}"[:120]) as store:
        _reparent(args, store)


def _would_cycle(store, tid, new_parent):
    """True if parenting `tid` under `new_parent` closes a parent loop."""
    cur, seen = new_parent, set()
    while cur:
        if cur == tid:
            return True
        if cur in seen:
            return False
        seen.add(cur)
        nxt = store.by_id.get(cur)
        cur = nxt.get("parent") if nxt else None
    return False


def _reparent(args, store):
    t = store.get(args.id)
    if args.detach:
        if args.to_epic is not _KEEP:
            raise TicketError(f"reparent got both a target epic ({args.to_epic}) "
                              "and --none; pass one")
        t["parent"], t["updated"] = None, st.now()
        print(f"{t['id']} reparented to (none)")
        return
    if args.to_epic is _KEEP:
        raise TicketError("reparent needs a target epic id, or --none to detach")
    epic = store.get(args.to_epic)
    if epic["kind"] != "epic":
        raise TicketError(f"parent {epic['id']} is not an epic")
    if epic["id"] == t["id"]:
        raise TicketError("a ticket cannot be its own parent")
    if _would_cycle(store, t["id"], epic["id"]):
        raise TicketError(
            f"refused: parenting {t['id']} under {epic['id']} would create a cycle")
    t["parent"], t["updated"] = epic["id"], st.now()
    print(f"{t['id']} reparented to {epic['id']}")
