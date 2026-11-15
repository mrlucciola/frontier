"""The ticket store: the log, replay and the one write path."""
import atexit
import fcntl
import json
import os
import re
import subprocess
import sys
import time

import plugins
import registry
import render
import who

ID_RE = re.compile(r"^([a-z][a-z0-9]{0,7})-([A-Za-z0-9]+)$")
KEY_ORDER = ("ts", "by", "op", "id")


class Store:
    def __init__(self, root):
        self.root = root
        self.dir = os.path.join(root, ".pm")
        self.log = os.path.join(self.dir, "log.jsonl")
        self.config = {}
        try:
            with open(os.path.join(self.dir, "config.json")) as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.config = data
        except (OSError, ValueError):
            pass
        self.prefix = self.config.get("prefix", "")


def _ancestor(here, *names):
    while True:
        if any(os.path.isfile(os.path.join(here, ".pm", n)) for n in names):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def _main_root(here):
    try:
        out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=here,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             universal_newlines=True)
    except OSError:
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return os.path.dirname(os.path.realpath(os.path.join(here, out.stdout.strip())))


def _toplevel(here):
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=here,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             universal_newlines=True)
    except OSError:
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return os.path.realpath(out.stdout.strip())


def locate_dir(start=None):
    """(Store, True) when the log exists, (Store, False) when only a config does."""
    here = os.path.realpath(start or os.getcwd())
    root = _ancestor(here, "config.json", "log.jsonl")
    if root is not None and os.path.isfile(os.path.join(root, ".pm", "log.jsonl")):
        return Store(root), True
    if (root is None or _toplevel(root) == root) and in_checkout(here):
        main = _main_root(here)
        if main is not None and os.path.isfile(os.path.join(main, ".pm", "log.jsonl")):
            return Store(main), True
    if root is not None:
        return Store(root), False
    return None, False


def find(start=None):
    s, has_log = locate_dir(start)
    return s if has_log else None


def require():
    s, has_log = locate_dir()
    if s is None:
        render.refuse("no store here. Start one: pm init <prefix>")
    if not has_log:
        if os.path.isfile(os.path.join(s.dir, "tickets.jsonl")):
            render.refuse("this store has not been imported yet. Fill its log: pm import")
        render.refuse("this store's log is missing. Bring it back from its git backup: pm restore")
    return s


