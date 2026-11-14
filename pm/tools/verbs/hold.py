"""pm ticket hold: mark this session's claim in flight, or clear the marker."""
import store as st
from store import TicketError, now


def register(subparsers):
    sp = subparsers.add_parser("hold", help="mark this session's claim in flight "
                               "(or --clear the marker)")
    sp.add_argument("id")
    sp.add_argument("reason", nargs="?", help="why the claim stays open across turns")
    sp.add_argument("--clear", action="store_true", help="remove the hold marker")
    sp.add_argument("--session", help="session id (default: $PM_SESSION_ID, then "
                                      "$CLAUDE_CODE_SESSION_ID)")


def run(args):
    with st.locked_verb(args, "hold") as store:
        t = store.get(args.id)
        if t["status"] != "claimed":
            raise TicketError(f"not claimed (status: {t['status']}); {st.status_hint(t)}")
        if args.clear:
            if args.reason:
                raise TicketError("hold --clear takes no reason")
            if "hold" not in t:
                raise TicketError("not held")
            del t["hold"]
            t["updated"] = now()
            print(f"{t['id']} hold cleared")
            return
        hold = st.hold_marker(args.reason, args.session)
        _, _, claim_tok = st.split_assignee(t["assignee"])
        if claim_tok != hold["token"]:
            raise TicketError(f"{t['id']} is claimed by {t['assignee']}, not by this "
                              "session; only the claiming session can hold it")
        t["hold"] = hold
        t["updated"] = now()
        print(f"{t['id']} held: {hold['reason']}")
