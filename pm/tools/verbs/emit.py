"""usage: pm emit id ns.name [key=value ...]

Append a plugin's event to a ticket's log. pm stores it and gives it no meaning;
read a value back with pm get id ns.key. The name needs a dot: plain names belong
to pm. The keys ts, by, op and id are reserved.
"""
import re

import render
import store

NAME = re.compile(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+$")


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("id")
    p.add_argument("name")
    p.add_argument("pairs", nargs="*")
    args = p.parse_args(argv)
    name = args.name
    if not NAME.match(name):
        render.refuse("emit takes a namespaced name such as wt.start. "
                      "Plain names belong to pm.")
    data = {}
    for pair in args.pairs:
        key, eq, value = pair.partition("=")
        if not eq or not key:
            render.usage_error(__doc__, "%s is not key=value." % pair)
        if key in store.KEY_ORDER:
            render.refuse("%s is reserved. Use another key." % key)
        data[key] = value
    s = store.home_of(store.require(), [args.id])

    def check(tickets):
        t = store.ticket(s, tickets, args.id)
        event = {"op": name, "id": t["id"]}
        event.update(data)
        return [event]

    store.change(s, check)
    return 0
