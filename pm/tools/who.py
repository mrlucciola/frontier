"""Who is acting: the actor name, the session token and the "yours" test."""
import hashlib
import os


def actor(as_name=None):
    if as_name:
        return as_name
    if os.environ.get("PM_ACTOR"):
        return os.environ["PM_ACTOR"]
    if os.environ.get("CLAUDE_CODE_SESSION_ID"):
        return "claude"
    if os.environ.get("CODEX_THREAD_ID"):
        return "codex"
    return os.environ.get("USER") or "unknown"


def token():
    for name in ("PM_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID"):
        sid = os.environ.get(name)
        if sid:
            return hashlib.sha256(sid.encode("utf-8")).hexdigest()[:8]
    return None


def by(as_name=None):
    tok = token()
    name = actor(as_name)
    return "%s#%s" % (name, tok) if tok else name


def actor_of(by_value):
    return by_value.split("#", 1)[0]


def yours(holder_by):
    if not holder_by:
        return False
    mine = token()
    theirs = holder_by.split("#", 1)[1] if "#" in holder_by else None
    if mine is None and theirs is None:
        return actor_of(holder_by) == actor()
    return mine == theirs
