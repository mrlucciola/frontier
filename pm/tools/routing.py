"""Store registry and prefix routing: which store owns an id, which stores are frozen.

Layout and rules are spec v2 sections 3 and 4 (pm/docs/spec/v2/SPEC.md). Reads
tolerate a bad registry; mutations fail closed on it. This module imports `store`
at load time; `store` imports it only inside functions.
"""
import json
import os

import store as st
from store import TicketError, owned_prefixes, ref_prefix

NO_OWNER_TAIL = ("add the repo to ~/frontier/runtime-tools/pm/stores.json "
                 "and deploy pm")


def registry_path():
    """`PM_STORES_FILE`, else `~/.config/pm/stores.json`."""
    return os.environ.get("PM_STORES_FILE") or os.path.join(
        os.path.expanduser("~"), ".config", "pm", "stores.json")


def _store_dir(repo):
    cand = os.path.join(repo, st.STORE_DIR)
    return cand if os.path.isdir(cand) else None


def store_owns(root, prefix):
    """True when the store at `root` owns `prefix` (reads its config.json only)."""
    try:
        with open(os.path.join(root, "config.json")) as f:
            return prefix in owned_prefixes(json.load(f))
    except (OSError, ValueError):
        return False


def load_registry():
    """Registry entries as [{path, role, store, config, error, successor}].

    No file and no symlink at the registry path is an empty registry; a dangling
    symlink is an error."""
    src = registry_path()
    try:
        with open(src) as f:
            data = json.load(f)
    except FileNotFoundError as e:
        if not os.path.lexists(src):
            return []
        raise TicketError(f"cannot read store registry {src}: {e}")
    except (OSError, ValueError) as e:
        raise TicketError(f"cannot read store registry {src}: {e}")
    entries = data.get("stores") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise TicketError(f"store registry {src}: expected {{\"stores\": [...]}}")
    out = []
    for raw in entries:
        if not isinstance(raw, dict) or not isinstance(raw.get("path"), str):
            raise TicketError(f"store registry {src}: every entry needs a string 'path'")
        role = raw.get("role", "live")
        if role not in ("live", "frozen"):
            raise TicketError(
                f"store registry {src}: role {role!r} of {raw['path']} must be "
                "live or frozen")
        path = os.path.abspath(os.path.expanduser(raw["path"]))
        e = {"path": path, "role": role, "store": _store_dir(path), "config": None,
             "error": None, "successor": raw.get("successor")}
        if e["store"] is None:
            e["error"] = f"no .pm store at {path}"
        else:
            try:
                with open(os.path.join(e["store"], "config.json")) as f:
                    cfg = json.load(f)
                if not isinstance(cfg, dict) or not isinstance(cfg.get("prefix"), str):
                    e["error"] = f"{e['store']}/config.json has no string 'prefix'"
                else:
                    e["config"] = cfg
            except (OSError, ValueError) as ex:
                e["error"] = f"cannot read {e['store']}/config.json: {ex}"
        out.append(e)
    return out


class Resolved:
    """`role` is None for a store found through the cwd: its role is looked up
    lazily, and only for a mutation."""

    def __init__(self, root, role="live"):
        self.root = root
        self.role = role
        self.repo = os.path.dirname(os.path.abspath(root))


def cwd_store_role(root):
    """Role of the store at `root` from the registry file alone. Fails closed: a
    registry that exists but cannot be read, has the wrong shape, or carries a
    role other than `live`/`frozen` on any entry raises TicketError. No file and no
    symlink means no frozen stores."""
    src = registry_path()
    real = os.path.realpath(os.path.dirname(os.path.abspath(root)))
    refused = "mutations are refused while a frozen store cannot be ruled out"
    try:
        with open(src) as f:
            data = json.load(f)
    except FileNotFoundError as e:
        if not os.path.lexists(src):
            return "live"
        raise TicketError(f"cannot read store registry {src}: {e}; {refused}")
    except (OSError, ValueError) as e:
        raise TicketError(f"cannot read store registry {src}: {e}; {refused}")
    entries = data.get("stores") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise TicketError(
            f"store registry {src}: expected {{\"stores\": [...]}}; mutations are refused")
    found = "live"
    for raw in entries:
        if not isinstance(raw, dict) or not isinstance(raw.get("path"), str):
            raise TicketError(
                f"store registry {src}: every entry needs a string 'path'; "
                "mutations are refused")
        role = raw.get("role", "live")
        if role not in ("live", "frozen"):
            raise TicketError(
                f"store registry {src}: role {role!r} of {raw['path']} must be "
                "exactly 'live' or 'frozen'; mutations are refused")
        if os.path.realpath(os.path.expanduser(raw["path"])) == real and role == "frozen":
            found = "frozen"
    return found


