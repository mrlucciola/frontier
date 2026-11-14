"""usage: pm init prefix

Start a store in this directory: it creates .pm/ with a config and an empty log, and
registers the prefix so any directory can reach the store by its ids. A prefix is 1 to
8 lowercase letters or digits, starting with a letter, and belongs to one store.
"""
import os
import re

import registry
import render
import store

PREFIX_RE = re.compile(r"^[a-z][a-z0-9]{0,7}$")


def run(argv):
    p = render.parser(__doc__)
    p.add_argument("prefix", nargs="?")
    args = p.parse_args(argv)
    if not args.prefix:
        render.usage_error(__doc__, "init needs a prefix.")
    if not PREFIX_RE.match(args.prefix):
        render.usage_error(
            __doc__, "a prefix is 1 to 8 lowercase letters or digits, starting with a letter.")

    here = os.getcwd()
    pm_dir = os.path.join(here, ".pm")
    if os.path.exists(os.path.join(pm_dir, "log.jsonl")):
        render.refuse("this directory already has a store, prefix %s."
                      % store.Store(here).prefix)
    for prefix, path, _ in registry.read():
        if prefix == args.prefix:
            render.refuse("prefix %s belongs to %s. Choose another." % (prefix, path))

    os.makedirs(pm_dir, exist_ok=True)
    with open(os.path.join(pm_dir, "config.json"), "w") as f:
        f.write('{"prefix":"%s"}\n' % args.prefix)
    open(os.path.join(pm_dir, "log.jsonl"), "a").close()
    registry.add(args.prefix, here)
    print("ready: %s (%s)" % (args.prefix, pm_dir))
    print("For agents without hooks, add to AGENTS.md: Tickets live in .pm/. Run `pm`.")
    if _in_checkout(here):
        store.unbuilt("backup")
    return 0


def _in_checkout(path):
    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return True
        parent = os.path.dirname(path)
        if parent == path:
            return False
        path = parent
