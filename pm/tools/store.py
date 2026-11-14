"""The ticket store: the log, replay and the one write path."""
import os
import sys


def unbuilt(name):
    path = os.environ.get("PM_UNBUILT_LOG")
    if path:
        with open(path, "a") as f:
            f.write(name + "\n")
    sys.stderr.write("pm: %s is not built yet.\n" % name)
    sys.exit(70)
