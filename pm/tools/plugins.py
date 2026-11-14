"""Plugins: directories of executables found by name. The one place that runs them."""
import os
import subprocess
import sys

import render


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
    return [p for p in (find(n, file) for n in names()) if p]


def any_pre():
    for n in names():
        try:
            files = os.listdir(os.path.join(root(), n))
        except OSError:
            continue
        if any(f.startswith("pre-") and find(n, f) for f in files):
            return True
    return False


def name_of(path):
    return os.path.basename(os.path.dirname(path))


def could_not_run(path, err):
    return "plugin %s could not run %s: %s." % (
        name_of(path), os.path.basename(path), err.strerror or err)


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
    try:
        return subprocess.call([path] + list(args), env=env)
    except OSError as e:
        render.refuse(could_not_run(path, e))


def run_hook(path, env, merge=False):
    """(exit code, output). Output is stdout, with stderr folded in when merge is set."""
    out = subprocess.run([path], env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT if merge else None,
                         universal_newlines=True, errors="replace")
    return out.returncode, out.stdout


def orient_text(s):
    parts = []
    env = dict(os.environ, PM_STORE=s.root)
    for path in with_file("orient"):
        try:
            out = subprocess.run([path], env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, universal_newlines=True,
                                 errors="replace")
        except OSError as e:
            sys.stderr.write("pm: warning: %s\n" % could_not_run(path, e))
            continue
        text = out.stdout
        if out.returncode != 0 or out.stderr:
            sys.stderr.write("pm: warning: plugin %s orient failed.\n" % name_of(path))
        if out.returncode == 0 and text.strip():
            parts.append(text.rstrip("\n"))
    return "\n".join(parts)
