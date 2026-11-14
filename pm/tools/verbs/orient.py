"""usage: pm

Orient: what you hold, what is ready and what is parked, each section only when it
has entries. Ready and parked show five tickets and a count of the rest. With
nothing to show it says how to file work.
"""
import plugins
import render
import store
import who


def _rank(t):
    return t["pri"]


def _section(name, rows, tickets, more):
    out = [name + ":"] + ["  " + render.line(t, tickets) for t in rows[:5]]
    if len(rows) > 5:
        out.append("  +%d more: %s" % (len(rows) - 5, more))
    return out


def run(argv):
    p = render.parser(__doc__)
    p.parse_args(argv)
    s = store.require()
    tickets = store.replay(store.read(s))
    ordered = sorted(tickets.values(), key=_rank)
    yours = [t for t in ordered if t["status"] == "taken" and who.yours(t["holder"])]
    ready = [t for t in ordered if t["status"] == "open" and t["kind"] != "epic"
             and all(store.is_done(b, tickets) for b in t["blocked_by"])]
    parked = [t for t in ordered if t["status"] == "parked"]
    out = []
    if yours:
        out += ["yours:"] + ["  " + render.line(t, tickets) for t in yours]
    if ready:
        out += _section("ready", ready, tickets, "pm ls ready")
    if parked:
        out += _section("parked", parked, tickets, "pm ls parked")
    extra = plugins.orient_text(s)
    if extra:
        out.append(extra)
    print("\n".join(out) if out else 'nothing to do. File work: pm new "title"')
    return 0
