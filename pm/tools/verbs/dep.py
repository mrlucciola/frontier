"""pm ticket dep: add blocks or related edges from one ticket to several, all or none."""
import store as st
from store import TicketError


def register(subparsers):
    sp = subparsers.add_parser(
        "dep", help="add edges: pm ticket dep SRC blocks|related DST [DST...] (all or none)")
    sp.add_argument("src")
    sp.add_argument("type", choices=("blocks", "related"))
    sp.add_argument("dst", nargs="+")
    sp.add_argument("--note", help="append this note to each DST (local targets only)")


def run(args):
    with st.locked_store(args.repo,
                         f"pm: dep {args.src} {' '.join(args.dst)}"[:120]) as store:
        _dep(args, store)


def _dep(args, store):
    blocks = args.type == "blocks"
    if args.note and not args.note.strip():
        raise TicketError("dep --note is empty; nothing written")
    plan = []
    for target in dict.fromkeys(args.dst):
        mine, other = (target, args.src) if blocks else (args.src, target)
        if st.is_remote_ref(store, other):
            row = store.get(mine)
            ref = st.edge_target(store, other)
            edge = {"type": "blocked-by" if blocks else "related", "to": ref}
            if edge in row["edges"]:
                raise TicketError(f"edge already exists ({target}); nothing written")
            if args.note:
                raise TicketError(f"--note needs a target in this store; {target} is "
                                  "cross-store; nothing written")
            line = (f"{row['id']} <--blocked-by-- {ref}" if blocks
                    else f"{row['id']} --related--> {ref}")
            plan.append((row, edge, None, line))
            continue
        src, dst = store.get(args.src), store.get(target)
        if src["id"] == dst["id"]:
            raise TicketError("a ticket cannot depend on itself; nothing written")
        edge = {"type": args.type, "to": dst["id"]}
        reverse = {"type": args.type, "to": src["id"]}
        if edge in src["edges"] or (not blocks and reverse in dst["edges"]):
            raise TicketError(
                f"edge already exists ({src['id']} -> {dst['id']}); nothing written")
        if blocks and st.would_cycle(store, src["id"], dst["id"]):
            raise TicketError(f"refused: {src['id']} blocks {dst['id']} would create "
                              "a cycle; nothing written")
        plan.append((src, edge, dst, f"{src['id']} --{args.type}--> {dst['id']}"))
    for row, edge, dst, line in plan:
        row["edges"].append(edge)
        row["updated"] = st.now()
        if args.note and dst is not None:
            dst["notes"].append(st.make_note(args.note))
            dst["updated"] = st.now()
        print(line)
