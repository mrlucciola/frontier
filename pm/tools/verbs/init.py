"""pm ticket init: create a ticket store in a repo root."""
import hashlib
import json
import os
import re

from store import STORE_DIR, TICKET_FILE, TicketError

PREFIX_RE = re.compile(r"^[a-z][a-z0-9]{1,7}$")

GITIGNORE_LINES = [
    "# pm archive: local history, not repo content (R2 amendment 2026-09-14).",
    "# Contents excluded rather than the directory, so the index can be",
    "# re-included -- git cannot re-include a file whose parent directory is",
    "# itself excluded.",
    ".pm/archive/*",
    "!.pm/archive/archive-index.jsonl",
    "# .pm/lock is local bookkeeping, not repo content (spec v2 section 1).",
    ".pm/lock",
]

FOOTPRINT = "Work items live in the ticket store -- use pm ticket."


def register(subparsers):
    sp = subparsers.add_parser("init", help="create a ticket store in a repo root")
    sp.add_argument("--prefix", required=True, help="ticket id prefix, unique per repo")
    sp.add_argument("--dir", default=None, help="repo root (default: --store, else cwd)")


def write_gitignore(repo_dir):
    path = os.path.join(repo_dir, ".gitignore")
    existing = ""
    if os.path.exists(path):
        with open(path) as f:
            existing = f.read()
    if ".pm/archive/*" in existing:
        return
    with open(path, "a") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n".join(GITIGNORE_LINES) + "\n")


def run(args):
    store_arg = getattr(args, "repo", None)
    if store_arg and args.dir and os.path.abspath(store_arg) != os.path.abspath(args.dir):
        raise TicketError("init: --store and --dir name different repo roots; pass one")
    repo_dir = os.path.abspath(store_arg or args.dir or ".")
    root = os.path.join(repo_dir, STORE_DIR)
    if os.path.isdir(root):
        raise TicketError(f"store already exists: {root}")
    if not PREFIX_RE.match(args.prefix):
        raise TicketError(f"invalid prefix {args.prefix!r}: must match ^[a-z][a-z0-9]{{1,7}}$")
    os.makedirs(root)
    config = {"prefix": args.prefix, "spec_version": 2,
              "store_id": hashlib.sha256((args.prefix + "|").encode()).hexdigest()[:12],
              "created_by": os.environ.get("PM_AGENT") or None}
    with open(os.path.join(root, "config.json"), "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)
        f.write("\n")
    open(os.path.join(root, TICKET_FILE), "w").close()
    open(os.path.join(root, "lock"), "w").close()
    write_gitignore(repo_dir)
    print(f"initialized {root} (prefix: {args.prefix})")
    print(FOOTPRINT)
