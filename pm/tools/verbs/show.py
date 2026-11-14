"""pm ticket show: full ticket with graph context."""
import json

import routing
import store as st
from store import TicketError


def register(subparsers):
    sp = subparsers.add_parser("show", help="full ticket with graph context")
    sp.add_argument("id")
    sp.add_argument("--notes", type=int, metavar="N",
                    help="text output: print only the last N notes, plus one line "
                         "saying how many were omitted (--json always prints all)")
    sp.add_argument("--all-notes", action="store_true",
                    help="text output: also print edit-trail notes (hidden by default)")
    out = sp.add_mutually_exclusive_group()
    out.add_argument("--json", action="store_true")
    out.add_argument("--field", action="append", metavar="NAME",
                     help="print one line per field of the --json object, in the "
                          "order given (repeatable)")


def field_text(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return ",".join(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def run(args):
    store = st.open_store(getattr(args, "repo", None))
    t = store.read(st.local_id(args.id))
    archive_path = t.get("archive_path")
    obj = dict(t, blocked_by=[b["id"] for b in store.blockers_of(t["id"])
                              if b["status"] != "closed"],
               blocks=[e["to"] for e in t["edges"] if e["type"] == "blocks"],
               children=[c["id"] for c in store.children(t["id"])],
               ready=store.is_ready(t))
    obj.pop("archive_path", None)

    if args.field:
        for name in args.field:
            if name not in obj:
                raise TicketError(f"show: no field {name}; fields: "
                                  + ", ".join(sorted(obj)))
        for name in args.field:
            print(field_text(obj[name]))
        return
    if args.json:
        print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
        return

    lines = [st.fmt_line(t)]
    if archive_path:
        lines.append(f"archived: {archive_path}")
    if t["body"]:
        lines.append(t["body"])
    cross = routing.cross_blockers(store, t)
    for key in ("parent", "blocked_by", "blocks", "children", "labels"):
        val = obj.get(key) if key != "parent" else t.get("parent")
        if key == "blocked_by":
            val = list(val) + [routing.cross_label(b) for b in cross
                               if b["status"] != "closed"]
        if key == "parent" and val and val in store.by_id:
            val = f"{val}  {store.by_id[val]['title']}"
        if val:
            lines.append(f"{key}: {val if isinstance(val, str) else ', '.join(val)}")
    reverse = routing.cross_blocks_of(store, t["id"])
    if reverse:
        lines.append(f"blocks (other stores): {', '.join(reverse)}")
    if t.get("compacted"):
        lines.append(f"compacted into {t['parent']} on close")
    for e in t["edges"]:
        if e["type"] == "discovered-from":
            lines.append(f"discovered-from: {e['to']}")
    for key in ("closed_by", "released_by"):
        if t.get(key):
            lines.append(f"{key}: {t[key]}")
    if t.get("subtasks"):
        lines.append("subtasks:")
        lines.extend(f"  {s['id']}  closed {str(s.get('closed'))[:10]}  {s.get('title')}"
                     for s in t["subtasks"])
    notes = t["notes"]
    if not args.all_notes:
        hidden = sum(1 for n in notes if n.get("kind") == "edit-trail")
        if hidden:
            notes = [n for n in notes if n.get("kind") != "edit-trail"]
            lines.append(f"({hidden} edit-trail note{'s' if hidden != 1 else ''} hidden; "
                         f"pm ticket show {t['id']} --all-notes prints them)")
    if args.notes is not None:
        if args.notes < 0:
            raise TicketError("--notes must be 0 or more")
        omitted = len(notes) - args.notes
        if omitted > 0:
            lines.append(f"({omitted} earlier note{'s' if omitted != 1 else ''} omitted; "
                         f"pm ticket show {t['id']} prints all {len(notes)})")
        notes = notes[len(notes) - args.notes:] if args.notes else []
    for n in notes:
        lines.append(f"note {n['ts']}: {n['text']}")
    print("\n".join(lines))