def registry_entry(root):
    """Raw registry entry for the store at `root` (a frozen one wins), or None.
    Tolerant: an unreadable or malformed registry is "no entry"."""
    real = os.path.realpath(os.path.dirname(os.path.abspath(root)))
    found = None
    try:
        with open(registry_path()) as f:
            entries = json.load(f)["stores"]
        for raw in entries:
            if os.path.realpath(os.path.expanduser(raw["path"])) == real:
                if raw.get("role") == "frozen":
                    return raw
                found = found or raw
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return found


def frozen_notice(root):
    """One line for a store registered frozen, else None."""
    entry = registry_entry(root)
    if not entry or entry.get("role") != "frozen":
        return None
    repo = os.path.dirname(os.path.abspath(root))
    succ = entry.get("successor")
    tail = f"; work is in {succ}/.pm" if isinstance(succ, str) and succ else ""
    return f"store {repo} is frozen{tail}"


def refuse_if_frozen(root):
    """Raise TicketError when the store at `root` is registered frozen or the
    registry cannot be trusted. Called on mutations only."""
    if cwd_store_role(root) != "frozen":
        return
    repo = os.path.dirname(os.path.abspath(root))
    succ = (registry_entry(root) or {}).get("successor")
    if isinstance(succ, str) and succ:
        raise TicketError(
            f"store {repo} is frozen (read-only in {registry_path()}); "
            f"mutations are refused; use {succ}/.pm")
    owners = []
    try:
        with open(os.path.join(root, "config.json")) as f:
            own = owned_prefixes(json.load(f))
        with open(registry_path()) as f:
            entries = json.load(f)["stores"]
        for raw in entries:
            if raw.get("role", "live") == "frozen":
                continue
            p = os.path.abspath(os.path.expanduser(raw["path"]))
            d = _store_dir(p)
            if d and store_owns(d, own[0] if own else ""):
                owners.append(p)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    hint = (f"; the live store for its prefix is {owners[0]}" if owners
            else "; pass --store <live repo> to write elsewhere")
    raise TicketError(
        f"store {repo} is frozen (read-only in {registry_path()}); "
        f"mutations are refused{hint}")


def _dedupe_owners(entries):
    seen, out = set(), []
    for e in entries:
        key = os.path.realpath(e["store"]) if e["store"] else e["path"]
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def owners_by_prefix(entries):
    """{prefix: {"live": [entries], "frozen": [entries]}}, deduped by realpath."""
    out = {}
    for e in entries:
        if not e["config"]:
            continue
        for pfx in owned_prefixes(e["config"]):
            out.setdefault(pfx, {"live": [], "frozen": []})[e["role"]].append(e)
    for roles in out.values():
        for k in roles:
            roles[k] = _dedupe_owners(roles[k])
    return out


