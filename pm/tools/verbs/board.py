"""pm ticket board: tickets grouped by status, priority or epic."""
import store as st

STATUS_ORDER = ("open", "claimed", "done-unmerged", "closed")
PRIORITY_ORDER = ("P0", "P1", "P2", "P3", "P4")
GROUPS = ("status", "priority", "epic")

_RESET = "\x1b[0m"
_TAG_COLOR = {"SEM": "31;1", "BLOCKED": "33", "READY": "32"}

NOTHING_TO_SHOW = "(nothing to show — no tickets in scope)\n"


def register(subparsers):
    sp = subparsers.add_parser("board", help="grouped/board view")
    sp.add_argument("--group-by", choices=GROUPS, default="status")
    sp.add_argument("--include-closed", action="store_true")
    sp.add_argument("--color", action="store_true")


def _c(text, code, color):
    return f"\x1b[{code}m{text}{_RESET}" if color else text


def _header(label, color):
    return _c(f"== {label} ==", "1", color)


def _semaphore_first(ids, id_map):
    return sorted((id_map[i] for i in ids if i in id_map),
                  key=lambda t: not t.get("semaphore"))


def _fmt_ticket(t, color, indent=0):
    pad = "  " * indent
    tags = []
    if t.get("semaphore"):
        tags.append("SEM")
    if t.get("kind") == "task":
        if t.get("blocked_by"):
            tags.append("BLOCKED")
        elif t.get("ready"):
            tags.append("READY")
    prefix = pad
    if tags:
        prefix = f"{pad}[{'|'.join(_c(tag, _TAG_COLOR[tag], color) for tag in tags)}] "
    assignee = f" @{t['assignee']}" if t.get("assignee") else ""
    return f"{prefix}{t['id']}  P{t['priority']}  {t['status']:<13}{t['title']}{assignee}"


def _section(label, ids, id_map, color):
    if not ids:
        return []
    lines = [_header(label, color)]
    lines.extend(_fmt_ticket(t, color) for t in _semaphore_first(ids, id_map))
    lines.append("")
    return lines


def _by_status(projection, id_map, color):
    lines = []
    for status in STATUS_ORDER:
        ids = projection["by_status"].get(status, [])
        lines.extend(_section(f"{status.upper()} ({len(ids)})", ids, id_map, color))
    return lines


def _by_priority(projection, id_map, color):
    lines = []
    for p in PRIORITY_ORDER:
        ids = projection["by_priority"].get(p, [])
        lines.extend(_section(f"{p} ({len(ids)})", ids, id_map, color))
    return lines


def _by_epic(projection, id_map, color):
    lines = []
    for epic in projection["epics"]:
        lines.append(_header(f"EPIC: {epic['title']} ({epic['status']}, "
                             f"{epic['open_children']} open)", color))
        if epic["id"] in id_map:
            lines.append(_fmt_ticket(id_map[epic["id"]], color))
        children = [c for c in epic["children"] if c in id_map]
        lines.extend(_fmt_ticket(t, color, indent=1)
                     for t in _semaphore_first(children, id_map))
        lines.append("")
    orphans = [i for i in projection["orphans"] if i in id_map]
    lines.extend(_section(f"ORPHANS ({len(orphans)})", orphans, id_map, color))
    return lines


_RENDERERS = {"status": _by_status, "priority": _by_priority, "epic": _by_epic}


def render(projection, group_by, color):
    if not projection["tickets"]:
        return NOTHING_TO_SHOW
    id_map = {t["id"]: t for t in projection["tickets"]}
    lines = _RENDERERS[group_by](projection, id_map, color)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def run(args):
    store = st.open_store(getattr(args, "repo", None))
    projection = st.project(store, include_closed=args.include_closed)
    print(render(projection, args.group_by, args.color))
