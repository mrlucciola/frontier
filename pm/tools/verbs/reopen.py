"""usage: pm reopen id

Make a done or parked ticket open again. Its notes stay; its findings and reason
are cleared. A ticket that is open or taken is refused.
"""
import render
import store
import who


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("id", nargs="?")
    args = p.parse_args(argv)
    if not args.id:
        render.usage_error(__doc__, "reopen needs a ticket id.")
    s = store.require()

    def check(tickets):
        t = store.ticket(s, tickets, args.id)
        if t["status"] == "open":
            render.refuse("%s is open already." % t["id"])
        if t["status"] == "taken":
            render.refuse("%s is taken by %s. Only done or parked tickets reopen."
                          % (t["id"], who.actor_of(t["holder"])))
        return [{"op": "reopen", "id": t["id"]}]

    events = store.change(s, check)
    print("%s open" % events[0]["id"])
    return 0
