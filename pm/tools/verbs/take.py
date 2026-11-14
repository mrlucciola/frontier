"""usage: pm take [id ...] [--force] [--as name] [--dry-run]

Take a ticket and print it. With no id, take the top of `pm ls ready`.
Taking a ticket you already hold prints it again. Taking a parked ticket resumes it.
--force takes a ticket that is blocked or that someone else holds. Use it only
when the operator says so.
--as records another name as the holder, for a named worker.
--dry-run checks and changes nothing.
"""
import render
import store
import who


def _blockers(t, tickets):
    return [b for b in t["blocked_by"] if not store.is_done(b, tickets)]


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("ids", nargs="*")
    p.add_argument("--force", action="store_true")
    p.add_argument("--as", dest="as_name")
    p.add_argument("--dry-run", dest="dry_run", action="store_true")
    args = p.parse_intermixed_args(argv)
    s = store.require()
    chosen = []

    def check(tickets):
        if args.ids:
            targets = [store.ticket(s, tickets, w) for w in args.ids]
        else:
            ready = [t for t in tickets.values()
                     if t["status"] == "open" and t["kind"] != "epic"
                     and not _blockers(t, tickets)]
            if not ready:
                render.refuse("nothing is ready. Everything open: pm ls open")
            targets = [min(ready, key=lambda t: t["pri"])]
        unique = []
        for t in targets:
            if t not in unique:
                unique.append(t)
        events = []
        for t in unique:
            event = {"op": "take", "id": t["id"]}
            if t["status"] == "done":
                render.refuse("%s is done. Reopen it: pm reopen %s" % (t["id"], t["id"]))
            if t["status"] == "taken":
                if who.yours(t["holder"]):
                    continue
                if not args.force:
                    render.refuse("%s is taken by %s. Pick another: pm ls ready"
                                  % (t["id"], who.actor_of(t["holder"])))
                event["from"] = t["holder"]
            else:
                blockers = _blockers(t, tickets)
                if blockers and not args.force:
                    render.refuse("%s is blocked by %s. Finish %s first: pm take %s"
                                  % (t["id"], ", ".join(blockers), blockers[0], blockers[0]))
            events.append(event)
        chosen[:] = [t["id"] for t in unique]
        return events

    store.change(s, check, actor=args.as_name, dry_run=args.dry_run)
    if args.dry_run:
        for tid in chosen:
            print("ok: %s can be taken" % tid)
        return 0
    tickets = store.replay(store.read(s))
    print("\n\n".join(render.show(tickets[tid], tickets) for tid in chosen))
    return 0
