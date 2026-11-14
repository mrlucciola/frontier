"""usage: pm drop [id ...] [-m "text"] [--force] [--dry-run]

Give a taken ticket back, untouched. With no id, drop the one ticket this session
holds. Only its holder drops it; --force drops one that someone else holds, and
is for the operator. -m leaves a note saying why.
--dry-run checks and changes nothing.
"""
import render
import store
import who


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("ids", nargs="*")
    p.add_argument("-m", dest="text")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", dest="dry_run", action="store_true")
    args = p.parse_intermixed_args(argv)
    s = store.home_of(store.require(), args.ids)
    chosen = []

    def check(tickets):
        if args.ids:
            targets = [store.ticket(s, tickets, w) for w in args.ids]
        else:
            targets = [store.ticket(s, tickets, None)]
        unique = []
        for t in targets:
            if t not in unique:
                unique.append(t)
        events = []
        for t in unique:
            if t["status"] != "taken":
                render.refuse("%s is %s, not taken. Nothing to drop." % (t["id"], t["status"]))
            if not who.yours(t["holder"]) and not args.force:
                holder = who.actor_of(t["holder"])
                render.refuse("%s is taken by %s. Only %s drops it, or the operator with --force."
                              % (t["id"], holder, holder))
            event = {"op": "drop", "id": t["id"]}
            if args.text:
                event["text"] = args.text
            events.append(event)
        chosen[:] = [t["id"] for t in unique]
        return events

    store.change(s, check, dry_run=args.dry_run)
    for tid in chosen:
        print("ok: %s can be dropped" % tid if args.dry_run else "%s open" % tid)
    return 0
