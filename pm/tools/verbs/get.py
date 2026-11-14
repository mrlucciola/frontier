"""usage: pm get id field [field ...]

Print one value per line, for scripts. Fields: status holder title pri kind under
labels blocked-by blocks store body. A name such as wt.branch prints the latest
value of branch among this ticket's events whose op starts with wt. An unset value
prints an empty line.
"""
import json

import render
import store

FIELDS = ("status", "holder", "title", "pri", "kind", "under", "labels",
          "blocked-by", "blocks", "store", "body")


def _text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, (dict, bool)):
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    return str(value)


def _plugin(t, field):
    ns, key = field.split(".", 1)
    found = None
    for event in t["events"]:
        if str(event.get("op", "")).startswith(ns + ".") and key in event:
            found = event[key]
    return found


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("id")
    p.add_argument("fields", nargs="+")
    args = p.parse_args(argv)
    for f in args.fields:
        dotted = "." in f and not f.startswith(".") and not f.endswith(".")
        if f not in FIELDS and not dotted:
            render.usage_error(__doc__, "no field %s. Fields: %s, or a plugin's ns.key"
                               % (f, " ".join(FIELDS)))
    s = store.require()
    tickets = store.replay(store.read(s))
    t = store.ticket(s, tickets, args.id)
    for f in args.fields:
        if f == "store":
            value = s.root
        elif f == "blocked-by":
            value = t["blocked_by"]
        elif f in FIELDS:
            value = t[f]
        else:
            value = _plugin(t, f)
        print(_text(value))
    return 0
