"""pm ticket where: the repo root of the store owning an id; --mutate preflights a close or release."""
import routing
import store as st
from store import TicketError


def register(subparsers):
    sp = subparsers.add_parser("where", help="print the repo root of the store owning an id")
    sp.add_argument("id")
    sp.add_argument("--mutate", action="store_true",
                    help="preflight a close/release of <id>: exit 1 with the refusal "
                         "(frozen or untrusted registry, unknown id, bad --findings, "
                         "already closed, epic with open children, not claimed) "
                         "without writing; prints the repo root when it would pass")
    sp.add_argument("--verb", choices=("close", "release"), default=None,
                    help="with --mutate, the verb to preflight (default close)")
    sp.add_argument("--findings", default=None,
                    help="with --mutate, also validate this close --findings value")


def run(args):
    if not args.mutate:
        if args.findings is not None:
            raise TicketError("--findings needs --mutate")
        if args.verb is not None:
            raise TicketError("--verb needs --mutate")
        print(routing.resolve_store(args.id, explicit=args.repo).repo)
        return
    # Preflight only, no writes. Not checked: findings_required and the "none needs a
    # note" rules (wt owns those), and races between this call and the real one.
    verb = args.verb or "close"
    if verb == "release" and args.findings is not None:
        raise TicketError("--findings applies to --verb close")
    tid = st.local_id(args.id)
    resolved = routing.resolve_store(tid, explicit=args.repo)
    routing.route_ids([tid], explicit=args.repo, mutate=True)
    routing.refuse_if_frozen(resolved.root)
    store = st.Store(resolved.root)
    archived = (tid not in store.by_id and tid in store.archived_ids()
                and tid not in store.compacted)
    if tid not in store.by_id and tid not in store.compacted and not archived:
        raise TicketError(f"no ticket {tid} in store {resolved.repo}")
    if args.findings is not None:
        st.parse_findings(args.findings, store)
    t = ({"id": tid, "kind": "task", "status": "closed"} if archived
         else store.read(tid))
    if verb == "release":
        st.refuse_if_unclaimed(t)
    else:
        st.refuse_if_closed(t)
        st.close_open_children(store, t, False, False)
    print(resolved.repo)
