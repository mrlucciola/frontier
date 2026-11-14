"""usage: pm show [id] [--notes] [--json]

Print one ticket: its line, links, body and the last five notes. --notes prints
every note. Without an id it shows the one ticket this session holds. A bare number
names a ticket in this store.
"""
import render
import store


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("id", nargs="?")
    p.add_argument("--notes", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    s = store.require()
    if args.json:
        store.unbuilt("json")
    tickets = store.replay(store.read(s))
    t = store.ticket(s, tickets, args.id)
    print(render.show(t, tickets, all_notes=args.notes))
    return 0
