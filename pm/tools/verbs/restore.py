"""usage: pm restore

Bring the log back from its git backup. Inside a git checkout every change stores the
log as one blob at refs/pm/log; restore writes that blob back when the log is missing
or has fewer events than the backup, and refuses when there is nothing to gain.
"""
import os

import render
import store


def _count(data):
    return len([line for line in data.splitlines() if line.strip()])


def run(argv):
    render.parser(__doc__).parse_args(argv)
    s, _ = store.locate_dir()
    if s is None:
        render.refuse("no store here. Start one: pm init <prefix>")
    if not store.in_checkout(s.root):
        render.refuse("this store is not in a git checkout, so it has no backup.")
    try:
        blob = store.backup_blob(s)
    except (OSError, RuntimeError) as e:
        render.refuse("cannot read the backup: %s." % ((str(e).splitlines() or ["unknown"])[0]))
    if blob is None:
        render.refuse("there is no backup at refs/pm/log.")
    try:
        with open(s.log, "rb") as f:
            have = _count(f.read())
    except OSError:
        have = 0
    saved = _count(blob)
    if have >= saved:
        render.refuse("the log has %d event%s and the backup has %d. Nothing to restore."
                      % (have, "" if have == 1 else "s", saved))
    tmp = s.log + ".restore"
    with open(tmp, "wb") as f:
        f.write(blob)
    os.replace(tmp, s.log)
    print("restored %d event%s from refs/pm/log" % (saved, "" if saved == 1 else "s"))
    return 0
