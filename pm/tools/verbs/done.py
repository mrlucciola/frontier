"""usage: pm done [id ...] [-m "text"] [--findings none|id,...] [--reason wont-fix|duplicate|superseded|abandoned] [--force] [--dry-run]

Finish a ticket. With no id, finish the one this session holds. Only the holder
finishes a taken ticket; --force overrides, and finishes an epic with children not
done. With findings_required, --findings names the tickets that took the findings,
or `none` with -m saying what you checked. --reason finishes without doing the work.
"""
import render
import store
import who

REASONS = ("wont-fix", "duplicate", "superseded", "abandoned")


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("ids", nargs="*")
    p.add_argument("-m", dest="text")
    p.add_argument("--findings")
    p.add_argument("--reason")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", dest="dry_run", action="store_true")
    args = p.parse_intermixed_args(argv)
    if args.reason and args.reason not in REASONS:
        render.usage_error(__doc__, "--reason is one of %s." % ", ".join(REASONS))
    s = store.home_of(store.require(), args.ids)
    chosen = []

    def check(tickets):
        if args.ids:
            targets = [store.ticket(s, tickets, w) for w in args.ids]
        else:
            targets = [store.ticket(s, tickets, None)]
        unique = []
        for t in targets:
            if t not in unique:
                unique.append(t)
        batch = [t["id"] for t in unique]
        events = []
        for t in unique:
            tid = t["id"]
            if t["status"] == "done":
                render.refuse("%s is already done." % tid)
            if t["status"] == "taken" and not who.yours(t["holder"]) and not args.force:
                holder = who.actor_of(t["holder"])
                render.refuse("%s is taken by %s. Only %s finishes it, or the operator with --force."
                              % (tid, holder, holder))
            if t["kind"] == "epic" and not args.force:
                open_kids = [c["id"] for c in tickets.values()
                             if c["under"] == tid and c["status"] != "done"
                             and c["id"] not in batch]
                if open_kids:
                    render.refuse("%s has children not done: %s. Finish them, or move one out: "
                                  "pm edit %s --under none"
                                  % (tid, ", ".join(open_kids), open_kids[0]))
            event = {"op": "done", "id": tid}
            findings = None
            if args.findings:
                words = [w for w in args.findings.split(",") if w]
                if words == ["none"]:
                    findings = "none"
                    if not (args.text or any(n["text"] for n in t["notes"])):
                        render.refuse('--findings none needs a reason. Add -m "<what you checked>"')
                else:
                    findings = [store.ticket(s, tickets, w)["id"] for w in words]
            elif s.config.get("findings_required"):
                render.refuse("%s needs --findings: none, or the ids of the tickets that took "
                              "the findings.\nRepeat: pm done %s --findings none "
                              '-m "<what you checked>"' % (tid, tid))
            if findings:
                event["findings"] = findings
            if args.reason:
                event["reason"] = args.reason
            if args.text:
                event["text"] = args.text
            events.append(event)
        chosen[:] = batch
        return events

    store.change(s, check, dry_run=args.dry_run)
    if args.dry_run:
        for tid in chosen:
            print("ok: %s can be done" % tid)
        return 0
    tickets = store.replay(store.read(s))
    for tid in chosen:
        print("%s done" % tid)
    told = []
    for tid in chosen:
        parent = tickets.get(tickets[tid]["under"] or "")
        if not parent or parent["id"] in told or parent["status"] == "done":
            continue
        if all(c["status"] == "done" for c in tickets.values() if c["under"] == parent["id"]):
            told.append(parent["id"])
            print("next: every child of %s is done. Finish the epic: pm done %s"
                  % (parent["id"], parent["id"]))
    return 0
