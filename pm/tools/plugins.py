"""Plugins: directories of executables found by name. The one place that runs them."""
import os
import subprocess


def root():
    return os.environ.get("PM_PLUGINS") or os.path.expanduser("~/.config/pm/plugins")


def names():
    try:
        found = os.listdir(root())
    except OSError:
        return []
    return sorted(n for n in found if os.path.isdir(os.path.join(root(), n)))


def find(name, file):
    path = os.path.join(root(), name, file)
    if os.path.isfile(path) and os.access(path, os.X_OK):
        return path
    return None


def with_file(file):
    return [(n, find(n, file)) for n in names() if find(n, file)]


def command(name):
    return find(name, "cmd") if name in names() else None


def hook_env(s, event, ticket):
    env = dict(os.environ)
    env.update({
        "PM_OP": str(event.get("op", "")),
        "PM_ID": str(event.get("id", "")),
        "PM_STORE": s.root,
        "PM_BY": str(event.get("by", "")),
        "PM_STATUS": ticket["status"] if ticket else "",
        "PM_TEXT": str(event.get("text") or ""),
        "PM_LABELS": " ".join((ticket or event).get("labels") or []),
    })
    return env


def run_command(path, args, s=None):
    env = dict(os.environ)
    if s is not None:
        env["PM_STORE"] = s.root
    return subprocess.call([path] + list(args), env=env)


def run_hook(path, env, merge=False):
    """(exit code, output). Output is stdout, with stderr folded in when merge is set."""
    out = subprocess.run([path], env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT if merge else None,
                         universal_newlines=True)
    return out.returncode, out.stdout


def orient_text():
    parts = []
    for _name, path in with_file("orient"):
        _code, text = run_hook(path, dict(os.environ))
        if text.strip():
            parts.append(text.rstrip("\n"))
    return "\n".join(parts)
