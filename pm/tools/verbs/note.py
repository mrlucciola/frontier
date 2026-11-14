"""usage: pm note [id] "text" [-k decision|finding|measurement]

Add a note to a ticket. Without an id the note goes to the one ticket this session
holds. A first word that is a number or an id names the ticket, not the text. -k
tags the note as a decision, a finding or a measurement.
"""
import re

import render
import store

KINDS = ("decision", "finding", "measurement")
_ID_WORD = re.compile(r"^(\d+|[a-z][a-z0-9]{0,7}-[A-Za-z0-9]+)$")


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("words", nargs="*")
    p.add_argument("-k", dest="kind")
    args = p.parse_args(argv)
    if args.kind is not None and args.kind not in KINDS:
        render.usage_error(__doc__, "a note kind is one of: %s." % ", ".join(KINDS))
    words = args.words
    word = None
    if len(words) >= 2 and _ID_WORD.match(words[0]):
        word, words = words[0], words[1:]
    if len(words) != 1 or not words[0].strip():
        render.usage_error(__doc__, "note needs text.")
    text = words[0]

    s = store.require()
    target = []

    def check(tickets):
        t = store.ticket(s, tickets, word)
        target.append(t["id"])
        event = {"op": "note", "id": t["id"], "text": text}
        if args.kind:
            event["kind"] = args.kind
        return [event]

    store.change(s, check)
    print("%s noted" % target[-1])
    return 0
