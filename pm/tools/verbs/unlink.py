"""usage: pm unlink a b

Remove every link between two tickets, whichever way it was made: blocks, related
or from. It is refused when the two are not linked.
"""
import render
import store


def _linked(t, other):
    return other in t["blocked_by"] or other in t["related"] or t["from"] == other


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("words", nargs="*")
    args = p.parse_args(argv)
    if len(args.words) != 2:
        render.usage_error(__doc__, "unlink needs two tickets.")

    s = store.require()
    names = []

    def check(tickets):
        a = store.ticket(s, tickets, args.words[0])
        b = store.ticket(s, tickets, args.words[1])
        names[:] = [a["id"], b["id"]]
        events = [{"op": "unlink", "id": x["id"], "to": y["id"]}
                  for x, y in ((a, b), (b, a)) if _linked(x, y["id"])]
        if not events:
            render.refuse("no link between %s and %s." % (a["id"], b["id"]))
        return events

    store.change(s, check)
    print("%s and %s unlinked" % tuple(names))
    return 0
