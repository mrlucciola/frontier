#!/usr/bin/python3
"""Print an ICM workspace's stage states and its one next action. Read-only.

Usage: state.py [<dir>] [--json]   (<dir> is the workspace root or a folder inside one stage)
"""
import argparse
import json
import sys
from pathlib import Path

# The skill directory is a linked source checkout; importing must not write bytecode into it.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace import workspace_state  # noqa: E402


def render(st):
    if st["root"] is None:
        return st["next"]
    lines = [f"ICM workspace: {st['root']}", f"entry: {st['entry']}"]
    for r in st["stages"]:
        detail = list(r["detail"])
        if r.get("waiting_on"):
            detail.append(f"waiting on {r['waiting_on']}")
        outs = f" [{', '.join(r['outputs'])}]" if r["outputs"] else ""
        tail = f" - {'; '.join(detail)}" if detail else ""
        lines.append(f"  {r['stage']}  {r['state']}{outs}{tail}")
    lines.append(f"next: {st['next']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Print ICM stage states and the next action.")
    ap.add_argument("dir", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    st = workspace_state(Path(a.dir))
    print(json.dumps(st, indent=1) if a.json else render(st))
    return 0 if st["root"] else 1


if __name__ == "__main__":
    sys.exit(main())
