"""usage: pm hook session-start|prompt|stop

What an agent harness should inject. Reads one JSON object on stdin with any of cwd,
session_id, prompt, stop_hook_active; a missing or bad one is empty. cwd picks the
store, session_id picks the session. session-start prints the tickets for the repo,
prompt each ticket it names once per session (kept in $TMPDIR/pm-mentioned-<token>), and stop, when the session still holds a ticket
it has not held, prints the four ways out on stderr and exits 2. Outside a store, or
with nothing to say, it prints nothing.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import render
import store
import who

EVENTS = ("session-start", "prompt", "stop")
COMPONENT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def _stdin():
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        data = json.loads(sys.stdin.read())
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _orient(cwd):
    # A subprocess: orient must find the store from cwd and read the session id set in run.
    try:
        out = subprocess.run(["/usr/bin/python3", os.path.join(COMPONENT, "cli", "pm")],
                             cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, universal_newlines=True)
    except OSError:
        return ""
    return out.stdout.strip()


def _session_start(cwd):
    print("pm tickets in this repo:")
    body = _orient(cwd)
    if body:
        print(body)
    print("All verbs: pm help")
    return 0


def _prompt(s, text):
    if not s.prefix or not isinstance(text, str):
        return 0
    tickets = store.replay(store.read(s))
    path = _mentioned_path()
    shown = _read_mentioned(path)
    seen = []
    for m in re.finditer(r"(?<![A-Za-z0-9-])%s-[A-Za-z0-9]+" % re.escape(s.prefix), text):
        tid = m.group(0)
        if tid in tickets and tid not in seen and tid not in shown:
            seen.append(tid)
    seen = seen[:3]
    if seen:
        print("mentioned:")
        for tid in seen:
            print("  " + render.line(tickets[tid], tickets))
        _keep_mentioned(path, seen)
    return 0


def _mentioned_path():
    tok = who.token()
    if not tok:
        return None
    return os.path.join(os.environ.get("TMPDIR") or tempfile.gettempdir(),
                        "pm-mentioned-" + tok)


def _read_mentioned(path):
    if not path:
        return set()
    try:
        with open(path) as f:
            return set(f.read().split("\n"))
    except (OSError, ValueError):
        return set()


def _keep_mentioned(path, ids):
    if not path:
        return
    try:
        with open(path, "a") as f:
            f.write("".join(tid + "\n" for tid in ids))
    except OSError:
        pass


def _stop(s, data):
    if data.get("stop_hook_active") is True:
        return 0
    tickets = store.replay(store.read(s))
    held = [t for t in tickets.values()
            if t["status"] == "taken" and not t["hold"] and who.yours(t["holder"])]
    if not held:
        return 0
    if len(held) == 1:
        tid = held[0]["id"]
        lead = "You still hold %s (%s). Before you stop, run one of:" % (tid, held[0]["title"])
    else:
        tid = "<id>"
        lead = "You still hold %s. Before you stop, run one of these for each:" % (
            ", ".join("%s (%s)" % (t["id"], t["title"]) for t in held))
    sys.stderr.write("\n".join([
        lead,
        '  pm done %s -m "<what landed>"' % tid,
        '  pm park %s -m "<what it waits on>"' % tid,
        "  pm drop %s" % tid,
        '  pm hold %s -m "<why it stays yours>"' % tid,
    ]) + "\n")
    return 2


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("event", nargs="?")
    args = p.parse_args(argv)
    if args.event not in EVENTS:
        render.usage_error(__doc__, "hook needs one of: %s." % ", ".join(EVENTS))
    data = _stdin()
    sid = data.get("session_id")
    if isinstance(sid, str) and sid:
        os.environ["PM_SESSION_ID"] = sid
    cwd = data.get("cwd")
    cwd = cwd if isinstance(cwd, str) and os.path.isdir(cwd) else os.getcwd()
    s = store.find(cwd)
    if s is None:
        return 0
    if args.event == "session-start":
        return _session_start(cwd)
    if args.event == "prompt":
        return _prompt(s, data.get("prompt"))
    return _stop(s, data)
