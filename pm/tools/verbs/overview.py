"""pm ticket overview: static Markdown overview of the store."""
import sys

import store as st

REGEN_COMMAND = "python3 scripts/overview.py"

_COUNT_LABELS = (
    ("total", "Total"),
    ("active", "Active"),
    ("ready", "Ready"),
    ("claimed", "Claimed"),
    ("unmerged", "Unmerged"),
    ("closed", "Closed"),
    ("semaphores", "Semaphores"),
)


def register(subparsers):
    sp = subparsers.add_parser("overview", help="static Markdown overview (derived; "
                               "write it outside the repo unless you mean to publish)")
    sp.add_argument("--out", help="output file (default: stdout)")
    sp.add_argument("--include-closed", action="store_true")


def _ticket_line(t):
    line = f"- `{t['id']}` — {t['title']} (P{t['priority']}, {t['status']})"
    if t.get("assignee"):
        line += f" — @{t['assignee']}"
    if t.get("blocked_by"):
        line += " — blocked by " + ", ".join(f"`{b}`" for b in t["blocked_by"])
    return line


def _section(title, lines):
    if not lines:
        return []
    return [f"## {title}", "", *lines, ""]


def render(projection):
    scope = projection["scope"]
    counts = projection["counts"]
    by_id = {t["id"]: t for t in projection["tickets"]}

    out = [
        "# Ticket store overview",
        "",
        "> **GENERATED — do not hand-edit.** Any edits made directly to this",
        "> file are lost the next time it is regenerated. Regenerate with:",
        f"> `{REGEN_COMMAND} --repo {scope['root']}`",
        ">",
        f"> Generated: `{projection['generated']}` — scope: `{scope['root']}`"
        f" (prefix `{scope['prefix']}`, include_closed=`{scope['include_closed']}`)",
        "",
        "## Counts",
        "",
        "| " + " | ".join(label for _, label in _COUNT_LABELS) + " |",
        "|" + "---|" * len(_COUNT_LABELS),
        "| " + " | ".join(str(counts.get(key, 0)) for key, _ in _COUNT_LABELS) + " |",
        "",
    ]

    out += _section("Semaphores (read before starting work)",
                    [_ticket_line(t) for t in projection["tickets"] if t["semaphore"]])
    out += _section("Ready", [_ticket_line(by_id[i]) for i in projection["order"]
                              if by_id[i]["ready"]])
    out += _section("In flight", [_ticket_line(by_id[i])
                                  for i in projection["by_status"].get("claimed", [])])
    out += _section("Done, unmerged",
                    [_ticket_line(by_id[i])
                     for i in projection["by_status"].get("done-unmerged", [])])

    epic_lines = []
    for epic in projection["epics"]:
        heading = (f"### `{epic['id']}` — {epic['title']} ({epic['status']}) — "
                   f"open children: {epic['open_children']}")
        if epic.get("hidden_children", 0):
            heading += f" (+{epic['hidden_children']} not in scope)"
        epic_lines += [heading, ""]
        if not epic["children"]:
            epic_lines.append("_(no children in scope)_")
        epic_lines.extend(_ticket_line(by_id[c]) for c in epic["children"])
        epic_lines.append("")
    out += _section("Epics", epic_lines)
    out += _section("Orphans", [_ticket_line(by_id[i]) for i in projection["orphans"]])

    while out and out[-1] == "":
        out.pop()
    out.append("")
    return "\n".join(out)


def run(args):
    store = st.open_store(getattr(args, "repo", None))
    text = render(st.project(store, include_closed=args.include_closed))
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
