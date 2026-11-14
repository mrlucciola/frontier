"""usage: pm ls [words ...] [-n count] [--json] [--all-stores]

List tickets, priority first. Status words (open taken parked done all) pick
statuses, default everything not done. ready, mine and epics narrow, so do under:id
and label:x; any other word must appear in the title or body. Twenty are shown;
-n 0 shows all. --all-stores reads every registered store.
"""
import registry
import render
import store
import who

STATUSES = ("open", "taken", "parked", "done")


def _matches(t, tickets, statuses, narrow, free):
    if t["status"] not in statuses:
        return False
    text = (t["title"] + "\n" + t["body"]).lower()
    if any(w.lower() not in text for w in free):
        return False
    for kind, value in narrow:
        if kind == "ready":
            if t["status"] != "open" or t["kind"] == "epic" or not all(
                    store.is_done(b, tickets) for b in t["blocked_by"]):
                return False
        elif kind == "mine":
            if t["status"] != "taken" or not who.yours(t["holder"]):
                return False
        elif kind == "epics":
            if t["kind"] != "epic":
                return False
        elif kind == "under":
            if t["under"] != value:
                return False
        elif kind == "label":
            if value not in t["labels"]:
                return False
    return True


def _stores(all_stores):
    if not all_stores:
        return [store.require()]
    seen, found = set(), []
    for _prefix, path, _ro in registry.read():
        s = store.find(path)
        if s is not None and s.root not in seen:
            seen.add(s.root)
            found.append(s)
    return found


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("words", nargs="*")
    p.add_argument("-n", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.add_argument("--all-stores", action="store_true")
    args = p.parse_intermixed_args(argv)
    if args.n < 0:
        render.usage_error(__doc__, "-n must be 0 or more.")
    statuses, narrow, free = set(), [], []
    for w in args.words:
        if w == "all":
            statuses.update(STATUSES)
        elif w in STATUSES:
            statuses.add(w)
        elif w in ("ready", "mine", "epics"):
            narrow.append((w, None))
        elif w.startswith("under:") and len(w) > 6:
            narrow.append(("under", w[6:]))
        elif w.startswith("label:") and len(w) > 6:
            narrow.append(("label", w[6:]))
        else:
            free.append(w)
    if not statuses:
        statuses = {"open", "taken", "parked"}
    rows = []
    for s in _stores(args.all_stores):
        tickets = store.replay(store.read(s))
        kept = [dict(t, _store=s.root) for t in tickets.values()
                if _matches(t, tickets, statuses, narrow, free)]
        for t in kept:
            t["_line"] = render.line(t, tickets)
        rows += kept
    rows.sort(key=lambda t: t["pri"])
    shown = rows[:args.n] if args.n else rows
    if not rows:
        print("nothing matches.")
        return 0
    for t in shown:
        if args.json:
            root = t["_store"] if args.all_stores else None
            print(render.as_json({k: v for k, v in t.items() if k[0] != "_"}, root))
        else:
            print(t["_line"])
    if len(shown) < len(rows) and not args.json:
        print("+%d more: add -n 0" % (len(rows) - len(shown)))
    return 0