def now():
    return os.environ.get("PM_NOW") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read(s):
    try:
        with open(s.log, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    events = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _blank(event):
    return {
        "blocked_by": [], "blocks": [], "body": event.get("body") or "",
        "created": event.get("ts"), "findings": None, "from": None, "hold": None,
        "holder": None, "id": event["id"],
        "kind": "epic" if event.get("kind") == "epic" else "task",
        "labels": list(event.get("labels") or []), "notes": [],
        "pri": event["pri"] if isinstance(event.get("pri"), int) else 2,
        "reason": None, "related": [], "status": "open",
        "title": event.get("title") or "", "under": event.get("under"),
        "updated": event.get("ts"), "events": [],
    }


def _note(t, event, kind, text):
    t["notes"].append({"ts": event.get("ts"), "by": event.get("by"),
                       "kind": kind, "text": text})


def _settle(t, status):
    t["status"] = status
    t["hold"] = None
    if status != "taken":
        t["holder"] = None


def _apply(t, event, op):
    if op == "edit":
        for key in ("title", "body", "pri"):
            if key in event:
                t[key] = event[key]
        if "under" in event:
            t["under"] = event["under"]
        if event.get("label") and event["label"] not in t["labels"]:
            t["labels"].append(event["label"])
        if event.get("unlabel") in t["labels"]:
            t["labels"].remove(event["unlabel"])
    elif op == "take":
        _settle(t, "taken")
        t["holder"] = event.get("by")
        if event.get("from"):
            _note(t, event, "took over from %s" % who.actor_of(event["from"]), "")
    elif op == "hold":
        t["hold"] = event.get("text")
    elif op == "drop":
        _settle(t, "open")
        if event.get("text"):
            _note(t, event, "dropped", event["text"])
    elif op == "park":
        _settle(t, "parked")
        if event.get("text"):
            _note(t, event, "parked", event["text"])
    elif op == "done":
        _settle(t, "done")
        t["findings"] = event.get("findings")
        t["reason"] = event.get("reason")
        if event.get("text"):
            _note(t, event, "done", event["text"])
    elif op == "reopen":
        _settle(t, "open")
        t["findings"] = None
        t["reason"] = None
    elif op == "note":
        if event.get("text"):
            _note(t, event, event.get("kind"), event["text"])
    elif op == "link":
        rel, to = event.get("rel"), event.get("to")
        if rel == "from":
            t["from"] = to
        elif rel in ("blocked-by", "related"):
            key = "blocked_by" if rel == "blocked-by" else "related"
            if to not in t[key]:
                t[key].append(to)
    elif op == "unlink":
        to = event.get("to")
        for key in ("blocked_by", "related"):
            t[key] = [x for x in t[key] if x != to]
        if t["from"] == to:
            t["from"] = None


OPS = ("new", "edit", "take", "hold", "drop", "park", "done", "reopen",
       "note", "link", "unlink")


def replay(events):
    tickets = {}
    for event in events:
        op, tid = event.get("op"), event.get("id")
        if not isinstance(op, str) or not isinstance(tid, str):
            continue
        if op == "new":
            if tid not in tickets:
                tickets[tid] = _blank(event)
                tickets[tid]["events"].append(event)
            continue
        t = tickets.get(tid)
        if t is None or not (op in OPS or "." in op):
            continue
        t["events"].append(event)
        t["updated"] = event.get("ts")
        if op in OPS:
            _apply(t, event, op)
    for tid, t in tickets.items():
        t["blocks"] = [o["id"] for o in tickets.values() if tid in o["blocked_by"]]
        for o in tickets.values():
            if tid in o["related"] and o["id"] not in t["related"]:
                t["related"].append(o["id"])
    return tickets


def ticket(s, tickets, word):
    if word is None:
        held = [t for t in tickets.values()
                if t["status"] == "taken" and who.yours(t["holder"])]
        if not held:
            render.refuse("you hold no ticket. Name one, or take one: pm take")
        if len(held) > 1:
            render.refuse("you hold %s. Name one." % ", ".join(t["id"] for t in held))
        return held[0]
    if word.isdigit():
        word = "%s-%s" % (s.prefix, word)
    m = ID_RE.match(word)
    if m and m.group(1) != s.prefix:
        if not registry.stores(m.group(1)):
            render.refuse("no store has prefix %s. Known: %s"
                          % (m.group(1), ", ".join(registry.known())))
        found = locate(m.group(1), word)
        if found:
            return found[1]
    elif word in tickets:
        return tickets[word]
    render.refuse("no ticket %s. Search: pm ls all <words>" % word)


def locate(prefix, tid):
    for path, _ in registry.stores(prefix):
        other = Store(path)
        if not os.path.isfile(other.log):
            continue
        t = replay(read(other)).get(tid)
        if t is not None:
            return other, t
    return None


def home(s, tid):
    m = ID_RE.match(tid or "")
    if m and m.group(1) != s.prefix:
        found = locate(m.group(1), tid)
        if found:
            return found[0]
    return s


def home_of(s, words):
    homes = {}
    for word in words:
        if word is None:
            continue
        if word.isdigit():
            word = "%s-%s" % (s.prefix, word)
        h = home(s, word)
        homes[h.root] = h
    if len(homes) > 1:
        render.refuse("%s are in different stores. Name them one store at a time."
                      % ", ".join(words))
    return next(iter(homes.values())) if homes else s


def next_id(s, tickets):
    n = len(tickets) + 1
    while "%s-%d" % (s.prefix, n) in tickets:
        n += 1
    return "%s-%d" % (s.prefix, n)


def is_done(tid, tickets):
    t = tickets.get(tid)
    if t is not None:
        return t["status"] == "done"
    m = ID_RE.match(tid or "")
    if m:
        found = locate(m.group(1), tid)
        if found:
            return found[1]["status"] == "done"
    return False


def open_blockers(t, tickets):
    return [b for b in t["blocked_by"] if not is_done(b, tickets)]


def blocked_elsewhere(tid, tickets):
    out = []
    pools = [tickets]
    for pre in registry.known():
        for path, _ in registry.stores(pre):
            other = Store(path)
            if os.path.isfile(other.log):
                pools.append(replay(read(other)))
    for pool in pools:
        for t in pool.values():
            if (tid in t["blocked_by"] and t["status"] != "done"
                    and t["id"] not in out):
                out.append(t["id"])
    return out


def _line(event):
    head = {k: event[k] for k in KEY_ORDER if k in event}
    rest = {k: event[k] for k in sorted(event) if k not in KEY_ORDER}
    head.update(rest)
    return json.dumps(head, separators=(",", ":"), ensure_ascii=False)


def in_checkout(path):
    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return True
        parent = os.path.dirname(path)
        if parent == path:
            return False
        path = parent


def _git(s, *args):
    out = subprocess.run(("git",) + args, cwd=s.root, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace").strip()
                           or "git %s failed" % args[0])
    return out.stdout


def backup_blob(s):
    """The log bytes stored at refs/pm/log, or None when there is no such ref."""
    try:
        subprocess.run(["git", "rev-parse", "--verify", "-q", "refs/pm/log"],
                       cwd=s.root, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return None
    return _git(s, "cat-file", "blob", "refs/pm/log")


def _backup(s):
    if not in_checkout(s.root):
        return
    try:
        sha = _git(s, "hash-object", "-w", ".pm/log.jsonl").decode().strip()
        _git(s, "update-ref", "refs/pm/log", sha)
    except (OSError, RuntimeError) as e:
        reason = (str(e).splitlines() or ["unknown"])[0]
        sys.stderr.write("pm: warning: backup failed: %s\n" % reason)


def _fill(events, actor):
    stamp, by = now(), who.by(actor)
    filled = []
    for event in events:
        event = dict(event)
        event.setdefault("ts", stamp)
        event.setdefault("by", by)
        filled.append(event)
    return filled


def _pre(s, filled, tickets):
    """True when at least one pre hook ran."""
    ran = False
    for event in filled:
        for path in plugins.with_file("pre-" + str(event["op"])):
            ran = True
            env = plugins.hook_env(s, event, tickets.get(event["id"]))
            try:
                code, text = plugins.run_hook(path, env, merge=True)
            except OSError as e:
                render.refuse(plugins.could_not_run(path, e))
            if code != 0:
                if not text.strip():
                    render.refuse("plugin %s refused %s %s." % (
                        plugins.name_of(path), event["op"], event["id"]))
                sys.stderr.write(text if text.endswith("\n") else text + "\n")
                sys.exit(1)
    return ran


_post_text = []


def _flush_post():
    if _post_text:
        sys.stdout.write("".join(_post_text))
        del _post_text[:]


def _post(s, filled, tickets):
    # Held until exit so hook output prints after the verb's own result.
    atexit.register(_flush_post)
    for event in filled:
        for path in plugins.with_file("post-" + str(event["op"])):
            env = plugins.hook_env(s, event, tickets.get(event["id"]))
            try:
                _code, text = plugins.run_hook(path, env)
            except OSError as e:
                sys.stderr.write("pm: warning: %s\n" % plugins.could_not_run(path, e))
                continue
            if text:
                _post_text.append(text if text.endswith("\n") else text + "\n")


def _same(a, b):
    def bare(events):
        return [{k: v for k, v in e.items() if k not in ("ts", "by")} for e in events]
    return bare(a) == bare(b)


def change(s, check, actor=None, dry_run=False, hooks=True):
    """Append what check returns. check may run twice (once for pre hooks outside the
    lock, once under it), so it must be pure. hooks=False skips every plugin hook."""
    frozen = registry.read_only_path(s.root)
    if frozen is not None:
        render.refuse("store %s is read-only (%s)." % (s.prefix, frozen))
    before = replay(read(s))
    checked = None
    if hooks and plugins.any_pre():
        checked = _fill(check(before), actor)
        if not _pre(s, checked, before):
            checked = None
    fd = os.open(s.log, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        tickets = replay(read(s))
        filled = _fill(check(tickets), actor)
        if checked is not None and not _same(checked, filled):
            render.refuse("the store changed while pm was checking. Run the command again.")
        written = bool(filled) and not dry_run
        if written:
            data = "".join(_line(e) + "\n" for e in filled).encode("utf-8")
            os.write(fd, data)
            _backup(s)
    finally:
        os.close(fd)
    if written and hooks:
        _post(s, filled, tickets)
    return filled
