#!/usr/bin/python3
"""Golden diff: old pm ticket CLI vs the new one on the live stores (read-only).

Exit 0 all same, 1 any DIFF, 2 any unruled SKIP (unless 1 already by DIFF).

`summary` catches up an owed history snapshot, which writes, so it is skipped on a
store holding `.pm/history-pending`. A `deferred` marker comes from
`history_interval_seconds`, a feature the rewrite defers (pm/docs/cut-list.md), so
that skip is ruled and does not fail the run; the store's other verbs are compared.
"""
import json
import os
import subprocess
import sys

REGISTRY = "/Users/matthias/frontier/runtime-tools/pm/stores.json"
OLD = "/Users/matthias/frontier/runtime-tools/pm/ticket/src/ticket"
NEW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "ticket")
SHOW_LIMIT = 5


def run(cli, repo, argv):
    env = dict(os.environ, PM_STORES_FILE=REGISTRY, PM_TELEMETRY_DIR="-")
    p = subprocess.run([sys.executable, "-B", cli, "--store", repo, *argv],
                       capture_output=True, text=True, env=env, timeout=120)
    return p.returncode, p.stdout


def first_diff(a, b):
    al, bl = a.splitlines(), b.splitlines()
    for i in range(max(len(al), len(bl))):
        x = al[i] if i < len(al) else "<end>"
        y = bl[i] if i < len(bl) else "<end>"
        if x != y:
            return f"line {i + 1}: old={x!r} new={y!r}"
    return "trailing newline differs"


def readable(repo):
    return os.path.isdir(repo) and os.access(repo, os.R_OK | os.X_OK) and os.access(
        os.path.join(repo, ".pm"), os.R_OK | os.X_OK)


def main():
    with open(REGISTRY) as f:
        stores = [os.path.expanduser(s["path"]) for s in json.load(f)["stores"]]
    counts = dict(stores=0, comparisons=0, same=0, DIFF=0, SKIP=0, ruled=0)
    for repo in stores:
        try:
            if not readable(repo):
                print(f"SKIP {repo}: repo or .pm not readable")
                counts["SKIP"] += 1
                continue
            marker = os.path.join(repo, ".pm", "history-pending")
            pending = None
            if os.path.exists(marker):
                with open(marker) as f:
                    pending = f.read().strip()
        except OSError as e:
            print(f"SKIP {repo}: {e}")
            counts["SKIP"] += 1
            continue
        counts["stores"] += 1
        cases = [["ready"], ["list"], ["stores", "--check"]]
        if pending is None:
            cases.insert(0, ["summary"])
        elif pending.startswith("deferred"):
            print(f"SKIP {repo} summary: deferred history marker; "
                  "history_interval_seconds is deferred (ruled)")
            counts["ruled"] += 1
        else:
            print(f"SKIP {repo} summary: .pm/history-pending fault marker (summary would commit)")
            counts["SKIP"] += 1
        rc, out = run(OLD, repo, ["list", "--json"])
        ids = []
        if rc == 0:
            try:
                data = json.loads(out)
                rows = data if isinstance(data, list) else data.get("tickets", [])
                ids = [r["id"] for r in rows if isinstance(r, dict) and "id" in r][:SHOW_LIMIT]
            except (ValueError, AttributeError):
                pass
        cases += [["show", i] for i in ids]
        for argv in cases:
            counts["comparisons"] += 1
            label = f"{repo} {' '.join(argv)}"
            try:
                old = run(OLD, repo, argv)
                new = run(NEW, repo, argv)
            except subprocess.TimeoutExpired:
                print(f"DIFF {label}: timeout")
                counts["DIFF"] += 1
                continue
            if old == new:
                print(f"same {label}")
                counts["same"] += 1
            else:
                counts["DIFF"] += 1
                if old[0] != new[0]:
                    print(f"DIFF {label}: exit old={old[0]} new={new[0]}; {first_diff(old[1], new[1])}")
                else:
                    print(f"DIFF {label}: {first_diff(old[1], new[1])}")
    print("golden_diff: stores {stores}, comparisons {comparisons}, same {same}, "
          "DIFF {DIFF}, SKIP {SKIP}, ruled skips {ruled}".format(**counts))
    if counts["DIFF"]:
        return 1
    return 2 if counts["SKIP"] else 0


if __name__ == "__main__":
    sys.exit(main())
