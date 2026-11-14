"""pm ticket validate: check a store against spec v2 invariants I-01..I-19."""
import json
import os
import re
import shlex
import sys

import store as st

SPEC_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "..", "..", "docs", "spec", "v2")
STORE_ENTRIES = {"config.json", "tickets.jsonl", "lock", "migrate-report.md",
                 "archive", "history-pending"}
UPGRADE_REPORT_RE = re.compile(r"^upgrade-\d+-to-\d+\.md$")
TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
ARCHIVE_INDEX_ROW_KEYS = {"id", "title", "source", "closed", "path", "archived", "meta"}
OLD_PM_UPGRADE = "~/frontier/runtime-tools/pm/ticket/src/ticket upgrade"
BACKFILLABLE_KEYS = {"assignee": None, "body": "", "closure_reason": None,
                     "edges": [], "labels": [], "notes": [], "parent": None}
OLD_ROW_FILE = "issues.jsonl"
HELP = ("check the store against its own spec version (v2; a pre-v2 store gets one "
        "I-02 step); exit 1 on problems, 2 on no/unreadable store")


def register(subparsers):
    sp = subparsers.add_parser("validate", help=HELP, description=HELP)
    sp.add_argument("--workspace", help=".vscode/*.code-workspace to fan out over")
    sp.add_argument("--json", action="store_true")


# --- the problem record ---

class Problem:
    __slots__ = ("file", "line", "id", "invariant", "message", "fix")

    def __init__(self, file, line, id, invariant, message, fix):
        self.file, self.line, self.id = file, line, id
        self.invariant, self.message, self.fix = invariant, message, fix

    def sort_key(self):
        return (self.file, (0,) if self.line is None else (1, self.line), self.invariant)

    def step_text(self):
        loc = self.file if self.line is None else f"{self.file}:{self.line}"
        if self.id:
            loc += f" ({self.id})"
        return f"{loc}: {self.message} -> {self.fix}"

    def to_json(self):
        return {"file": self.file, "line": self.line, "id": self.id,
                "invariant": self.invariant, "message": self.message,
                "fix": self.fix, "agent_may_fix": self.fix.startswith("run:")}


# --- a minimal JSON-Schema checker for the subset the spec schemas use ---

def _load_schema(name):
    with open(os.path.join(SPEC_DIR, name)) as f:
        return json.load(f)


def _type_ok(obj, t):
    return {"object": lambda: isinstance(obj, dict),
            "array": lambda: isinstance(obj, list),
            "string": lambda: isinstance(obj, str),
            "integer": lambda: isinstance(obj, int) and not isinstance(obj, bool),
            "number": lambda: isinstance(obj, (int, float)) and not isinstance(obj, bool),
            "boolean": lambda: isinstance(obj, bool),
            "null": lambda: obj is None}.get(t, lambda: True)()


def _resolve(schema, root):
    if "$ref" not in schema:
        return schema
    node = root
    for part in schema["$ref"].lstrip("#/").split("/"):
        node = node[part]
    return node


