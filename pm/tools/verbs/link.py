"""usage: pm link a blocks|related b [c ...] [--note "text"]

Link ticket a to one or more others. "a blocks b" keeps b out of ready until a is
done; a link that would make a cycle is refused. "related" shows on both tickets and
gates nothing. A link that already exists is printed and not added again. --note
adds the text as a note on each ticket after the relation, even for an existing link.
"""
import render
import store


def _reaches(tickets, start, goal):
    seen, todo = set(), [start]
    while todo:
        tid = todo.pop()
        if tid == goal:
            return True
        if tid in seen or tid not in tickets:
            continue
        seen.add(tid)
        todo.extend(tickets[tid]["blocks"])
    return False


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("words", nargs="*")
    p.add_argument("--note", dest="note")
    args = p.parse_args(argv)
    words = args.words
    if args.note is not None and not args.note.strip():
        render.usage_error(__doc__, "--note needs text.")
    if len(words) < 3:
        render.usage_error(__doc__, "link needs two tickets and a relation.")
    if words[1] not in ("blocks", "related"):
        render.usage_error(__doc__, "a relation is blocks or related.")
    rel = words[1]

    s = store.require()
    s = store.home_of(s, words[2:] if rel == "blocks" else words[:1])
    lines = []

    def check(tickets):
        del lines[:]
        a = store.ticket(s, tickets, words[0])
        others = [store.ticket(s, tickets, w) for w in words[2:]]
        events, pending = [], set()
        for b in others:
            if b["id"] == a["id"]:
                render.refuse("%s cannot be linked to itself." % a["id"])
            lines.append("%s %s %s" % (a["id"], rel, b["id"]))
            if rel == "blocks":
                if _reaches(tickets, b["id"], a["id"]):
                    render.refuse("%s already blocks %s. That would be a cycle."
                                  % (b["id"], a["id"]))
                if a["id"] in b["blocked_by"] or (b["id"], a["id"]) in pending:
                    continue
                pending.add((b["id"], a["id"]))
                events.append({"op": "link", "id": b["id"], "rel": "blocked-by",
                               "to": a["id"]})
            else:
                key = frozenset((a["id"], b["id"]))
                if b["id"] in a["related"] or key in pending:
                    continue
                pending.add(key)
                events.append({"op": "link", "id": a["id"], "rel": "related",
                               "to": b["id"]})
        if args.note is not None:
            for tid in dict.fromkeys([a["id"]] + [b["id"] for b in others]):
                events.append({"op": "note", "id": tid, "text": args.note})
        return events

    store.change(s, check)
    print("\n".join(lines))
    return 0
