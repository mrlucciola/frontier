"""pm ticket create: file a ticket; prints its id."""
import argparse
import json
import math
import re
import sys
from datetime import datetime

import store as st
from store import TicketError, now

KINDS = ("task", "epic")

# Duplicate guard. A token is rare when at most DUP_RARE_MIN_DF rows,
# or DUP_RARE_FRACTION of the store, hold it. Floor: DUP_THRESHOLD shared rare
# words/ids, or one shared rare path or quoted string (DUP_STRONG_WEIGHT), and an
# idf-weighted Jaccard of DUP_MIN_SIMILARITY.
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


def priority_type(raw):
    """0-4 or P0-P4, case-insensitive."""
    s = raw[1:] if raw and raw[0] in "Pp" else raw
    try:
        n = int(s)
    except ValueError:
        n = -1
    if n not in range(5):
        raise argparse.ArgumentTypeError(
            f"invalid priority: {raw!r} (expected 0-4 or P0-P4)")
    return n


def register(subparsers):
    sp = subparsers.add_parser("create", help="file a ticket; prints its id")
    sp.add_argument("title")
    sp.add_argument("--body", default="")
    sp.add_argument("--kind", choices=KINDS, default="task")
    sp.add_argument("--priority", type=priority_type, default=2)
    sp.add_argument("--parent", help="epic id")
    sp.add_argument("--discovered-from", dest="discovered_from",
                    help="ticket being worked when this was discovered")
    sp.add_argument("--label", action="append")
    sp.add_argument("--id-file", dest="id_file", metavar="PATH",
                    help="also write the new id to PATH, so a follow-up command "
                         "can read it without $(...) command substitution")
    sp.add_argument("--claim-as", dest="claim_as", metavar="NAME",
                    help="claim the ticket for NAME in the same call, removing "
                         "the need to thread the id into a second command")
    sp.add_argument("--session", help="session id for --claim-as attribution")
    sp.add_argument("--dup-of", dest="dup_of", metavar="ID",
                    help="duplicate guard: add a sighting note to ID instead of "
                         "filing a new ticket")
    sp.add_argument("--new", action="store_true",
                    help="duplicate guard: file even when a similar ticket exists "
                         "(marks the row dedupe_overridden)")
    sp.add_argument("--json", action="store_true")


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
        if t["status"] == "closed":
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


def run(args):
    problem = st.title_problem(args.title)
    if problem:
        raise TicketError(problem)
    minted = []
    subject = lambda: " ".join(["pm: create", *minted])[:120]
    with st.locked_store(getattr(args, "repo", None), subject) as store:
        _create(args, store, minted)


def _create(args, store, minted):
    for label in args.label or []:
        problem = st.label_problem(label)
        if problem:
            raise TicketError(f"{problem}; nothing written")
    if args.parent:
        store.get(args.parent)
    discovered = st.edge_target(store, args.discovered_from, "discovered-from") \
        if args.discovered_from else None
    if args.parent and store.get(args.parent)["kind"] != "epic":
        raise TicketError(f"parent {args.parent} is not an epic")
    if args.claim_as:
        veto = st.claim_veto({"kind": args.kind, "status": "open", "assignee": None})
        if veto:
            raise TicketError(veto)
    if args.dup_of and args.new:
        raise TicketError("--dup-of and --new are mutually exclusive")
    if args.dup_of:
        dup = store.get(args.dup_of)
        dup["notes"].append(st.make_note(
            f"sighting {now()[:10]} (found in {args.discovered_from or 'none'}): "
            f"{args.title}", "finding"))
        dup["updated"] = now()
        print(dup["id"])
        return
    if not args.new:
        cands = find_duplicates(store.tickets, args.title, args.body or "")
        if cands:
            if args.json:
                print(json.dumps({"possible_duplicates": cands},
                                 ensure_ascii=False, indent=2, sort_keys=True))
            else:
                for c in cands:
                    print(f"possible duplicate: {c['id']} {c['status']} {c['title']}",
                          file=sys.stderr)
                print("pm: nothing written; add a sighting with --dup-of <id>, or "
                      "file anyway with --new", file=sys.stderr)
            sys.exit(2)
    t = {
        "id": store.new_id(args.title),
        "title": args.title,
        "body": args.body or "",
        "kind": args.kind,
        "status": "open",
        "priority": args.priority,
        "assignee": None,
        "parent": args.parent,
        "labels": sorted(set(args.label or [])),
        "edges": [],
        "notes": [],
        "created": now(),
        "updated": now(),
        "closure_reason": None,
    }
    if args.new:
        t["dedupe_overridden"] = True
    if args.discovered_from:
        t["edges"].append({"type": "discovered-from", "to": discovered})
    store.tickets.append(t)
    store.by_id[t["id"]] = t
    minted.append(t["id"])
    if args.id_file:
        with open(args.id_file, "w") as f:
            f.write(t["id"] + "\n")
    if args.claim_as:
        t["status"] = "claimed"
        t["assignee"] = st.session_assignee(args.claim_as, args.session)
        t["updated"] = now()
    print(t["id"])
