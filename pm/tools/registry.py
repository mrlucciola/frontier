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
        words = line.strip().split(None, 1)
        if len(words) == 2:
            rest, ro = words[1], False
            if rest.endswith(" ro") and rest[:-3].strip():
                rest, ro = rest[:-3].strip(), True
            out.append((words[0], rest, ro))
    return out


def stores(prefix):
    return [(p, ro) for pre, p, ro in read() if pre == prefix]


def known():
    seen = []
    for pre, _, _ in read():
        if pre not in seen:
            seen.append(pre)
    return seen


def read_only_path(store_path):
    here = os.path.realpath(store_path)
    for _, p, ro in read():
        if ro and os.path.realpath(p) == here:
            return p
    return None


def add(prefix, store_path):
    target = path()
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "a") as f:
        f.write("%s %s\n" % (prefix, store_path))
