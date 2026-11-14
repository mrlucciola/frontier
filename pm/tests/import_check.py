"""Check pm import against every registered store: the installed pm's view of a copy
of the store, and this component's pm after `pm import` on another copy, must agree.

Copies live under this worktree's .tmp/. No real store, ~/.config/pm or ~/frontier is
written. Prints each difference; exits 0 only when every store matches.
"""
import json
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PM = os.path.join(ROOT, "pm", "cli", "pm")
WORK = os.path.join(ROOT, ".tmp", "import-check")
LIST = os.path.expanduser("~/frontier/runtime-tools/pm/stores.json")
MAX_SHOWN = 15
STATUS = {"open": "open", "claimed": "taken", "done-unmerged": "parked", "closed": "done"}


def bare(target):
    return target.split("/", 1)[1] if target and "/" in target else target


def actor(identity):
    if not identity:
        return None
    rest = identity.split(":", 1)[1] if ":" in identity else identity
    name, _, token = rest.partition("#")
    name = name.rsplit("/", 1)[-1]
    return "%s#%s" % (name, token) if token else name


def findings(value):
    if not value:
        return None
    value = [bare(v) for v in value]
    return "none" if value == ["none"] else value


def run(cmd, cwd, env, **kw):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, universal_newlines=True, **kw)


def read_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def expected(rows, subtasks_of):
    """{id: the fields the new pm must show} for every ticket of the old store."""
    out = {}
    for r in rows:
        status = STATUS.get(r["status"], "open")
        done = status == "done"
        reason = r.get("closure_reason")
        hold = r.get("hold")
        out[r["id"]] = {
            "title": r.get("title") or "", "body": r.get("body") or "",
            "kind": "epic" if r.get("kind") == "epic" else "task",
            "pri": r.get("priority"), "under": bare(r.get("parent")),
            "labels": list(r.get("labels") or []), "status": status,
            "holder": actor(r.get("assignee")) if status == "taken" else None,
            "hold": hold.get("reason") if status == "taken" and isinstance(hold, dict) else None,
            "findings": findings(r.get("findings")) if done else None,
            "reason": reason if done and reason not in (None, "done") else None,
            "notes": [[n.get("ts"), n.get("kind"), n.get("text")] for n in r.get("notes") or []
                      if n.get("kind") != "edit-trail" and n.get("text")],
            "blocked_by": set(bare(e["to"]) for e in r.get("edges") or []
                              if e.get("type") == "blocked-by"),
            "related": set(bare(e["to"]) for e in r.get("edges") or []
                           if e.get("type") == "related"),
            "from": next((bare(e["to"]) for e in r.get("edges") or []
                          if e.get("type") == "discovered-from"), None),
            "created": r.get("created"),
        }
    for r in rows:
        for e in r.get("edges") or []:
            to = bare(e.get("to"))
            if to not in out:
                continue
            if e.get("type") == "blocks":
                out[to]["blocked_by"].add(r["id"])
            elif e.get("type") == "related":
                out[to]["related"].add(r["id"])
    for r in rows:
        for sub in r.get("subtasks") or []:
            out[sub["id"]] = {
                "title": sub.get("title") or "", "body": "", "kind": "task", "pri": 2,
                "under": r["id"], "labels": [], "status": "done", "holder": None,
                "hold": None, "findings": findings(sub.get("findings")),
                "reason": sub.get("reason") if sub.get("reason") not in (None, "done") else None,
                "notes": [[sub.get("closed"), None, sub["note"]]] if sub.get("note") else [],
                "blocked_by": set(), "related": set(), "from": None,
                "created": r.get("created"),
            }
    return out


def got(row):
    return {
        "title": row["title"], "body": row["body"], "kind": row["kind"], "pri": row["pri"],
        "under": row["under"], "labels": row["labels"], "status": row["status"],
        "holder": row["holder"], "hold": row["hold"], "findings": row["findings"],
        "reason": row["reason"],
        "notes": [[n["ts"], n["kind"], n["text"]] for n in row["notes"]],
        "blocked_by": set(row["blocked_by"]), "related": set(row["related"]),
        "from": row["from"], "created": row["created"],
    }


