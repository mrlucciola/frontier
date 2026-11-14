"""usage: pm park [id] -m "text"

Stop work that is not finished, and say what it waits on. With no id, park the
one ticket this session holds. The ticket leaves you and stays out of `pm ls ready`;
`pm take <id>` resumes it. Only a ticket you hold can be parked.
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
        render.usage_error(__doc__, 'park needs -m "what it waits on".')
    s = store.require()

    def check(tickets):
        t = store.ticket(s, tickets, args.id)
        if t["status"] != "taken":
            render.refuse("%s is %s, not yours. Take it first: pm take %s"
                          % (t["id"], t["status"], t["id"]))
        if not who.yours(t["holder"]):
            holder = who.actor_of(t["holder"])
            render.refuse("%s is taken by %s, not yours. Only %s parks it."
                          % (t["id"], holder, holder))
        return [{"op": "park", "id": t["id"], "text": args.text}]

    events = store.change(s, check)
    print("%s parked" % events[0]["id"])
    return 0
