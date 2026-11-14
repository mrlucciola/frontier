"""usage: pm edit id [--title text] [--body text] [-p 0-4] [-l label] [--unlabel label] [--under id|none]

Change a ticket's fields and print which changed. --under files the ticket beneath
an epic; --under none takes it out. -l adds a label, --unlabel removes one.
"""
import argparse

import render
import store


def _priority(text):
    if text not in ("0", "1", "2", "3", "4"):
        raise argparse.ArgumentTypeError("priority is 0 to 4")
    return int(text)


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("id", nargs="?")
    p.add_argument("--title")
    p.add_argument("--body")
    p.add_argument("-p", dest="pri", type=_priority)
    p.add_argument("-l", dest="label")
    p.add_argument("--unlabel")
    p.add_argument("--under")
    args = p.parse_args(argv)
    if not args.id:
        render.usage_error(__doc__, "edit needs a ticket id.")
    if args.title is not None and not args.title.strip():
        render.usage_error(__doc__, "a title cannot be empty.")
    fields = [name for name, value in (
        ("title", args.title), ("body", args.body), ("pri", args.pri),
        ("labels", args.label or args.unlabel), ("under", args.under)) if value is not None]
    if not fields:
        render.usage_error(__doc__, "edit needs something to change.")

    s = store.home_of(store.require(), [args.id])
    target = []

    def check(tickets):
        t = store.ticket(s, tickets, args.id)
        target.append(t["id"])
        event = {"op": "edit", "id": t["id"]}
        if args.title is not None:
            event["title"] = args.title
        if args.body is not None:
            event["body"] = args.body
        if args.pri is not None:
            event["pri"] = args.pri
        if args.label:
            event["label"] = args.label
        if args.unlabel:
            event["unlabel"] = args.unlabel
        if args.under is not None:
            if args.under == "none":
                event["under"] = None
            else:
                parent = store.ticket(s, tickets, args.under)
                if parent["kind"] != "epic":
                    render.refuse('%s is not an epic. Make one: pm new "title" --epic'
                                  % parent["id"])
                event["under"] = parent["id"]
        return [event]

    store.change(s, check)
    print("%s edited: %s" % (target[-1], ", ".join(fields)))
    return 0
