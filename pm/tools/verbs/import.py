"""usage: pm import

Fill a new log from a spec v2 store. Run it in a directory whose .pm/ holds the old
tickets.jsonl (and archive/tickets-*.jsonl) but no events. Old ids, dates, notes and
kinds are kept, edit-trail notes are left behind, the prefix is registered, and the old
files stay in place. A log that already has events is refused.
"""
import glob
import json
import os
import sys

import registry
import render
import store

STATUS = {"open": "open", "claimed": "taken", "done-unmerged": "parked", "closed": "done"}
ORDER = ("open", "taken", "parked", "done")


def _name(identity):
    """`agent:harness/sess-1#e8bc163c` -> `sess-1#e8bc163c`; no identity -> `import`."""
    if not identity or not isinstance(identity, str):
        return "import"
    rest = identity.split(":", 1)[1] if ":" in identity else identity
    name, _, token = rest.partition("#")
    name = name.rsplit("/", 1)[-1] or "import"
    return "%s#%s" % (name, token) if token else name


def _bare(target):
    return target.split("/", 1)[1] if isinstance(target, str) and "/" in target else target


def _rows(path):
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as e:
        render.refuse("cannot read %s: %s." % (path, e.strerror or e))
    rows = []
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            render.refuse("%s line %d is not a ticket row. Fix or remove it, then run pm import again."
                          % (os.path.basename(path), n))
        rows.append(row)
    return rows


def _new(row, ts):
    event = {"ts": ts, "by": "import", "op": "new", "id": row["id"],
             "title": row.get("title") or ""}
    if row.get("body"):
        event["body"] = row["body"]
    if row.get("kind") == "epic":
        event["kind"] = "epic"
    if isinstance(row.get("priority"), int):
        event["pri"] = row["priority"]
    if row.get("labels"):
        event["labels"] = list(row["labels"])
    if row.get("parent"):
        event["under"] = _bare(row["parent"])
    return event


def _done(tid, ts, by, reason, findings):
    event = {"ts": ts, "by": by, "op": "done", "id": tid}
    if reason and reason != "done":
        event["reason"] = reason
    if findings:
        findings = [_bare(f) for f in findings]
        event["findings"] = "none" if findings == ["none"] else findings
    return event


def _plan(rows):
    news, notes, links, states, holds = [], [], [], [], []
    ids = set()
    counts = {k: 0 for k in ORDER}
    skipped = []
    for row in rows:
        if row["id"] in ids:
            skipped.append(row["id"])
            continue
        ids.add(row["id"])
        for sub in row.get("subtasks") or []:
            if isinstance(sub, dict) and isinstance(sub.get("id"), str):
                ids.add(sub["id"])
    seen = set()
    for row in rows:
        tid = row["id"]
        if tid in seen:
            continue
        seen.add(tid)
        created = row.get("created") or row.get("updated")
        updated = row.get("updated") or created
        news.append(_new(row, created))
        for note in row.get("notes") or []:
            if note.get("kind") == "edit-trail" or not note.get("text"):
                continue
            event = {"ts": note.get("ts") or created, "by": "import", "op": "note",
                     "id": tid, "text": note["text"]}
            if note.get("kind"):
                event["kind"] = note["kind"]
            notes.append(event)
        for edge in row.get("edges") or []:
            kind, to = edge.get("type"), _bare(edge.get("to"))
            if kind == "blocks":
                if to in ids:
                    links.append({"ts": created, "by": "import", "op": "link", "id": to,
                                  "rel": "blocked-by", "to": tid})
                else:
                    skipped.append("%s blocks %s" % (tid, edge.get("to")))
            elif kind in ("blocked-by", "related", "discovered-from"):
                links.append({"ts": created, "by": "import", "op": "link", "id": tid,
                              "rel": "from" if kind == "discovered-from" else kind, "to": to})
        status = STATUS.get(row.get("status"), "open")
        counts[status] += 1
        if status == "taken":
            holder = _name(row.get("assignee"))
            states.append({"ts": updated, "by": holder, "op": "take", "id": tid})
            hold = row.get("hold")
            if isinstance(hold, dict) and hold.get("reason"):
                holds.append({"ts": hold.get("since") or updated, "by": holder, "op": "hold",
                              "id": tid, "text": hold["reason"]})
        elif status == "parked":
            states.append({"ts": updated, "by": "import", "op": "park", "id": tid})
        elif status == "done":
            states.append(_done(tid, updated, _name(row.get("closed_by")),
                                row.get("closure_reason"), row.get("findings")))
        for sub in row.get("subtasks") or []:
            if not isinstance(sub, dict) or not isinstance(sub.get("id"), str):
                continue
            if sub["id"] in seen:
                continue
            seen.add(sub["id"])
            closed = sub.get("closed") or updated
            news.append({"ts": created, "by": "import", "op": "new", "id": sub["id"],
                         "title": sub.get("title") or "", "under": tid})
            if sub.get("note"):
                notes.append({"ts": closed, "by": "import", "op": "note", "id": sub["id"],
                              "text": sub["note"]})
            states.append(_done(sub["id"], closed, _name(sub.get("closed_by")),
                                sub.get("reason"), sub.get("findings")))
            counts["done"] += 1
    return news + notes + links + states + holds, counts, skipped


def run(argv):
    p = render.parser(__doc__)
    p.parse_args(argv)
    s, _ = store.locate_dir()
    if s is None:
        render.refuse("no store here. Put the old .pm/ in this directory first.")
    source = os.path.join(s.dir, "tickets.jsonl")
    if not os.path.isfile(source):
        render.refuse("no %s. Nothing to import." % source)
    if not s.prefix:
        render.refuse("%s has no prefix. Set one in config.json." % os.path.join(s.dir, "config.json"))
    rows = _rows(source)
    for path in sorted(glob.glob(os.path.join(s.dir, "archive", "tickets-*.jsonl"))):
        rows += _rows(path)

    result = {}

    def check(tickets):
        if tickets or (os.path.exists(s.log) and os.path.getsize(s.log) > 0):
            render.refuse("this store already has events. Import only fills an empty log.")
        events, counts, skipped = _plan(rows)
        result["counts"], result["skipped"] = counts, skipped
        return events

    for prefix, path, _ in registry.read():
        if prefix == s.prefix and os.path.realpath(path) != os.path.realpath(s.root):
            render.refuse("prefix %s belongs to %s. Choose another." % (prefix, path))
    store.change(s, check, hooks=False)
    if not any(pre == s.prefix and os.path.realpath(path) == os.path.realpath(s.root)
               for pre, path, _ in registry.read()):
        registry.add(s.prefix, s.root)
    counts = result["counts"]
    print("imported %d tickets: %s" % (sum(counts.values()), ", ".join(
        "%d %s" % (counts[k], k) for k in ORDER if counts[k])))
    for item in result["skipped"]:
        sys.stderr.write("pm: warning: skipped %s\n" % item)
    return 0
