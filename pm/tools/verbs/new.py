"""usage: pm new "title" [-b body] [-p 0-4] [-l label] [--epic] [--under id] [--from id] [--blocks id] [--blocked-by id] [--take] [--as name] [--new]

File a ticket and print its id. Priority is 0 (most urgent) to 4; the default is 2.
--epic makes a ticket that groups others, --under files it beneath an epic, --take
takes it in the same call. A title close to an open one is refused unless --new.
"""
import argparse
import math
import re
from datetime import datetime

import render
import store
from store import now

DUP_THRESHOLD = 3
DUP_STRONG_WEIGHT = 3
DUP_RARE_MIN_DF = 3
DUP_RARE_FRACTION = 0.05
DUP_MIN_SIMILARITY = 0.25
DUP_CLOSED_WINDOW_DAYS = 30
DUP_MAX_CANDIDATES = 3

_DUP_WORD_RE = re.compile(r"[a-z][a-z0-9_]{3,}")
_DUP_ID_RE = re.compile(r"\b[a-z][a-z0-9]{1,7}-[0-9a-f]{6}\b")
_DUP_PATH_RE = re.compile(
    r"(?<![\w/.~-])(?:[\w.~-]+/)+[\w.-]*\w|\b[\w-]+\.(?:py|md|json|jsonl|sh|toml|ts|js|ya?ml)\b")
_DUP_QUOTE_RE = re.compile(r"""(?<!\w)(['"])([^'"\n]{12,}?)\1(?!\w)""")


def dup_tokens(text):
    """{(kind, token)}: kind w(ord) / i(d) / p(ath) / q(uote)."""
    low = text.lower()
    toks = {("w", w) for w in _DUP_WORD_RE.findall(low)}
    toks |= {("i", m) for m in _DUP_ID_RE.findall(low)}
    toks |= {("p", m.rstrip(".")) for m in _DUP_PATH_RE.findall(low)}
    toks |= {("q", " ".join(m[1].split())) for m in _DUP_QUOTE_RE.findall(low)}
    return toks


def find_duplicates(tickets, title, body, now_ts=None):
    """Up to DUP_MAX_CANDIDATES `{id,status,title,score,shared}` for open rows, or
    rows closed within DUP_CLOSED_WINDOW_DAYS, that share enough rare tokens with
    the new text, best first."""
    new = dup_tokens(f"{title}\n{body}")
    if not new:
        return []
    rows = [(t, dup_tokens(f"{t['title']}\n{t.get('body', '')}")) for t in tickets]
    df = {k: 1 for k in new}
    for _, toks in rows:
        for k in toks:
            df[k] = df.get(k, 0) + 1
    total = len(rows) + 1
    rare_max = max(DUP_RARE_MIN_DF, int(len(rows) * DUP_RARE_FRACTION))
    idf = lambda k: math.log(1 + total / df[k])
    new_w = sum(idf(k) for k in new)
    now_dt = datetime.strptime(now_ts or now(), "%Y-%m-%dT%H:%M:%SZ")
    out = []
    for t, toks in rows:
        if t["status"] == "done":
            age = now_dt - datetime.strptime(t["updated"], "%Y-%m-%dT%H:%M:%SZ")
            if age.days > DUP_CLOSED_WINDOW_DAYS:
                continue
        common = new & toks
        rare = [k for k in common if df[k] - 1 <= rare_max]
        if sum(DUP_STRONG_WEIGHT if k[0] in "pq" else 1 for k in rare) < DUP_THRESHOLD:
            continue
        shared_w = sum(idf(k) for k in common)
        sim = shared_w / (new_w + sum(idf(k) for k in toks) - shared_w)
        if sim >= DUP_MIN_SIMILARITY:
            out.append({"id": t["id"], "status": t["status"], "title": t["title"],
                        "score": round(sim, 2), "shared": sorted(k[1] for k in rare)})
    out.sort(key=lambda c: (-c["score"], c["id"]))
    return out[:DUP_MAX_CANDIDATES]


def _priority(text):
    if text not in ("0", "1", "2", "3", "4"):
        raise argparse.ArgumentTypeError("priority is 0 to 4")
    return int(text)


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("title", nargs="?")
    p.add_argument("-b", dest="body")
    p.add_argument("-p", dest="pri", type=_priority)
    p.add_argument("-l", dest="labels", action="append")
    p.add_argument("--epic", action="store_true")
    p.add_argument("--under")
    p.add_argument("--from", dest="source")
    p.add_argument("--blocks")
    p.add_argument("--blocked-by", dest="blocked_by")
    p.add_argument("--take", action="store_true")
    p.add_argument("--as", dest="as_name")
    p.add_argument("--new", action="store_true")
    args = p.parse_args(argv)
    if not args.title or not args.title.strip():
        render.usage_error(__doc__, "new needs a title.")

    s = store.require()

    def check(tickets):
        if not args.new:
            found = find_duplicates(list(tickets.values()), args.title, args.body or "")
            if found:
                match = tickets[found[0]["id"]]
                render.refuse(
                    'this looks like %s\nSame work: pm note %s "seen again: <where>"\n'
                    "Different work: repeat with --new"
                    % (render.line(match, tickets), match["id"]))
        event = {"op": "new", "id": store.next_id(s, tickets), "title": args.title}
        if args.body:
            event["body"] = args.body
        if args.epic:
            event["kind"] = "epic"
        if args.pri is not None:
            event["pri"] = args.pri
        if args.labels:
            event["labels"] = args.labels
        if args.under:
            parent = store.ticket(s, tickets, args.under)
            if parent["kind"] != "epic":
                render.refuse('%s is not an epic. Make one: pm new "title" --epic'
                              % parent["id"])
            event["under"] = parent["id"]
        links = []
        if args.source:
            links.append({"op": "link", "id": event["id"], "rel": "from",
                          "to": store.ticket(s, tickets, args.source)["id"]})
        if args.blocked_by:
            links.append({"op": "link", "id": event["id"], "rel": "blocked-by",
                          "to": store.ticket(s, tickets, args.blocked_by)["id"]})
        if args.blocks:
            links.append({"op": "link", "id": store.ticket(s, tickets, args.blocks)["id"],
                          "rel": "blocked-by", "to": event["id"]})
        events = [event]
        if args.take:
            events.append({"op": "take", "id": event["id"]})
        return events + links

    events = store.change(s, check, actor=args.as_name)
    print(events[0]["id"])
    return 0
