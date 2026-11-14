"""usage: pm log [id] [-n count]

Print the stored event lines of a ticket exactly as written, oldest first. Without
an id it uses the one ticket this session holds. -n keeps the last count lines.
"""
import json

import render
import store


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("id", nargs="?")
    p.add_argument("-n", type=int, default=0)
    args = p.parse_args(argv)
    if args.n < 0:
        render.usage_error(__doc__, "-n must be 0 or more.")
    s = store.require()
    t = store.ticket(s, store.replay(store.read(s)), args.id)
    try:
        with open(s.log, encoding="utf-8", errors="replace") as f:
            raw = f.read().splitlines()
    except OSError:
        raw = []
    rows = []
    for text in raw:
        try:
            event = json.loads(text)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("id") == t["id"]:
            rows.append(text)
    for text in rows[-args.n:] if args.n else rows:
        print(text)
    return 0
