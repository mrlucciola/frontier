"""usage: pm hold [id] -m "text"

Mark a ticket you hold as deliberately kept across a pause, and say why. With no
id, hold the one ticket this session holds. The status stays taken; finishing,
parking or dropping the ticket clears the hold.
"""
import render
import store
import who


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("id", nargs="?")
    p.add_argument("-m", dest="text")
    args = p.parse_args(argv)
    if not args.text or not args.text.strip():
        render.usage_error(__doc__, 'hold needs -m "why it is kept".')
    s = store.home_of(store.require(), [args.id])

    def check(tickets):
        t = store.ticket(s, tickets, args.id)
        if t["status"] != "taken":
            render.refuse("%s is %s, not yours. Take it first: pm take %s"
                          % (t["id"], t["status"], t["id"]))
        if not who.yours(t["holder"]):
            holder = who.actor_of(t["holder"])
            render.refuse("%s is taken by %s, not yours. Only %s holds it."
                          % (t["id"], holder, holder))
        return [{"op": "hold", "id": t["id"], "text": args.text}]

    events = store.change(s, check)
    print("%s held: %s" % (events[0]["id"], args.text))
    return 0
