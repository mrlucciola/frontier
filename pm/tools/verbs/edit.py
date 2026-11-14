"""pm ticket edit: atomically edit title, priority or body; old values stay as notes."""
import json

import store as st
from store import TicketError, priority_type


def register(subparsers):
    sp = subparsers.add_parser("edit", help="edit ticket title, priority, or body")
    sp.add_argument("id")
    sp.add_argument("--title")
    sp.add_argument("--priority", type=priority_type)
    sp.add_argument("--body")
    sp.add_argument("--append-body", dest="append_body",
                    help="append text as a new line to the existing body")


def run(args):
    with st.locked_store(getattr(args, "repo", None),
                         lambda: f"pm: edit {args.id}"[:120]) as store:
        _edit(args, store)


def _trail(text, ts):
    return st.make_note(f"edit history: {text}", "edit-trail", ts)


def _edit(args, store):
    if (args.title is None and args.priority is None and args.body is None
            and args.append_body is None):
        raise TicketError("pm ticket edit: nothing to do (pass --title, --priority, "
                          "--body, or --append-body)")
    if args.append_body is not None:
        if args.body is not None:
            raise TicketError("pm ticket edit: --append-body cannot be combined "
                              "with --body")
        if not args.append_body.strip():
            raise TicketError("pm ticket edit: --append-body text is empty")

    # Every field is validated before the row is touched: a combined edit is
    # all-or-nothing.
    title = None
    if args.title is not None:
        title = args.title.splitlines()[0] if args.title else args.title
        problem = st.title_problem(title)
        if problem:
            raise TicketError(problem)

    t = store.get(args.id)
    changed_at = st.now()
    if title is not None:
        t["title"] = title
        print(f"{t['id']} title: {title}")
    if args.priority is not None:
        if args.priority != t["priority"]:
            t["notes"].append(_trail(f"priority was P{t['priority']}", changed_at))
            t["priority"] = args.priority
        print(f"{t['id']} priority: P{args.priority}")
    if args.body is not None:
        if args.body != t["body"]:
            t["notes"].append(_trail(
                f"body was {json.dumps(t['body'], ensure_ascii=False)}", changed_at))
            t["body"] = args.body
        print(f"{t['id']} body updated")
    if args.append_body is not None:
        old = t["body"]
        new = args.append_body.rstrip("\n")
        t["notes"].append(_trail(
            f"body was {json.dumps(old, ensure_ascii=False)}", changed_at))
        t["body"] = f"{old.rstrip(chr(10))}\n{new}" if old.strip() else new
        print(f"{t['id']} body appended")
    t["updated"] = changed_at
