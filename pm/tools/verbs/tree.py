"""pm ticket tree: impact analysis and the epic subtree of one ticket."""
import json

import routing
import store as st
from store import TicketError


def register(subparsers):
    sp = subparsers.add_parser("tree", help="impact analysis around a ticket")
    sp.add_argument("id")
    sp.add_argument("--json", action="store_true")


def row_of(store, tid):
    """The live row, or the synthesized closed row of a compacted id, else None."""
    if tid in store.by_id:
        return store.by_id[tid]
    if tid in store.compacted:
        parent, entry = store.compacted[tid]
        return st.synthesize_tombstone(tid, parent, entry)
    return None


def blocks_of(store, tid):
    """Ids `tid` blocks (its outgoing blocks-edges); none for a compacted or
    archived id, whose edges are gone."""
    row = store.by_id.get(tid)
    if row is None and (tid in store.archived_ids() or tid in store.compacted):
        return []
    return [e["to"] for e in (row or store.get(tid))["edges"] if e["type"] == "blocks"]


def run(args):
    store = st.open_store(args.repo)
    tid = st.local_id(args.id)
    root = row_of(store, tid)
    if root is None and tid in store.archived_ids():
        raise TicketError(f"{tid} is archived; tree needs a live ticket "
                          f"(pm ticket show {tid})")
    root = root or store.get(tid)
    obj = {
        "id": root["id"],
        "impacts": store.walk(root["id"], lambda i: blocks_of(store, i)),
        "blocked_by_chain": store.walk(
            root["id"], lambda i: [b["id"] for b in store.blockers_of(i)]),
        "subtree": store.subtree(root["id"]),
    }
    if args.json:
        print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
        return

    def line(i):
        row = row_of(store, i)
        return st.fmt_line(row) if row else i

    lines = [st.fmt_line(root)]
    for label, key in (("impacts (transitively blocks)", "impacts"),
                       ("blocked-by chain", "blocked_by_chain"),
                       ("epic subtree", "subtree")):
        ids = obj[key]
        lines.append(f"{label}:")
        lines.extend(f"  {line(i)}" for i in ids)
        leaves = routing.cross_blockers(store, root) if key == "blocked_by_chain" else []
        for b in leaves:
            lines.append(f"  {b['ref']} [{b['reason'] or b['status']}]"
                         + (f" {b['title']}" if b["title"] else ""))
        if not ids and not leaves:
            lines.append("  (none)")
    print("\n".join(lines))
