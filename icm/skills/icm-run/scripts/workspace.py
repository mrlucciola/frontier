"""What an ICM workspace's files say about each stage.

Shared by state.py and record.py, which must agree on what a stage's outputs, inputs and
review evidence are: record.py writes the binding that state.py later checks.
Standard library only.
"""
import hashlib
import re
from pathlib import Path

STAGE_RE = re.compile(r"^(\d\d)[-_].+")
REVIEWER_RE = re.compile(r"^\s*(?:[-*]\s*)?reviewer:\s*(human|script|model)\b\s*(.*)$", re.I | re.M)
BLOCK_RE = re.compile(r"^```icm-review\n(.*?)^```", re.S | re.M)
POINTER_NAMES = ("CLAUDE.md", "GEMINI.md")
# A model that never loads icm-run follows the entry file's own routes, and "output exists" reads as
# "passed"; this line in the entry file is what keeps such a model at the check.
ROUTE_LINE = ("Status, runs, continues and stage approvals in this workspace go through the icm-run skill. "
              "A stage's output existing does not mean it passed its check.")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_dirs(root: Path):
    stages = root / "stages"
    if not stages.is_dir():
        return []
    found = [d for d in stages.iterdir() if d.is_dir() and STAGE_RE.match(d.name)]
    return sorted(found, key=lambda d: (int(d.name[:2]), d.name))


def is_root(d: Path) -> bool:
    return (d / "CONTEXT.md").is_file() and bool(stage_dirs(d))


def find_root(start: Path):
    """<start> itself, or the parent of the nearest enclosing stages/ directory; nothing wider."""
    start = start.resolve()
    if is_root(start):
        return start
    for anc in start.parents:
        if anc.name == "stages":
            return anc.parent if is_root(anc.parent) else None
    return None


def entry_status(root: Path) -> str:
    """AGENTS.md holds the entry; any other provider's entry file must be a one-line pointer to it."""
    agents = root / "AGENTS.md"
    present = [n for n in POINTER_NAMES if (root / n).is_file()]
    if not agents.is_file():
        if present:
            return f"legacy: {', '.join(present)} without AGENTS.md; canonicalize to AGENTS.md before running"
        return "missing: no AGENTS.md entry file"
    lines = [ln for ln in agents.read_text(errors="replace").splitlines() if ln.strip()]
    if len(lines) == 1 and any(n in lines[0] for n in POINTER_NAMES):
        return "conflict: AGENTS.md points at another entry file; AGENTS.md must hold the content"
    for name in present:
        lines = [ln for ln in (root / name).read_text(errors="replace").splitlines() if ln.strip()]
        if not (len(lines) == 1 and "AGENTS.md" in lines[0] and len(lines[0]) <= 120):
            return f"conflict: {name} has its own content; it must be a one-line pointer to AGENTS.md"
    return "ok"


def route_status(root: Path) -> str:
    agents = root / "AGENTS.md"
    if agents.is_file() and "icm-run" in agents.read_text(errors="replace"):
        return "ok"
    return f'missing: ask the owner to add this line under the AGENTS.md title: "{ROUTE_LINE}"'


def sections(text: str):
    out, name = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            name = m.group(1).strip().lower()
            out[name] = []
        elif name:
            out[name].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def placeholder(s: str) -> bool:
    return any(c in s for c in "{}[]<>*") or " " in s


def contract(stage: Path):
    """Backticked Inputs paths, concrete Outputs names, and the Check's reviewer kind (human unless stated)."""
    path = stage / "CONTEXT.md"
    if not path.is_file():
        return None
    sec = sections(path.read_text(errors="replace"))
    inputs = [p for p in re.findall(r"`([^`]+)`", sec.get("inputs", "")) if not placeholder(p)]
    outputs = []
    for p in re.findall(r"`([^`]+)`", sec.get("outputs", "")):
        if not placeholder(p) and not p.endswith("/"):
            outputs.append(p[len("output/"):] if p.startswith("output/") else p)
    m = REVIEWER_RE.search(sec.get("check", ""))
    kind = m.group(1).lower() if m else "human"
    command = m.group(2).strip().strip("`").strip() if m else ""
    return {"sha": sha(path), "inputs": inputs, "outputs": outputs, "kind": kind, "command": command}


