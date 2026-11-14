"""Everything the user reads: refusals, usage errors, ticket text."""
import argparse
import sys


def refuse(text):
    sys.stderr.write("pm: %s\n" % text)
    sys.exit(1)


def usage_error(doc, text):
    sys.stderr.write("pm: %s\n%s\n" % (text, doc.strip().split("\n")[0]))
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def __init__(self, doc):
        super().__init__(add_help=False)
        self.doc = doc

    def error(self, message):
        usage_error(self.doc, message[:1].lower() + message[1:] + ".")


def parser(doc):
    return _Parser(doc)


def _open_blockers(t, tickets):
    import store
    if t["status"] == "done":
        return []
    return [b for b in t["blocked_by"] if not store.is_done(b, tickets)]


def line(t, tickets):
    import who
    out = "%s  P%s  %s  %s" % (t["id"], t["pri"], t["status"], t["title"])
    if t["kind"] == "epic":
        out += " [epic]"
    if t["status"] == "taken" and t["holder"]:
        out += "  @%s" % who.actor_of(t["holder"])
    blockers = _open_blockers(t, tickets)
    if blockers:
        out += "  blocked by %s" % ", ".join(blockers)
    return out


def _note_lines(n):
    import who
    head = "  %s %s" % ((n["ts"] or "")[:10], who.actor_of(n["by"] or ""))
    if n["kind"]:
        head += " [%s]" % n["kind"]
    if not n["text"]:
        return [head]
    rows = n["text"].split("\n")
    return ["%s: %s" % (head, rows[0])] + ["    " + r for r in rows[1:]]


def show(t, tickets, all_notes=False):
    import store
    out = [line(t, tickets)]
    if t["under"]:
        parent = tickets.get(t["under"])
        out.append("under: %s%s" % (t["under"], " " + parent["title"] if parent else ""))
    if t["status"] != "done":
        waiting = [b for b in t["blocks"] if not store.is_done(b, tickets)]
        waiting += [b for b in store.blocked_elsewhere(t["id"], tickets) if b not in waiting]
        if waiting:
            out.append("blocks: %s" % ", ".join(waiting))
    if t["related"]:
        out.append("related: %s" % ", ".join(t["related"]))
    if t["from"]:
        out.append("from: %s" % t["from"])
    if t["labels"]:
        out.append("labels: %s" % ", ".join(t["labels"]))
    if t["hold"]:
        out.append("hold: %s" % t["hold"])
    if t["findings"]:
        f = t["findings"]
        out.append("findings: %s" % (", ".join(f) if isinstance(f, list) else f))
    if t["reason"]:
        out.append("reason: %s" % t["reason"])
    if t["kind"] == "epic":
        kids = [c for c in tickets.values() if c["under"] == t["id"]]
        if kids:
            counts = ", ".join(
                "%d %s" % (n, st) for st in ("open", "taken", "parked", "done")
                for n in [sum(1 for c in kids if c["status"] == st)] if n)
            out.append("children: %s" % counts)
            for c in [c for c in kids if c["status"] != "done"][:10]:
                out.append("  " + line(c, tickets))
    if t["body"]:
        out += ["", t["body"]]
    notes = [n for n in t["notes"] if n["text"] or n["kind"]]
    if notes:
        shown = notes if all_notes else notes[-5:]
        if len(shown) < len(notes):
            head = "notes (last 5 of %d; all: pm show %s --notes):" % (len(notes), t["id"])
        else:
            head = "notes:"
        out += ["", head]
        for n in shown:
            out += _note_lines(n)
    return "\n".join(out)


def as_json(t, store_root=None):
    import json
    data = {k: v for k, v in t.items() if k != "events"}
    if store_root is not None:
        data["store"] = store_root
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