def schema_check(obj, schema, root=None, pointer=""):
    """[(json_pointer, message)] for the subset of JSON Schema the spec uses:
    type, enum, const, pattern, minimum, maximum, minLength, maxLength, required,
    additionalProperties, items, minItems, uniqueItems, anyOf, $ref/$defs."""
    root = schema if root is None else root
    schema = _resolve(schema, root)
    problems = []
    pointer = pointer or "/"
    base = pointer.rstrip("/")

    if "anyOf" in schema:
        if any(not schema_check(obj, sub, root, pointer) for sub in schema["anyOf"]):
            return []
        return [(pointer, "does not match any of the allowed shapes")]
    if "type" in schema and not _type_ok(obj, schema["type"]):
        return [(pointer, f"expected type {schema['type']}, got {type(obj).__name__}")]

    if "enum" in schema and obj not in schema["enum"]:
        problems.append((pointer, f"expected one of {schema['enum']!r}, got {obj!r}"))
    if "const" in schema and obj != schema["const"]:
        problems.append((pointer, f"expected {schema['const']!r}, got {obj!r}"))
    if isinstance(obj, str):
        if "pattern" in schema and not re.match(schema["pattern"], obj):
            problems.append((pointer, f"does not match pattern {schema['pattern']}"))
        if "minLength" in schema and len(obj) < schema["minLength"]:
            problems.append((pointer, f"length < {schema['minLength']}"))
        if "maxLength" in schema and len(obj) > schema["maxLength"]:
            problems.append((pointer, f"length > {schema['maxLength']}"))
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if "minimum" in schema and obj < schema["minimum"]:
            problems.append((pointer, f"< minimum {schema['minimum']}"))
        if "maximum" in schema and obj > schema["maximum"]:
            problems.append((pointer, f"> maximum {schema['maximum']}"))

    if isinstance(obj, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in obj:
                problems.append((base + "/" + key, f"missing required key {key!r}"))
        if schema.get("additionalProperties") is False:
            problems.extend((base + "/" + key, f"unexpected key {key!r}")
                            for key in obj if key not in props)
        for key, val in obj.items():
            if key in props:
                problems.extend(schema_check(val, props[key], root, base + "/" + key))

    if isinstance(obj, list):
        if "minItems" in schema and len(obj) < schema["minItems"]:
            problems.append((pointer, f"fewer than {schema['minItems']} items"))
        if "items" in schema:
            for i, item in enumerate(obj):
                problems.extend(schema_check(item, schema["items"], root, f"{base}/{i}"))
        if schema.get("uniqueItems"):
            seen = []
            for i, item in enumerate(obj):
                key = json.dumps(item, sort_keys=True)
                if key in seen:
                    problems.append((f"{base}/{i}", "duplicate item"))
                seen.append(key)
    return problems


# --- reading a store by hand ---

class Loaded:
    """A store read raw: its config, rows with line numbers, and the id maps the
    invariants need. Unlike `store.Store` it tolerates any spec_version."""

    def __init__(self, root, config, rows):
        self.root, self.config, self.rows = root, config, rows
        self.by_id = {}
        for _, row in rows:
            if isinstance(row, dict) and isinstance(row.get("id"), str):
                self.by_id.setdefault(row["id"], row)
        self.compacted = {}
        for _, row in rows:
            subs = row.get("subtasks") if isinstance(row, dict) else None
            for entry in subs if isinstance(subs, list) else []:
                if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                    self.compacted.setdefault(entry["id"], row.get("id"))
        self._archive = None

    def archive_index(self):
        """[(lineno, obj_or_None, error_or_None)] of archive/archive-index.jsonl."""
        if self._archive is None:
            self._archive = []
            path = os.path.join(self.root, "archive", "archive-index.jsonl")
            if os.path.exists(path):
                with open(path) as f:
                    for lineno, line in enumerate(f, 1):
                        if not line.strip():
                            continue
                        try:
                            self._archive.append((lineno, json.loads(line), None))
                        except json.JSONDecodeError as e:
                            self._archive.append((lineno, None, str(e)))
        return self._archive

    def archive_self_ids(self):
        return {obj["id"] for _, obj, err in self.archive_index()
                if not err and isinstance(obj, dict) and obj.get("source") == "self"
                and isinstance(obj.get("id"), str)}

    def would_parent_cycle(self, tid, new_parent):
        cur, seen = new_parent, set()
        while cur:
            if cur == tid:
                return True
            if cur in seen:
                return False
            seen.add(cur)
            nxt = self.by_id.get(cur)
            cur = nxt.get("parent") if nxt else None
        return False


def _relpath(path, root):
    return os.path.relpath(path, root)


def load(root):
    """(Loaded, None, None), or (None, error_path, error_message) for a missing or
    unparsable config or row file, naming the exact file and line."""
    config_path = os.path.join(root, "config.json")
    repo_dir = os.path.dirname(root)
    if not os.path.exists(config_path):
        return None, _relpath(config_path, repo_dir), "file not found"
    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return None, _relpath(config_path, repo_dir), str(e)
    if not isinstance(config, dict):
        return None, _relpath(config_path, repo_dir), "not a JSON object"
    sv = config.get("spec_version")
    name = st.TICKET_FILE if isinstance(sv, int) and sv >= 2 else OLD_ROW_FILE
    path = os.path.join(root, name)
    if not os.path.exists(path):
        if "spec_version" in config:
            return None, _relpath(path, repo_dir), "file not found"
        return Loaded(root, config, []), None, None
    rows = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append((lineno, json.loads(line)))
            except json.JSONDecodeError as e:
                return None, f"{_relpath(path, repo_dir)}:{lineno}", str(e)
    return Loaded(root, config, rows), None, None


# --- the invariants ---

def check_entries(loaded):
    pre_v2 = _is_pre_v2(loaded.config)
    problems = []
    for name in sorted(os.listdir(loaded.root)):
        if (name in STORE_ENTRIES or name.endswith(".tmp") or name == ".tmp"
                or UPGRADE_REPORT_RE.match(name) or (pre_v2 and name == OLD_ROW_FILE)):
            continue
        problems.append(Problem(name, None, None, "I-01", f"{name} is not part of the store",
            f"operator: remove or relocate {name}; it is not part of the store"))
    return problems


def _is_pre_v2(config):
    sv = config.get("spec_version")
    if "version" in config and "spec_version" not in config:
        return True
    return isinstance(sv, int) and not isinstance(sv, bool) and sv < 2


def check_config(loaded, schema):
    """(problems, short_circuit): a pre-v2 config is exactly one I-02 step."""
    config = loaded.config
    if _is_pre_v2(config):
        sv = config.get("spec_version")
        what = ("store is v0 (unversioned pilot shape)" if sv is None
                else f"store is spec v{sv}; this pm reads v2 only")
        return [Problem("config.json", None, None, "I-02", what,
                        f"operator: migrate it with the old pm: {OLD_PM_UPGRADE}")], True
    problems = [Problem("config.json", None, None, "I-02", f"{p}: {m}",
                        f"operator: config.json {p}: {m}")
                for p, m in schema_check(config, schema)]
    legacy = config.get("legacy_prefixes")
    if isinstance(legacy, list) and config.get("prefix") in legacy:
        prefix = config["prefix"]
        problems.append(Problem("config.json", None, None, "I-02",
            f"/legacy_prefixes: contains the primary prefix {prefix!r}",
            "operator: config.json /legacy_prefixes: remove the primary "
            f"prefix {prefix!r}; legacy prefixes must differ from it"))
    sv = config.get("spec_version")
    if isinstance(sv, int) and sv != 2:
        problems.append(Problem("config.json", None, None, "I-02",
            f"spec_version {sv} does not match target 2",
            f"operator: config.json spec_version: expected 2, got {sv}"))
    return problems, False


def check_schema_rows(loaded, schema):
    """I-03 prefix match and I-04 row schema."""
    config = loaded.config
    prefix = config.get("prefix")
    owned = st.owned_prefixes(config)
    shown = prefix if len(owned) <= 1 else "/".join(owned)
    problems = []
    for lineno, row in loaded.rows:
        rid = row.get("id") if isinstance(row, dict) else None
        if isinstance(rid, str) and isinstance(prefix, str) \
                and not any(rid.startswith(p + "-") for p in owned):
            problems.append(Problem(st.TICKET_FILE, lineno, rid, "I-03",
                f"row id {rid} does not carry prefix {shown}",
                f"operator: row id {rid} does not carry prefix {shown}; "
                "re-file or edit the id and every edge that names it"))
        for pointer, message in schema_check(row, schema):
            fix = f"operator: {lineno} {pointer}: {message}"
            key = pointer.lstrip("/")
            if pointer.count("/") == 1 and message.startswith("missing required key") \
                    and key in BACKFILLABLE_KEYS:
                fix += f"; add the key by hand with the value {json.dumps(BACKFILLABLE_KEYS[key])}"
            problems.append(Problem(st.TICKET_FILE, lineno,
                rid if isinstance(rid, str) else None, "I-04", f"{pointer}: {message}", fix))
    return problems


def check_duplicate_ids(loaded):
    problems = []
    lines_of = {}
    for lineno, row in loaded.rows:
        rid = row.get("id") if isinstance(row, dict) else None
        if isinstance(rid, str):
            lines_of.setdefault(rid, []).append(lineno)
    archive_ids = loaded.archive_self_ids()
    for rid, lines in sorted(lines_of.items()):
        if len(lines) > 1:
            loc = ",".join(str(x) for x in lines)
            problems.append(Problem(st.TICKET_FILE, lines[0], rid, "I-05",
                f"duplicate id {rid} at lines {loc}",
                f"operator: duplicate id {rid} at lines {loc}; keep one, re-file the other"))
        if rid in archive_ids:
            problems.append(Problem(st.TICKET_FILE, lines[0], rid, "I-05",
                f"duplicate id {rid}: also present in archive index",
                f"operator: duplicate id {rid} at lines {lines[0]}; "
                "keep one, re-file the other"))
    seen = {}
    for lineno, row in loaded.rows:
        subs = row.get("subtasks") if isinstance(row, dict) else None
        for entry in subs if isinstance(subs, list) else []:
            sid = entry.get("id") if isinstance(entry, dict) else None
            if not isinstance(sid, str):
                continue
            if sid in lines_of:
                where = "also a live row"
            elif sid in archive_ids:
                where = "also present in archive index"
            elif sid in seen:
                where = f"also a subtask id at line {seen[sid]}"
            else:
                seen[sid] = lineno
                continue
            problems.append(Problem(st.TICKET_FILE, lineno, sid, "I-05",
                f"duplicate id {sid}: {where}",
                f"operator: duplicate id {sid} in subtasks at line {lineno}; "
                "keep one, re-file the other"))
    return problems


def _row_problem(lineno, rid, inv, message, fix):
    return Problem(st.TICKET_FILE, lineno, rid, inv, message, fix)


def check_row(loaded, lineno, rid, row):
    """I-04 subtask shape, I-06..I-12, I-14, I-15, I-19 for one row."""
    problems = []
    add = lambda inv, message, fix: problems.append(  # noqa: E731
        _row_problem(lineno, rid, inv, message, fix))
    status, assignee, kind = row.get("status"), row.get("assignee"), row.get("kind")

    title = row.get("title")
    if isinstance(title, str) and st.title_problem(title):
        trunc = (title.splitlines()[0] if title.splitlines() else "")[:st.TITLE_MAX]
        if trunc:
            fix = f"run: pm ticket edit {rid} --title {shlex.quote(trunc)}"
        else:
            fix = (f"operator: {rid} has an empty title; supply one and run "
                   f"pm ticket edit {rid} --title <title>")
        add("I-06", f"title is empty, multi-line, or over {st.TITLE_MAX} chars", fix)

    if kind == "task" and (status == "claimed") != (assignee is not None):
        add("I-07", "assignee must be non-null iff status is claimed",
            f"run: pm ticket release {rid}")
    elif kind == "epic" and (status == "claimed" or assignee is not None):
        add("I-08", "epics cannot be claimed and must carry no assignee",
            f"run: pm ticket release {rid}")

    subs = row.get("subtasks")
    if subs is not None:
        if kind != "epic":
            add("I-04", "/subtasks: only an epic row may carry subtasks",
                f"operator: {lineno} /subtasks: remove subtasks from {rid}, "
                "which is not an epic")
        elif isinstance(subs, list):
            keys = [(e.get("closed"), e.get("id")) for e in subs
                    if isinstance(e, dict) and isinstance(e.get("closed"), str)
                    and isinstance(e.get("id"), str)]
            if keys != sorted(keys):
                add("I-04", "/subtasks: entries not sorted by (closed, id)",
                    f"operator: {lineno} /subtasks: sort entries by (closed, id)")

    if status != "closed" and row.get("closure_reason") is not None:
        add("I-19", "closure_reason must be null when status is not closed",
            f"run: pm ticket edit {rid} --closure-reason null")

    problems.extend(_parent_problems(loaded, lineno, rid, row))
    problems.extend(_label_problems(lineno, rid, row))
    problems.extend(_edge_problems(loaded, lineno, rid, row))
    problems.extend(_time_problems(lineno, rid, row))
    return problems


def _parent_problems(loaded, lineno, rid, row):
    parent = row.get("parent")
    if not isinstance(parent, str):
        return []
    if parent not in loaded.by_id:
        message = f"parent {parent} does not exist"
        fix = (f"operator: parent {parent} of {rid} does not exist; "
               f"pm ticket reparent {rid} --none or restore {parent}")
    elif loaded.by_id[parent].get("kind") != "epic":
        message, fix = f"parent {parent} is a task", f"operator: parent {parent} is a task"
    elif loaded.would_parent_cycle(rid, parent):
        message = "parent cycle"
        fix = f"operator: parent cycle {rid} -> {parent} -> ... -> {rid}"
    else:
        return []
    return [_row_problem(lineno, rid, "I-09", message, fix)]


def _label_problems(lineno, rid, row):
    labels = row.get("labels")
    if not isinstance(labels, list):
        return []
    problems = []
    for lbl in labels:
        if not (isinstance(lbl, str) and st.LABEL_RE.match(lbl)):
            problems.append(_row_problem(lineno, rid, "I-10",
                f"label {lbl!r} is not a valid label",
                f"operator: label {lbl} on {rid} is not a valid label; "
                "rewrite it lowercase or remove it"))
    if all(isinstance(lbl, str) for lbl in labels) and labels != sorted(set(labels)):
        problems.append(_row_problem(lineno, rid, "I-10", "labels not sorted/deduped",
            f"operator: rewrite the labels array of {rid} sorted and without duplicates"))
    return problems


def _edge_problems(loaded, lineno, rid, row):
    edges = row.get("edges")
    problems = []
    for e in edges if isinstance(edges, list) else []:
        if not isinstance(e, dict):
            continue
        etype, eto = e.get("type"), e.get("to")
        cross = isinstance(eto, str) and "/" in eto
        if etype == "blocked-by" and isinstance(eto, str) and not cross:
            problems.append(_row_problem(lineno, rid, "I-04",
                f"blocked-by edge -> {eto} must name a cross-store target (<prefix>/<id>)",
                f"operator: blocked-by edge {rid} -> {eto} must be "
                f"<prefix>/<id>; pm ticket unlink {rid} {eto} --type blocked-by"))
        elif eto == rid:
            problems.append(_row_problem(lineno, rid, "I-12",
                f"self-referencing {etype} edge", f"run: pm ticket unlink {rid} {rid}"))
        elif cross:
            continue
        elif isinstance(eto, str) and eto not in loaded.by_id \
                and eto not in loaded.archive_self_ids() and eto not in loaded.compacted:
            problems.append(_row_problem(lineno, rid, "I-11",
                f"{etype} edge -> {eto} names no ticket",
                f"operator: {etype} edge {rid} -> {eto} names no ticket; "
                f"pm ticket unlink {rid} {eto} or restore {eto}"))
    return problems


def _time_problems(lineno, rid, row):
    problems = []
    notes = row.get("notes")
    if isinstance(notes, list):
        tss = [n.get("ts") if isinstance(n, dict) else None for n in notes]
        for k in range(1, len(tss)):
            a, b = tss[k - 1], tss[k]
            if isinstance(a, str) and isinstance(b, str) and b < a:
                problems.append(_row_problem(lineno, rid, "I-14",
                    f"note timestamps out of order at index {k}",
                    f"operator: note timestamps out of order on {rid} at index {k}"))
                break
    created, updated = row.get("created"), row.get("updated")
    if isinstance(created, str) and isinstance(updated, str) \
            and TIMESTAMP_RE.match(created) and TIMESTAMP_RE.match(updated) \
            and updated < created:
        problems.append(_row_problem(lineno, rid, "I-15",
            f"updated {updated} precedes created {created}",
            f"operator: {rid} updated {updated} precedes created {created}"))
    return problems


def check_blocks_cycles(loaded):
    graph, line_of = {}, {}
    for lineno, row in loaded.rows:
        rid = row.get("id") if isinstance(row, dict) else None
        if isinstance(rid, str):
            graph.setdefault(rid, [])
            line_of.setdefault(rid, lineno)
    for _, row in loaded.rows:
        rid = row.get("id") if isinstance(row, dict) else None
        if not isinstance(rid, str):
            continue
        for e in row.get("edges", []) or []:
            if isinstance(e, dict) and e.get("type") == "blocks" and e.get("to") in graph:
                graph[rid].append(e["to"])

    color = {n: 0 for n in graph}
    stack, reported, problems = [], set(), []

    def canonical(chain):
        core = chain[:-1]
        i = core.index(min(core))
        return tuple(core[i:] + core[:i])

    def dfs(u):
        color[u] = 1
        stack.append(u)
        for v in graph[u]:
            if color[v] == 1:
                chain = stack[stack.index(v):] + [v]
                key = canonical(chain)
                if key not in reported:
                    reported.add(key)
                    problems.append(_row_problem(line_of.get(chain[0]), chain[0], "I-13",
                        "blocks graph has a cycle",
                        f"operator: blocks cycle {' -> '.join(chain)}; "
                        "pm ticket unlink one edge"))
            elif color[v] == 0:
                dfs(v)
        stack.pop()
        color[u] = 2

    for n in sorted(graph):
        if color[n] == 0:
            dfs(n)
    return problems


def _archive_problem(file, line, id, inv, message):
    return Problem(file, line, id, inv, message, f"operator: {file}:{line}: {message}"
                   if line else f"operator: {file}: {message}")


def check_archive(loaded, ticket_schema):
    """I-16 index rows, I-17 year files, I-18 stray entries."""
    archive_dir = os.path.join(loaded.root, "archive")
    if not os.path.isdir(archive_dir):
        return []
    index_file = "archive/archive-index.jsonl"
    problems = []
    for lineno, obj, err in loaded.archive_index():
        if err:
            msg, rid = f"invalid JSON: {err}", None
        elif not isinstance(obj, dict):
            msg, rid = "row is not an object", None
        else:
            keys = set(obj)
            if keys == ARCHIVE_INDEX_ROW_KEYS:
                continue
            detail = []
            if ARCHIVE_INDEX_ROW_KEYS - keys:
                detail.append(f"missing {sorted(ARCHIVE_INDEX_ROW_KEYS - keys)}")
            if keys - ARCHIVE_INDEX_ROW_KEYS:
                detail.append(f"unexpected {sorted(keys - ARCHIVE_INDEX_ROW_KEYS)}")
            msg, rid = "; ".join(detail), obj.get("id")
        problems.append(Problem(index_file, lineno, rid, "I-16", msg,
                                f"operator: archive-index.jsonl:{lineno}: {msg}"))

    year_re = re.compile(r"^tickets-[0-9]{4}\.jsonl$")
    epic_subs = {}
    for name in sorted(os.listdir(archive_dir)):
        path = os.path.join(archive_dir, name)
        if not year_re.match(name) or not os.path.isfile(path):
            continue
        with open(path) as f:
            for lineno, line in enumerate(f, 1):
                if not line.strip():
                    continue
                file = f"archive/{name}"
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    problems.append(_archive_problem(file, lineno, None, "I-17",
                                                     f"invalid JSON: {e}"))
                    continue
                rid = obj.get("id") if isinstance(obj, dict) else None
                for pointer, message in schema_check(obj, ticket_schema):
                    problems.append(_archive_problem(file, lineno, rid, "I-17",
                                                     f"{pointer}: {message}"))
                if isinstance(obj, dict) and isinstance(obj.get("subtasks"), list):
                    epic_subs[(name, rid)] = {e.get("id") for e in obj["subtasks"]
                                              if isinstance(e, dict)}
                if isinstance(obj, dict) and obj.get("status") != "closed":
                    problems.append(_archive_problem(file, lineno, rid, "I-17",
                                                     "archived row is not status closed"))

    year_files = {n for n in os.listdir(archive_dir) if year_re.match(n)}
    for lineno, obj, err in loaded.archive_index():
        meta = obj.get("meta") if isinstance(obj, dict) else None
        epic = meta.get("compacted_into") if isinstance(meta, dict) else None
        if err or not isinstance(epic, str) or obj.get("path") not in year_files:
            continue
        if obj.get("id") not in epic_subs.get((obj["path"], epic), ()):
            msg = f"{obj.get('id')} is not a subtask of {epic} in {obj['path']}"
            problems.append(Problem(index_file, lineno, obj.get("id"), "I-17", msg,
                                    f"operator: archive-index.jsonl:{lineno}: {msg}"))

    source_dir_re = re.compile(r"^.+-[0-9]{8}$")
    for name in sorted(os.listdir(archive_dir)):
        if name == "archive-index.jsonl" or year_re.match(name) or name.endswith(".tmp"):
            continue
        if os.path.isdir(os.path.join(archive_dir, name)) and source_dir_re.match(name):
            continue
        problems.append(Problem(f"archive/{name}", None, None, "I-18",
            f"{name} is not an archive entry",
            f"operator: archive/{name} is not an archive entry"))
    return problems


def problems_of(loaded):
    """Every invariant problem in a loaded store, sorted for printing."""
    problems = check_entries(loaded)
    config_problems, short = check_config(loaded, _load_schema("config.schema.json"))
    problems.extend(config_problems)
    if not short:
        schema = _load_schema("ticket.schema.json")
        problems.extend(check_schema_rows(loaded, schema))
        problems.extend(check_duplicate_ids(loaded))
        for lineno, row in loaded.rows:
            rid = row.get("id") if isinstance(row, dict) else None
            if isinstance(rid, str):
                problems.extend(check_row(loaded, lineno, rid, row))
        problems.extend(check_blocks_cycles(loaded))
        problems.extend(check_archive(loaded, schema))
    problems.sort(key=lambda p: p.sort_key())
    return problems


# --- one store, rendered ---

def validate_one(root):
    """One store's result as a dict for text and --json rendering."""
    loaded, err_path, err_msg = load(root)
    if loaded is None:
        return {"exit": 2, "path": err_path, "error": err_msg}
    problems = problems_of(loaded)
    config = loaded.config
    if "version" in config and "spec_version" not in config:
        label = "v0"
    else:
        sv = config.get("spec_version")
        label = sv if isinstance(sv, int) else "unknown"
    return {"exit": 1 if problems else 0, "root": root, "spec_version": label,
            "rows": len(loaded.rows),
            "archive": "present" if os.path.isdir(os.path.join(root, "archive")) else "absent",
            "problems": problems, "loaded": loaded}


def result_json(result):
    if result["exit"] == 2:
        return {"ok": False, "spec_version": None, "problems": [],
                "error": result["error"], "path": result["path"]}
    return {"ok": result["exit"] == 0, "spec_version": result["spec_version"],
            "problems": [p.to_json() for p in result["problems"]]}


def print_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def print_result(as_json, result):
    if as_json:
        print_json(result_json(result))
    elif result["exit"] == 2:
        where = f"{result['path']}: " if result["path"] else ""
        print(f"pm: {where}{result['error']}", file=sys.stderr)
    elif result["exit"] == 0:
        print(f"OK spec_version={result['spec_version']} rows={result['rows']} "
              f"archive={result['archive']}")
    else:
        problems = result["problems"]
        print(f"FAIL spec_version={result['spec_version']} problems={len(problems)}")
        for i, p in enumerate(problems, 1):
            print(f"{i}. {p.step_text()}")


# --- --workspace ---

def parse_jsonc(text):
    """JSON with // and /* */ comments and trailing commas, as a
    `.code-workspace` file carries them."""
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def discover_workspace_repos(workspace_file):
    """Repo roots from `folders[].path`, kept when they hold `.git` and `.pm`."""
    with open(workspace_file) as f:
        data = parse_jsonc(f.read())
    base = os.path.dirname(os.path.abspath(workspace_file))
    repos = []
    for folder in data.get("folders", []):
        p = folder.get("path")
        if not p:
            continue
        full = os.path.normpath(os.path.join(base, p))
        if os.path.exists(os.path.join(full, ".git")) \
                and os.path.isdir(os.path.join(full, st.STORE_DIR)):
            repos.append(full)
    return repos


def workspace_problems(results):
    """W-01 shared prefix and W-02 shared id across the fanned-out stores."""
    prefixes, ids = {}, {}
    for result in results:
        if result["exit"] == 2:
            continue
        loaded = result["loaded"]
        prefix = loaded.config.get("prefix")
        if isinstance(prefix, str):
            prefixes.setdefault(prefix, []).append(result["repo"])
        for _, row in loaded.rows:
            tid = row.get("id") if isinstance(row, dict) else None
            if isinstance(tid, str):
                ids.setdefault(tid, []).append(result["repo"])
    out = []
    for prefix, repos in sorted(prefixes.items()):
        if len(repos) > 1:
            a, b = repos[0], repos[1]
            out.append(Problem("workspace", None, None, "W-01",
                f"prefix {prefix} used by {a} and {b}",
                f"operator: prefix {prefix} used by {a} and {b}; pick a new prefix "
                "in one config.json and re-id its rows"))
    for tid, repos in sorted(ids.items()):
        if len(repos) > 1:
            a, b = repos[0], repos[1]
            out.append(Problem("workspace", None, tid, "W-02",
                f"id {tid} in {a} and {b}", f"operator: id {tid} in {a} and {b}"))
    return out


def run_workspace(args):
    results, exit_code = [], 0
    for repo in discover_workspace_repos(args.workspace):
        root = st.find_store(repo) or os.path.join(repo, st.STORE_DIR)
        result = validate_one(root)
        result["repo"] = repo
        results.append(result)
        exit_code = max(exit_code, result["exit"])
    ws_problems = workspace_problems(results)
    if ws_problems:
        exit_code = max(exit_code, 1)
    if args.json:
        print_json({"ok": exit_code == 0,
                    "repos": [dict(result_json(r), repo=r["repo"]) for r in results],
                    "workspace": [p.to_json() for p in ws_problems]})
        sys.exit(exit_code)
    for result in results:
        print(f"== {result['repo']} ==")
        print_result(False, result)
    if ws_problems:
        print("== workspace ==")
        for i, p in enumerate(ws_problems, 1):
            print(f"{i}. {p.step_text()}")
    sys.exit(exit_code)


def run(args):
    if args.workspace:
        run_workspace(args)
    root = st.find_store(args.repo)
    if not root:
        print_result(args.json, {"exit": 2, "path": None,
                                 "error": "no ticket store found (run: pm ticket init)"})
        sys.exit(2)
    result = validate_one(root)
    print_result(args.json, result)
    sys.exit(result["exit"])
