"""usage: pm stores

List the registry: one line per store, the prefix and its directory, with ro after a
read-only one. pm init adds a line; ids are routed to their store by prefix.
"""
import render
import registry


def run(argv):
    p = render.parser(__doc__)
    p.parse_args(argv)
    for prefix, path, ro in registry.read():
        print("%s  %s%s" % (prefix, path, "  ro" if ro else ""))
    return 0
