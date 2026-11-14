"""pm ticket lint: validate plus body-path warnings and the pilot contract; `lint <id>` checks dispatch headings."""
import os
import re
import sys
from datetime import datetime, timezone

import store as st
from store import TicketError
from verbs import validate

HELP = ("validate, then WARN lines for stale or .local/ paths in open ticket bodies; "
        "pilot tickets must meet their contract (P-01/P-02); `lint <id>` checks a "
        "ticket has the dispatch headings")

#: A repo-relative path token: two or more `/`-joined segments, not a URL, absolute or `~/` path.
BODY_PATH_RE = re.compile(r"(?<![\w/.~:-])((?:[\w.-]+/)+[\w.-]*[\w])")
#: A home-relative or absolute user path (`~/...`, `/Users/<u>/...`, `/home/<u>/...`).
ABS_PATH_RE = re.compile(
    r"(?<![\w/.:-])((?:~|/Users/[\w.-]+|/home/[\w.-]+)/(?:[\w.-]+/)*[\w.-]*[\w])")
#: A body line naming a file it is about to create is not a stale citation.
PLANNED_RE = re.compile(r"\b(add|adds|added|new|create|creates)\b", re.I)
TRANSIENT_SEGMENTS = frozenset({".tmp", ".worktrees"})
LOCAL_DUMP_DIR = ".local"

DISPATCH_HEADINGS = (
    ("Done", ("Done", "Gate")),
    ("Writes", ("Writes", "Files")),
    ("Read first", ("Read first", "Inputs")),
    ("Do not", ("Do not", "Not in scope")),
)

PILOT_LABEL = "pilot"
REVIEW_BY_RE = re.compile(r"^\s*review_by:[ \t]*(\S*)", re.M)
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def register(subparsers):
    sp = subparsers.add_parser("lint", help=HELP, description=HELP)
    sp.add_argument("id", nargs="?", help="check this ticket for the dispatch headings instead")
    sp.add_argument("--workspace", help=".vscode/*.code-workspace to fan out over")
    sp.add_argument("--json", action="store_true")


def body_path_tokens(line, repo):
    """[(path as written, absolute path or None)] for each path on one body line, in text
    order. None: repo-relative but its first segment is not a directory at the repo root."""
    found = {}
    for m in BODY_PATH_RE.finditer(line):
        path = m.group(1).rstrip(".")
        first = path.split("/", 1)[0]
        if first in (".", ".."):
            continue
        is_path = first == LOCAL_DUMP_DIR or os.path.isdir(os.path.join(repo, first))
        found[m.start()] = (path, os.path.join(repo, path) if is_path else None)
    roots = sorted({repo, os.path.realpath(repo)}, key=len, reverse=True)
    repo_abs_re = re.compile(r"(?<![\w/.:-])((?:" + "|".join(map(re.escape, roots))
                             + r")/(?:[\w.-]+/)*[\w.-]*[\w])")
    for rx in (ABS_PATH_RE, repo_abs_re):
        for m in rx.finditer(line):
            path = m.group(1).rstrip(".")
            found.setdefault(m.start(), (path, os.path.expanduser(path)))
    return [found[k] for k in sorted(found)]


def body_path_warnings(store):
    """[(kind, ticket id, path)] over bodies of tickets that are not closed and not
    labelled `worker:codex`: `local-path` for a path under `.local/`, `stale-path` for a
    cited path that does not exist. Planned-file lines and `.tmp/`, `.worktrees/` paths
    are skipped."""
    repo = os.path.dirname(os.path.abspath(store.root))
    local_root = os.path.realpath(os.path.join(repo, LOCAL_DUMP_DIR))
    out = []
    for t in store.tickets:
        if not isinstance(t, dict) or t.get("status") == "closed" \
                or "worker:codex" in (t.get("labels") or []):
            continue
        seen = set()
        for line in str(t.get("body") or "").splitlines():
            planned = bool(PLANNED_RE.search(line))
            for path, resolved in body_path_tokens(line, repo):
                if path in seen or resolved is None \
                        or TRANSIENT_SEGMENTS.intersection(path.split("/")):
                    continue
                seen.add(path)
                norm = os.path.realpath(resolved)
                if norm == local_root or norm.startswith(local_root + os.sep):
                    out.append(("local-path", t.get("id"), path))
                elif not planned and not os.path.exists(resolved):
                    out.append(("stale-path", t.get("id"), path))
    return out


