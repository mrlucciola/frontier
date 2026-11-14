"""pm ticket reopen: reopen closed or done-unmerged ticket(s)."""
import store as st
from store import TicketError, now


def register(subparsers):
    sp = subparsers.add_parser("reopen", help="reopen closed/unmerged ticket(s)")
    sp.add_argument("id", nargs="+")


def run(args):
    with st.locked_verb(args, "reopen") as store:
        ids = st.each_id(args)
        for tid in ids:
            t = store.get(tid)
            if t["status"] == "open":
                raise TicketError(f"already open; {st.status_hint(t)}")
            if t["status"] == "claimed":
                raise TicketError(f"{tid} is claimed by {t['assignee']}; "
                                  f"`pm ticket release {tid}` first, then reopen if "
                                  "it is still needed")
        for tid in ids:
            t = store.get(tid)
            t["status"], t["assignee"], t["updated"] = "open", None, now()
            for key in ("hold", "findings", "findings_absent", "closed_by", "released_by"):
                t.pop(key, None)
            print(f"{t['id']} reopened")
