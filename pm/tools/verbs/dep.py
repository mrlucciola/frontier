"""pm ticket dep: add a blocks or related edge between two tickets."""
import store as st
from store import TicketError


def register(subparsers):
    sp = subparsers.add_parser("dep", help="add an edge: pm ticket dep SRC blocks|related DST")
    sp.add_argument("src")
    sp.add_argument("type", choices=("blocks", "related"))
    sp.add_argument("dst")


def run(args):
    with st.locked_store(getattr(args, "repo", None),
                         lambda: f"pm: dep {args.src} {args.dst}"[:120]) as store:
        _dep(args, store)


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


def _dep(args, store):
    blocks = args.type == "blocks"
    mine, other = (args.dst, args.src) if blocks else (args.src, args.dst)
    if st.is_remote_ref(store, other):
        row = store.get(mine)
        ref = st.edge_target(store, other)
        edge = {"type": "blocked-by" if blocks else "related", "to": ref}
        if edge in row["edges"]:
            raise TicketError("edge already exists")
        row["edges"].append(edge)
        row["updated"] = st.now()
        if blocks:
            print(f"{row['id']} <--blocked-by-- {ref}")
        else:
            print(f"{row['id']} --related--> {ref}")
        return
    src, dst = store.get(args.src), store.get(args.dst)
    if src["id"] == dst["id"]:
        raise TicketError("a ticket cannot depend on itself")
    edge = {"type": args.type, "to": dst["id"]}
    reverse = {"type": args.type, "to": src["id"]}
    if edge in src["edges"] or (args.type == "related" and reverse in dst["edges"]):
        raise TicketError("edge already exists")
    if blocks and would_cycle(store, src["id"], dst["id"]):
        raise TicketError(f"refused: {src['id']} blocks {dst['id']} would create a cycle")
    src["edges"].append(edge)
    src["updated"] = st.now()
    print(f"{src['id']} --{args.type}--> {dst['id']}")