def inside(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def output_files(stage: Path):
    """Produced files under output/ except dotfiles and check.md, and any path that escapes it."""
    out = stage / "output"
    files, problems = {}, []
    if not out.is_dir():
        return files, problems
    if not inside(out, stage):
        return files, ["output/ resolves outside the stage"]
    for p in sorted(out.rglob("*")):
        rel = p.relative_to(out)
        if any(part.startswith(".") for part in rel.parts) or str(rel) == "check.md" or p.is_dir():
            continue
        if not inside(p, out):
            problems.append(f"output/{rel} resolves outside output/")
            continue
        files[str(rel)] = p
    return files, problems


def input_files(stage: Path, rows):
    """Declared inputs as {path relative to the stage: sha}; a folder row means the files directly in it."""
    found, missing = {}, []
    for row in rows:
        p = stage / row
        if p.is_file():
            found[row] = sha(p)
        elif p.is_dir():
            # An upstream verdict re-recorded for the same bytes must not make this stage stale.
            upstream_output = p.resolve().name == "output" and p.resolve().parent.parent.name == "stages"
            for f in sorted(p.iterdir()):
                if f.is_file() and not f.name.startswith(".") and not (upstream_output and f.name == "check.md"):
                    found[str(Path(row) / f.name)] = sha(f)
        else:
            missing.append(row)
    return found, missing


def parse_check(stage: Path):
    path = stage / "output" / "check.md"
    if not path.is_file():
        return None
    text = path.read_text(errors="replace")
    first = text.splitlines()[0].strip() if text.strip() else ""
    verdict = "pass" if first == "pass" else "fail" if first.startswith("fail") else None
    m = BLOCK_RE.search(text)
    if not m:
        return {"verdict": verdict, "first": first, "bound": False}
    fields, outputs, inputs = {}, {}, {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key in ("output", "input"):
            digest, _, rel = value.partition(" ")
            (outputs if key == "output" else inputs)[rel.strip()] = digest
        elif key:
            fields[key] = value
    return {"verdict": verdict, "first": first, "bound": True, "fields": fields, "outputs": outputs, "inputs": inputs}


def diff(recorded, current):
    return sorted(k for k in set(recorded) | set(current) if recorded.get(k) != current.get(k))


def evaluate(stage: Path):
    """One stage's state: unproduced, pending, rejected, accepted, stale or blocked, with the reason."""
    c = contract(stage)
    row = {"stage": stage.name, "kind": c["kind"] if c else None, "outputs": [], "missing_inputs": []}
    if c is None:
        return {**row, "state": "blocked", "detail": ["no CONTEXT.md contract"]}
    outputs, problems = output_files(stage)
    inputs, missing = input_files(stage, c["inputs"])
    row.update(outputs=sorted(outputs), missing_inputs=missing)
    if problems:
        return {**row, "state": "blocked", "detail": problems}
    absent = [o for o in c["outputs"] if o not in outputs]
    empty = [o for o in c["outputs"] if o in outputs and outputs[o].stat().st_size == 0]
    if not outputs or absent or empty:
        detail = [f"partial: {', '.join([f'{o} missing' for o in absent] + [f'{o} empty' for o in empty])}"] \
            if outputs else []
        return {**row, "state": "unproduced", "detail": detail}
    ev = parse_check(stage)
    need = f"needs {c['kind']} review"
    if ev is None:
        return {**row, "state": "pending", "detail": [f"no check.md; {need}"]}
    if not ev["bound"] or ev["verdict"] is None:
        return {**row, "state": "pending", "detail": [f"check.md is not bound review evidence; {need}"]}
    f = ev["fields"]
    if f.get("stage") != stage.name or f.get("decision") != ev["verdict"]:
        return {**row, "state": "pending", "detail": [f"check.md names another stage or contradicts its first line; {need}"]}
    if f.get("reviewer") != c["kind"]:
        return {**row, "state": "pending", "detail": [f"evidence is from a {f.get('reviewer')} reviewer; {need}"]}
    stale = []
    if f.get("contract") != c["sha"]:
        stale.append("stage CONTEXT.md changed since review")
    changed = diff(ev["outputs"], {rel: sha(p) for rel, p in outputs.items()})
    if changed:
        stale.append(f"outputs changed since review: {', '.join(changed)}")
    changed = diff(ev["inputs"], inputs)
    if changed:
        stale.append(f"inputs changed since review: {', '.join(changed)}")
    if stale:
        return {**row, "state": "stale", "detail": stale}
    if ev["verdict"] == "fail":
        return {**row, "state": "rejected", "detail": [f"{c['kind']} {f.get('by', '?')}: {ev['first']}"]}
    return {**row, "state": "accepted", "detail": [f"{c['kind']} {f.get('by', '?')} at {f.get('recorded_at', '?')}"]}


def workspace_state(start: Path):
    """Every stage's state and the one next action; a stage may run only when all earlier ones are accepted."""
    root = find_root(start)
    if root is None:
        return {"root": None, "next": "not an ICM workspace: no root CONTEXT.md with stages/NN-* here or above this stage"}
    entry = entry_status(root)
    rows = [evaluate(s) for s in stage_dirs(root)]
    current = None
    for r in rows:
        r["may_run"] = False
        if current is not None:
            r["waiting_on"] = current["stage"]
        elif r["state"] != "accepted":
            current = r
            r["may_run"] = entry == "ok" and r["state"] in ("unproduced", "rejected", "stale") \
                and not r["missing_inputs"]
    if entry != "ok":
        nxt = f"stop: entry {entry}"
    elif current is None:
        nxt = "pipeline accepted: every stage passed its check for the current files"
    elif current["missing_inputs"] and current["state"] in ("unproduced", "rejected", "stale"):
        nxt = f"blocked: {current['stage']} is missing inputs {', '.join(current['missing_inputs'])}"
    else:
        s = current["stage"]
        nxt = {
            "unproduced": f"run {s}",
            "pending": f"review {s} ({current['kind']} check); do not run a later stage",
            "rejected": f"revise {s}, then review it again",
            "stale": f"re-run or re-review {s}; its review no longer matches the files",
            "blocked": f"blocked: {s}: {'; '.join(current['detail'])}",
        }[current["state"]]
    return {"root": str(root), "entry": entry, "route": route_status(root), "stages": rows, "next": nxt}
