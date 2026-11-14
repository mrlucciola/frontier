"""pm ticket unlink: remove edge(s) SRC -> DST."""
import store as st
from store import TicketError

EDGE_TYPES = ("blocks", "related", "discovered-from", "blocked-by")


def register(subparsers):
    sp = subparsers.add_parser("unlink", help="remove edge(s) SRC -> DST")
    sp.add_argument("src")
    sp.add_argument("dst")
    sp.add_argument("--type", choices=EDGE_TYPES,
                    help="restrict to one edge type (default: all)")


def run(args):
    with st.locked_store(args.repo,
                         f"pm: unlink {args.src} {args.dst}"[:120]) as store:
        _unlink(args, store)


def _unlink(args, store):
    src, dst, etype = args.src, args.dst, args.type
    if (etype == "blocks" and st.is_remote_ref(store, src)
            and not st.is_remote_ref(store, dst)):
        # `unlink A blocks B` across stores removes the blocked-by held on B
        src, dst, etype = dst, src, "blocked-by"
    to = f"{st.ref_prefix(dst)}/{dst}" if st.is_remote_ref(store, dst) else dst
    t = store.get(src)
    before = len(t["edges"])
    t["edges"] = [e for e in t["edges"]
                  if not (e.get("to") == to
                          and (etype is None or e.get("type") == etype))]
    removed = before - len(t["edges"])
    if removed == 0:
        hint = " (a cross-store block is removed with --type blocks)" \
            if to != dst and etype is None else ""
        raise TicketError(f"no edge {src} -> {to} found{hint}")
    t["updated"] = st.now()
    print(f"{src}: removed {removed} edge(s) to {to}")
