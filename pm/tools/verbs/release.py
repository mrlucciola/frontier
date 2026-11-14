"""pm ticket release: give claimed ticket(s) back to open."""
import os

import store as st
from store import now


def register(subparsers):
    sp = subparsers.add_parser("release", help="release claimed ticket(s) back to open")
    sp.add_argument("id", nargs="+")
    sp.add_argument("--session", help="session id for released_by attribution "
                                      "(default: $PM_SESSION_ID, then "
                                      "$CLAUDE_CODE_SESSION_ID)")


def acting_identity(args):
    """The identity a claim by this session would carry, or None without a
    session token (a bare name says nothing about which session acted)."""
    if not st.session_token(args.session):
        return None
    name = (os.environ.get("PM_AGENT") or "").partition("/")[2] \
        or st._agent_provider() or "pm"
    return st.session_assignee(name, args.session)


def run(args):
    with st.locked_verb(args, "release") as store:
        # A stray assignee at any status also passes the guard: release is the
        # mechanical fix for "claimed but unassigned" and "assignee set but not
        # claimed" drift that a hand-edited store can hold.
        ids = st.each_id(args)
        for tid in ids:
            st.refuse_if_unclaimed(store.get(tid))
        actor = acting_identity(args)
        for tid in ids:
            t = store.get(tid)
            t["assignee"], t["updated"] = None, now()
            t.pop("hold", None)
            # The stray-assignee fix on a closed or done-unmerged row clears the
            # assignee only; it must not reopen the row.
            if t["status"] in ("closed", "done-unmerged"):
                print(f"{t['id']} released (assignee cleared, status {t['status']} kept)")
                continue
            t["status"] = "open"
            t.pop("closed_by", None)
            if actor:
                t["released_by"] = actor
            else:
                t.pop("released_by", None)
            print(f"{t['id']} released")