def check_store(index, path):
    src = os.path.join(path, ".pm")
    if not os.path.isfile(os.path.join(src, "tickets.jsonl")):
        return None, ["no readable %s" % os.path.join(src, "tickets.jsonl")]
    base = os.path.join(WORK, str(index))
    dirs = {}
    for name in ("old", "new"):
        dirs[name] = os.path.join(base, name)
        os.makedirs(dirs[name], exist_ok=True)
        dest = os.path.join(dirs[name], ".pm")
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    empty = os.path.join(base, "registry-empty")
    scratch = os.path.join(base, "registry-new")
    open(empty, "w").close()
    open(scratch, "w").close()
    env_old = dict(os.environ, PM_TELEMETRY_DIR="-", PM_STORES_FILE=empty,
                   GIT_DIR=os.path.join(base, "no-git"))
    env_new = dict(os.environ, PM_STORES=scratch, GIT_DIR=os.path.join(base, "no-git"))
    env_new.pop("PM_NOW", None)

    live = []
    for status in ("open", "claimed", "done-unmerged", "closed"):
        r = run(["pm", "ticket", "list", "--json", "--status", status], dirs["old"], env_old)
        if r.returncode != 0:
            return None, ["installed pm failed (%s): %s" % (status, r.stderr.strip())]
        live += json.loads(r.stdout)

    r = run(["/usr/bin/python3", "-B", PM, "import"], dirs["new"], env_new)
    if r.returncode != 0:
        return None, ["pm import failed: %s" % r.stderr.strip()]
    for line in r.stderr.splitlines():
        if "backup failed" in line:
            continue
        print("  note: %s" % line)
    r = run(["/usr/bin/python3", "-B", PM, "ls", "all", "-n", "0", "--json"], dirs["new"], env_new)
    if r.returncode != 0:
        return None, ["pm ls failed: %s" % r.stderr.strip()]
    new_rows = {}
    for line in r.stdout.splitlines():
        if line.strip():
            row = json.loads(line)
            new_rows[row["id"]] = row

    rows = list(live)
    seen = set(x["id"] for x in rows)
    for f in sorted(glob.glob(os.path.join(src, "archive", "tickets-*.jsonl"))):
        for row in read_rows(f):
            if row["id"] not in seen:
                seen.add(row["id"])
                rows.append(row)
    want = expected(rows, None)

    diffs = []
    for tid in sorted(set(want) - set(new_rows)):
        diffs.append("%s: missing after import" % tid)
    for tid in sorted(set(new_rows) - set(want)):
        diffs.append("%s: not in the old store" % tid)
    for tid in sorted(set(want) & set(new_rows)):
        have = got(new_rows[tid])
        for key in sorted(want[tid]):
            if want[tid][key] != have[key]:
                diffs.append("%s %s: old %r, new %r" % (tid, key, want[tid][key], have[key]))
    return len(want), diffs


def main():
    with open(LIST) as f:
        entries = json.load(f)["stores"]
    failed = 0
    for index, entry in enumerate(entries):
        path = os.path.expanduser(entry["path"])
        try:
            count, diffs = check_store(index, path)
        except (OSError, ValueError, KeyError) as e:
            count, diffs = None, ["%s: %s" % (type(e).__name__, e)]
        if diffs:
            failed += 1
            print("DIFF %s (%d)" % (path, len(diffs)))
            for d in diffs[:MAX_SHOWN]:
                print("  " + d)
            if len(diffs) > MAX_SHOWN:
                print("  ... %d more" % (len(diffs) - MAX_SHOWN))
        else:
            print("ok   %s (%d tickets)" % (path, count))
    print("stores: %d, differing: %d" % (len(entries), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