def resolve_store(ref, explicit=None, cwd=None, read=False, _ctx=None):
    """The store owning ticket id `ref`.

    1. `explicit` (--store/--repo): that store, unchanged.
    2. The cwd store, when it owns the prefix.
    3. Registry entries whose config owns the prefix; live beats frozen.
    4. With `read=True`, a row the live owner lacks falls back to a frozen owner
       that has it.
    Raises TicketError on a collision or when nothing owns the prefix."""
    if explicit:
        root = st.find_store(explicit)
        if not root:
            raise TicketError("no ticket store found (run: pm ticket init)")
        return Resolved(root, "live")
    prefix = ref_prefix(ref)
    if prefix is None:
        raise TicketError(f"cannot read a ticket prefix from {ref!r}")
    tid = ref.rpartition("/")[2]
    ctx = _ctx if _ctx is not None else {}

    def registry():
        if "entries" not in ctx:
            ctx["entries"] = load_registry()
        return ctx["entries"]

    def frozen_with_row():
        for e in registry():
            if (e["role"] == "frozen" and e["config"]
                    and prefix in owned_prefixes(e["config"])
                    and tid in st.Store(e["store"]).by_id):
                return Resolved(e["store"], "frozen")
        return None

    if "cwd_root" not in ctx:
        ctx["cwd_root"] = st.find_store(cwd)
        ctx["owned"] = []
        if ctx["cwd_root"]:
            try:
                with open(os.path.join(ctx["cwd_root"], "config.json")) as f:
                    ctx["owned"] = owned_prefixes(json.load(f))
            except (OSError, ValueError):
                pass
    cwd_root = ctx["cwd_root"]
    if cwd_root and prefix in ctx["owned"]:
        # Opens no registry, except to find a frozen row for a read the cwd store
        # lacks; a registry that fails there never fails the read.
        if read:
            if "cwd_store" not in ctx:
                ctx["cwd_store"] = st.Store(cwd_root)
            if tid not in ctx["cwd_store"].by_id:
                try:
                    found = frozen_with_row()
                except TicketError:
                    found = None
                if found:
                    return found
        return Resolved(cwd_root, None)
    owners = owners_by_prefix(registry()).get(prefix, {"live": [], "frozen": []})
    live, frozen = owners["live"], owners["frozen"]
    if len(live) > 1:
        raise TicketError(
            f"prefix '{prefix}' is owned by two registered stores: "
            f"{live[0]['path']}, {live[1]['path']}; fix "
            "runtime-tools/pm/stores.json or pass --store")
    if len(live) == 1:
        if read and tid not in st.Store(live[0]["store"]).by_id:
            found = frozen_with_row()
            if found:
                return found
        return Resolved(live[0]["store"], "live")
    if len(frozen) == 1:
        return Resolved(frozen[0]["store"], "frozen")
    if len(frozen) > 1:
        raise TicketError(
            f"prefix '{prefix}' is owned by two registered stores: "
            f"{frozen[0]['path']}, {frozen[1]['path']}; fix "
            "runtime-tools/pm/stores.json or pass --store")
    raise TicketError(
        f"no registered store owns prefix '{prefix}'; pass --store <repo>, or "
        f"{NO_OWNER_TAIL}")


def route_ids(ids, explicit=None, cwd=None, mutate=False):
    """Repo to pass as `repo=` for a verb taking `ids`, or None to leave the
    default (cwd store) alone. All ids must resolve to one store; a mutation routed
    to a frozen store is refused. Ids with no readable prefix are left to the
    verb's own error."""
    if explicit:
        return None
    resolved = []
    ctx = {}
    for i in ids:
        if ref_prefix(i) is None:
            continue
        resolved.append((i, resolve_store(i, None, cwd, read=not mutate, _ctx=ctx)))
    if not resolved:
        return None
    roots = {os.path.realpath(r.root) for _, r in resolved}
    if len(roots) > 1:
        by_root = {}
        for i, r in resolved:
            by_root.setdefault(r.repo, []).append(i)
        detail = "; ".join(f"{repo}: {', '.join(v)}" for repo, v in by_root.items())
        raise TicketError(
            f"ids belong to different stores ({detail}); run one call per store")
    first = resolved[0][1]
    if mutate and first.role is None:
        first.role = cwd_store_role(first.root)
    if mutate and first.role == "frozen":
        succ = (registry_entry(first.root) or {}).get("successor")
        use = f"; use {succ}/.pm" if isinstance(succ, str) and succ else ""
        raise TicketError(
            f"store {first.repo} is frozen (read-only in "
            f"runtime-tools/pm/stores.json); mutations are refused{use}")
    if ctx.get("cwd_root") and os.path.realpath(ctx["cwd_root"]) == next(iter(roots)):
        return None
    return first.repo