def missing_dispatch_headings(body):
    """Canonical names of the dispatch headings no body line starts with, as `<name>:`
    or an alias, case-insensitively, in canonical order."""
    lines = [line.lstrip().lower() for line in str(body or "").splitlines()]
    return [canon for canon, names in DISPATCH_HEADINGS
            if not any(line.startswith(n.lower() + ":")
                       for line in lines for n in names)]


def pilot_review_by(body):
    """(date or None, raw text or None): the first `review_by:` body line."""
    m = REVIEW_BY_RE.search(str(body or ""))
    if not m:
        return None, None
    raw = m.group(1)
    if not ISO_DATE_RE.match(raw):
        return None, raw
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date(), raw
    except ValueError:
        return None, raw


def pilot_problems(store, today=None):
    """[validate.Problem] for the pilot contract over every ticket labelled `pilot`: an
    open one needs a `review_by: YYYY-MM-DD` body line not in the past (P-01); a closed
    one needs notes starting `measured:` and `ruling:` (P-02)."""
    today = today or datetime.now(timezone.utc).date()
    problems = []
    for t in store.tickets:
        if not isinstance(t, dict) or PILOT_LABEL not in (t.get("labels") or []):
            continue
        tid = t.get("id")
        if t.get("status") == "closed":
            texts = [str(n.get("text") or "").lstrip().lower()
                     for n in (t.get("notes") or []) if isinstance(n, dict)]
            for prefix in ("measured", "ruling"):
                if not any(x.startswith(prefix + ":") for x in texts):
                    problems.append(validate.Problem(st.TICKET_FILE, None, tid, "P-02",
                        f"closed pilot ticket has no '{prefix}:' note",
                        f"operator: pm ticket note {tid} '{prefix}: <text>' "
                        "(ruling: promoted, rejected or extended)"))
            continue
        due, raw = pilot_review_by(t.get("body"))
        if due is None:
            what = "missing" if raw is None else f"unparsable ({raw!r})"
            problems.append(validate.Problem(st.TICKET_FILE, None, tid, "P-01",
                f"open pilot ticket review_by: line {what}",
                f"operator: add a body line 'review_by: YYYY-MM-DD' to {tid}"))
        elif due < today:
            problems.append(validate.Problem(st.TICKET_FILE, None, tid, "P-01",
                f"pilot review_by {due.isoformat()} is past",
                f"operator: rule {tid} (ruling: promoted, rejected or extended) "
                "and close it or set a new review_by"))
    return problems


def _openable(root):
    try:
        return st.Store(root)
    except (TicketError, OSError, ValueError):
        return None


def run_dispatch(args):
    store = st.open_store(args.repo)
    t = store.by_id.get(args.id)
    if t is None:
        raise TicketError(f"no such ticket: {args.id}; {st.NO_SUCH_TICKET_HINT}")
    missing = missing_dispatch_headings(t.get("body"))
    for heading in missing:
        print(f"missing: {heading}")
    if not missing:
        print("dispatchable")
    sys.exit(1 if missing else 0)


def run(args):
    if args.id:
        return run_dispatch(args)
    root = None if args.workspace else st.find_store(args.repo)
    store = _openable(root) if root else None
    result = validate.validate_one(root) if root else None
    if result and result["exit"] != 2:
        if store is not None:
            result["problems"] = sorted(result["problems"] + pilot_problems(store),
                                        key=lambda p: p.sort_key())
            result["exit"] = 1 if result["problems"] else 0
        validate.print_result(args.json, result)
        code = result["exit"]
    else:
        code = validate.run_code(args)
    if code in (0, 1) and store is not None:
        stream = sys.stderr if args.json else sys.stdout
        for kind, tid, path in body_path_warnings(store):
            print(f"WARN {kind} {tid} {path}", file=stream)
    sys.exit(code)
