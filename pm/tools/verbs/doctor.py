"""usage: pm doctor

Check this store. Prints one line per problem and exits 1: a line that is not an
event (every verb skips it), an event for a ticket that was never created, and a
link to a ticket no registered store has. A clean store prints its prefix and counts.
"""
import json

import render
import store


def _plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def _event(text):
    try:
        event = json.loads(text)
    except ValueError:
        return None
    if isinstance(event, dict) and isinstance(event.get("op"), str) \
            and isinstance(event.get("id"), str):
        return event
    return None


def _exists(s, tid, known):
    if tid in known:
        return True
    m = store.ID_RE.match(tid or "")
    return bool(m and m.group(1) != s.prefix and store.locate(m.group(1), tid))


def run(argv):
    render.parser(__doc__).parse_args(argv)
    s = store.require()
    try:
        with open(s.log, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        lines = []
    problems, known, count, links = [], set(), 0, []
    for n, text in enumerate(lines, 1):
        if not text.strip():
            continue
        event = _event(text)
        if event is None:
            problems.append("line %d is not an event; pm skips it. Delete the line by hand." % n)
            continue
        count += 1
        if event["op"] == "new":
            known.add(event["id"])
        elif event["id"] not in known and event["op"] in store.OPS:
            problems.append("line %d is an event for unknown ticket %s." % (n, event["id"]))
        if event["op"] == "link" and isinstance(event.get("to"), str):
            links.append((n, event["to"]))
    for n, to in links:
        if not _exists(s, to, known):
            problems.append("line %d links to %s, which cannot be found." % (n, to))
    problems.sort(key=lambda p: int(p.split()[1]))
    if problems:
        print("\n".join(problems))
    else:
        print("ok: %s, %s, %s" % (s.prefix, _plural(len(known), "ticket"), _plural(count, "event")))
    if store.in_checkout(s.root):
        print(_backup_line(s, lines))
    return 1 if problems else 0


def _backup_line(s, lines):
    try:
        blob = store.backup_blob(s)
    except (OSError, RuntimeError) as e:
        return "backup: cannot read refs/pm/log: %s" % ((str(e).splitlines() or ["unknown"])[0])
    if blob is None:
        return "backup: refs/pm/log does not exist yet. The next change creates it."
    text = blob.decode("utf-8", "replace")
    if text.splitlines() == lines:
        return "backup: refs/pm/log is current"
    saved = len([x for x in text.splitlines() if x.strip()])
    have = len([x for x in lines if x.strip()])
    if saved > have:
        return "backup: refs/pm/log has %d events and the log has %d. Bring them back: pm restore" \
            % (saved, have)
    return "backup: refs/pm/log has %d events and the log has %d. The next change updates it." \
        % (saved, have)
