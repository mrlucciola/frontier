"""pm ticket claim: take ready ticket(s) for a session."""
import routing
import store as st
from store import TicketError, now

EXITS = (
    "Exits: close: `pm ticket close <id>`\n"
    "       close --unmerged: `pm ticket close <id> --unmerged --note \"<where/how>\"`\n"
    "       release: `pm ticket release <id>`\n"
    "       hold: keep the claim deliberately (work in flight); just stop again")


def register(subparsers):
    sp = subparsers.add_parser("claim", help="claim ready ticket(s)")
    sp.add_argument("id", nargs="+")
    sp.add_argument("--as", dest="by", required=True, help="agent/operator name")
    sp.add_argument("--session", help="session id for claim attribution "
                    "(default: $PM_SESSION_ID, then $CLAUDE_CODE_SESSION_ID); stored "
                    "as agent:<provider>/<name>#<hash> so the Stop hook can tell "
                    "whose claim it is")
    sp.add_argument("--force", action="store_true", help="claim despite blockers")
    sp.add_argument("--reopen", action="store_true",
                    help="take a done-unmerged ticket back in one call (reopen + claim)")
    sp.add_argument("--hold", metavar="REASON",
                    help="mark the claim in flight: the Stop hook warns once per "
                         "session instead of blocking every turn; release/close "
                         "clear it")


def blocked_by(store, t):
    return ([b["id"] for b in store.blockers_of(t["id"]) if b["status"] != "closed"]
            + [routing.cross_label(b) for b in routing.unsatisfied_cross(store, t)])


def run(args):
    with st.locked_verb(args, "claim") as store:
        ids = st.each_id(args)
        for tid in ids:
            t = store.get(tid)
            veto = st.claim_veto(t, args.reopen)
            if veto:
                raise TicketError(veto)
            if not store.is_ready({**t, "status": "open"}) and not args.force:
                raise TicketError(f"not ready — blocked by: {', '.join(blocked_by(store, t))} "
                                  "(use --force to claim anyway)")
        assignee = st.session_assignee(args.by, args.session)
        hold = st.hold_marker(args.hold, args.session) if args.hold is not None else None
        for tid in ids:
            t = store.get(tid)
            t["status"], t["assignee"], t["updated"] = "claimed", assignee, now()
            t.pop("released_by", None)
            if args.reopen:
                for key in ("findings", "findings_absent", "closed_by"):
                    t.pop(key, None)
            if hold:
                t["hold"] = dict(hold)
            print(f"{t['id']} claimed by {assignee}"
                  + (f" (held: {hold['reason']})" if hold else ""))
        print(EXITS)
