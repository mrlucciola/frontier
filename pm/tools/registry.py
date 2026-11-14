"""The registry: which prefix lives in which store directory."""
import os


def path():
    return os.environ.get("PM_STORES") or os.path.expanduser("~/.config/pm/stores")


def read():
    try:
        with open(path()) as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        words = line.split()
        if len(words) >= 2:
            out.append((words[0], words[1], words[2:3] == ["ro"]))
    return out


def add(prefix, store_path):
    target = path()
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "a") as f:
        f.write("%s %s\n" % (prefix, store_path))