# --- cross-store rows: read-only, no foreign lock ---

def _row_state(other, tid):
    t = other.by_id.get(tid)
    if t:
        return {"status": t.get("status"), "title": t.get("title"), "reason": None}
    if tid in other.archived_ids():
        return {"status": "closed", "title": None, "reason": None}
    if tid in other.compacted:
        return {"status": "closed", "title": other.compacted[tid][1].get("title"),
                "reason": None}
    return {"status": None, "title": None,
            "reason": f"unresolved: no ticket {tid} in "
                      f"{os.path.dirname(os.path.abspath(other.root))}"}


def cross_target(store, ref):
    """State of a cross-store id `<prefix>/<id>` as {status, title, reason}:
    `reason` is set (and `status` None) when the target does not resolve. Cached
    on the store; foreign stores are opened without the flock."""
    cache = store.cross_cache
    if ref in cache["targets"]:
        return cache["targets"][ref]
    cache["targets"][ref] = state = _resolve_cross(store, ref)
    return state


def _resolve_cross(store, ref):
    prefix, sep, tid = ref.rpartition("/")
    if not sep or not prefix or not tid:
        return {"status": None, "title": None,
                "reason": f"unresolved: {ref!r} is not <prefix>/<id>"}
    if prefix in owned_prefixes(store.config) and (
            prefix == store.config.get("prefix") or tid in store.by_id
            or tid in store.archived_ids() or tid in store.compacted):
        return _row_state(store, tid)
    repo = os.path.dirname(os.path.abspath(store.root))
    try:
        r = resolve_store(ref, None, repo, read=True, _ctx=cache_ctx(store))
        key = os.path.realpath(r.root)
        foreign = store.cross_cache["stores"]
        other = foreign.get(key)
        if other is None:
            other = foreign[key] = st.Store(r.root)
    except TicketError as e:
        return {"status": None, "title": None,
                "reason": "unresolved: " + str(e).split(";")[0]}
    except (OSError, ValueError) as e:
        return {"status": None, "title": None,
                "reason": f"unresolved: cannot read the store for {ref}: {e}"}
    return _row_state(other, tid)


def cache_ctx(store):
    return store.cross_cache["ctx"]


def cross_blockers(store, t):
    """[{ref, status, title, reason}] for every blocked-by edge on `t`. Opens
    nothing unless the row carries such an edge."""
    out = []
    for e in t.get("edges", []):
        if e.get("type") == "blocked-by" and isinstance(e.get("to"), str):
            out.append(dict(cross_target(store, e["to"]), ref=e["to"]))
    return out


def unsatisfied_cross(store, t):
    return [b for b in cross_blockers(store, t) if b["status"] != "closed"]


def cross_label(b):
    return f"{b['ref']} ({b['reason'] or b['status']})"


def cross_blocks_of(store, tid):
    """Rows in other live registry stores whose blocked-by edge names `tid`, as
    ["<prefix>/<id>"] (the reverse line `show` prints). Best effort: an unreadable
    registry or store contributes nothing."""
    ref = f"{ref_prefix(tid)}/{tid}"
    mine = os.path.realpath(store.root)
    try:
        entries = load_registry()
    except TicketError:
        return []
    out = []
    foreign = store.cross_cache["stores"]
    for e in entries:
        if e["role"] != "live" or not e["store"]:
            continue
        key = os.path.realpath(e["store"])
        if key == mine:
            continue
        try:
            other = foreign.get(key) or foreign.setdefault(key, st.Store(e["store"]))
        except (TicketError, OSError, ValueError):
            continue
        for row in other.tickets:
            if not isinstance(row, dict):
                continue
            if any(x.get("type") == "blocked-by" and x.get("to") == ref
                   for x in row.get("edges", []) if isinstance(x, dict)):
                out.append(f"{ref_prefix(row['id'])}/{row['id']}")
    return sorted(out)
