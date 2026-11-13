#!/usr/bin/env python3
"""Check routing documents and component layout against docs/contributing.md.

Reads only. Exit 0: no violations after exemptions. Exit 1: violations remain.
Exit 2: usage error, or the repository root is not a git work tree.
"""
import glob
import os
import re
import shlex
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHIM = "@AGENTS.md"
ROOT_FILES = ("CLAUDE.md", "AGENTS.md", "README.md", "docs/contributing.md")
INTEGRATION_DIRS = ("skills", "hooks", "instructions", "config", "cli")
INDEX_HEADER = ["Component", "Purpose", "Development instructions"]
ROUTE_HEADERS = (["Change", "Read"], ["Work", "Read"])
INTERPRETERS = ("python3", "/usr/bin/python3")
EXEMPTION_HEADER = ["Component", "Rule", "Reason"]
FROM_ROOT = "from the repository root"
FROM_COMPONENT = "from this component directory"
RUN_MESSAGE = ('no validation block: a paragraph beginning "Run" that says '
               '"from the repository root", followed by a sh fence')

RULES = (
    "R-FILE", "R-CLAUDE", "I-TABLE", "I-ROW", "I-MISSING", "I-UNINDEXED",
    "C-AGENTS", "C-README", "C-CLAUDE", "C-INSTALL", "C-README-ROUTE",
    "A-TITLE", "A-TABLE", "A-RUN", "A-CWD", "A-TARGET",
    "L-TARGET", "L-ROOT", "L-ANCHOR", "X-ROW", "X-STALE",
)
EXEMPTABLE = ("I-UNINDEXED",) + tuple(r for r in RULES if r[0] in "CAL")

FENCE = re.compile(r"(`{3,}|~{3,})(.*)")
CODE_SPAN = re.compile(r"`[^`]*`")
LINK = re.compile(r'\[([^\]\n]*)\]\(([^()\s]+)(?:[ \t]+"[^"]*")?\)')
EXTERNAL = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|//)")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")


def split_fences(text):
    """Return (prose, fences): numbered lines outside fences, and
    (opening line, info word, numbered body lines) for each fence."""
    prose, fences, opened = [], [], None
    for n, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if opened:
            char, count, _, _, body = opened
            if len(stripped) >= count and set(stripped) == {char}:
                fences.append(opened[2:])
                opened = None
            else:
                body.append((n, line))
            continue
        m = FENCE.match(stripped)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            words = m.group(2).split()
            opened = (m.group(1)[0], len(m.group(1)), n, words[0] if words else "", [])
        else:
            prose.append((n, line))
    if opened:
        fences.append(opened[2:])
    return prose, fences


def links(prose):
    for n, line in prose:
        for m in LINK.finditer(CODE_SPAN.sub("", line)):
            if not EXTERNAL.match(m.group(2)):
                yield n, m.group(2)


def resolve(doc, target):
    """Return (absolute path or None when outside the repository, fragment,
    whether the target is written root-relative or is a same-file anchor)."""
    path, _, fragment = target.partition("#")
    path = urllib.parse.unquote(path)
    if not path:
        return doc, fragment, True
    if path.startswith("~"):
        return None, fragment, False
    base = ROOT if path.startswith("/") else doc.parent
    full = Path(os.path.normpath(os.path.join(base, path.lstrip("/"))))
    if full != ROOT and ROOT not in full.parents:
        return None, fragment, path.startswith("/")
    return full, fragment, path.startswith("/")


def rel(path):
    return path.relative_to(ROOT).as_posix()


def slugs(path):
    seen, out = {}, set()
    for _, line in split_fences(path.read_text(errors="replace"))[0]:
        m = HEADING.match(line)
        if not m:
            continue
        title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", m.group(1)).replace("`", "")
        slug = re.sub(r"[^\w\- ]", "", title.strip().lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        out.add(slug if count == 0 else "%s-%d" % (slug, count))
    return out


def tables(prose):
    """Yield (header line, header cells, [(line, cells), ...]) for each table."""
    block = []
    for n, line in prose + [(0, "")]:
        if line.startswith("|") and (not block or n == block[-1][0] + 1):
            block.append((n, line))
            continue
        if block:
            rows = [(k, [c.strip() for c in text.strip().strip("|").split("|")]) for k, text in block]
            yield rows[0][0], rows[0][1], rows[2:]
        block = [(n, line)] if line.startswith("|") else []


def table_after(prose, title):
    """First table below the heading with this title, or None."""
    start = next((n for n, line in prose
                  if HEADING.match(line) and HEADING.match(line).group(1) == title), None)
    if start is None:
        return None
    return next((t for t in tables(prose) if t[0] > start), None)


def tracked_dirs():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"],
                             capture_output=True, text=True)
    except OSError:
        out = None
    if out is None or out.returncode != 0:
        sys.stderr.write("check_structure: error: %s is not a git work tree\n" % ROOT)
        sys.exit(2)
    firsts = {entry.split("/", 1)[0] for entry in out.stdout.split("\0") if "/" in entry}
    return {d for d in firsts if d != "docs" and not d.startswith(".")}


def flag(report, path, line, rule, message, component=None):
    report.append((path, line or 0, rule, message, component))


def cell_link(doc, cell, name):
    """Top-level directory whose <dir>/<name> the cell's single link points to."""
    targets = [t for _, t in links([(0, cell)])]
    if len(targets) != 1:
        return None
    full = resolve(doc, targets[0])[0]
    if full is None:
        return None
    parts = full.relative_to(ROOT).parts
    return parts[0] if len(parts) == 2 and parts[1] == name else None


def check_index(report):
    """Return {indexed directory: README.md line}, or None when the table is absent."""
    readme = ROOT / "README.md"
    if not readme.is_file():
        return None
    prose = split_fences(readme.read_text(errors="replace"))[0]
    table = table_after(prose, "Components")
    if table is None or table[1] != INDEX_HEADER:
        flag(report, "README.md", 0, "I-TABLE",
                   'no "## Components" table with header '
                   '"| Component | Purpose | Development instructions |"')
        return None
    indexed = {}
    for n, cells in table[2]:
        first = cell_link(readme, cells[0], "README.md") if len(cells) == 3 else None
        third = cell_link(readme, cells[2], "AGENTS.md") if len(cells) == 3 else None
        if first is None or first != third:
            flag(report, "README.md", n, "I-ROW",
                       "index row must link /<dir>/README.md in column 1 "
                       "and /<dir>/AGENTS.md in column 3")
        else:
            indexed[first] = n
    return indexed


def links_to(doc, target):
    prose = split_fences(doc.read_text(errors="replace"))[0]
    return any(resolve(doc, t)[0] == target for _, t in links(prose))


def check_files(report, name):
    base = ROOT / name

    def add(filename, rule, message):
        flag(report, "%s/%s" % (name, filename), 0, rule, message, name)

    for filename, rule in (("AGENTS.md", "C-AGENTS"), ("README.md", "C-README")):
        if not (base / filename).is_file():
            add(filename, rule, "missing required component file")
    shim = base / "CLAUDE.md"
    if not shim.is_file() or shim.read_text(errors="replace").strip() != SHIM:
        add("CLAUDE.md", "C-CLAUDE", 'missing or not exactly "%s"' % SHIM)
    install = base / "INSTALL.md"
    reason = next((d for d in INTEGRATION_DIRS if (base / d).is_dir()), None)
    if reason and not install.is_file():
        add("INSTALL.md", "C-INSTALL", "missing; required because %s/%s/ exists" % (name, reason))
    readme = base / "README.md"
    if readme.is_file():
        for filename in ("AGENTS.md", "INSTALL.md"):
            required = filename == "AGENTS.md" or install.is_file()
            if required and not links_to(readme, base / filename):
                add("README.md", "C-README-ROUTE", "does not link /%s/%s" % (name, filename))


def option(tokens, flag):
    return tokens[tokens.index(flag) + 1] if flag in tokens[:-1] else None


def target_error(command, base):
    try:
        tokens = shlex.split(command)
    except ValueError:
        return "cannot parse command"
    if not tokens or tokens[0] not in INTERPRETERS:
        return "command must start with python3 or /usr/bin/python3"
    i, module, script = 1, None, None
    while i < len(tokens):
        token = tokens[i]
        if token == "-m" and i + 1 < len(tokens):
            module = tokens[i + 1]
            break
        if token in ("-W", "-X"):
            i += 2
        elif token.startswith("-"):
            i += 1
        else:
            script = token
            break
    if script is not None:
        return None if (base / script).is_file() else "script %s does not exist" % script
    if module is None:
        return "cannot parse command"
    if module != "unittest":
        return "module %s has no path to check" % module
    directory = option(tokens, "-s")
    pattern = option(tokens, "-p") or "test*.py"
    if directory is None:
        return "unittest discover needs -s <dir>"
    if not (base / directory).is_dir():
        return "test directory %s does not exist" % directory
    if not glob.glob(str(base / directory / pattern)):
        return "no file matches %s in %s" % (pattern, directory)
    return None


def check_agents(report, name):
    path = "%s/AGENTS.md" % name
    text = (ROOT / path).read_text(errors="replace")
    lines = text.splitlines()
    prose, fences = split_fences(text)

    def add(line, rule, message):
        flag(report, path, line, rule, message, name)

    if not lines or not re.match(r"^# .+ maintenance$", lines[0]):
        add(1, "A-TITLE", 'first line must be "# <Name> maintenance"')

    table = next(tables(prose), None)
    filled = table and any(len(c) == 2 and all(c) for _, c in table[2])
    if not table or table[1] not in ROUTE_HEADERS or not filled:
        add(table[0] if table else 1, "A-TABLE",
            'route table header must be "| Change | Read |" or "| Work | Read |" '
            "with at least one filled row")

    fence = next((f for f in fences if f[1] == "sh"), None)
    if not fence:
        add(1, "A-RUN", RUN_MESSAGE)
        return
    end = next((i for i in range(fence[0] - 2, -1, -1) if lines[i].strip()), -1)
    first = end
    while first > 0 and lines[first - 1].strip():
        first -= 1
    paragraph = " ".join(line.strip() for line in lines[first:end + 1]) if end >= 0 else ""
    commands = [(n, line.strip()) for n, line in fence[2]
                if line.strip() and not line.strip().startswith("#")]
    located = FROM_ROOT in paragraph or FROM_COMPONENT in paragraph
    if not paragraph.startswith("Run") or not located or not commands:
        add(first + 1 if end >= 0 else fence[0], "A-RUN", RUN_MESSAGE)
        return
    base = ROOT
    if FROM_COMPONENT in paragraph:
        add(first + 1, "A-CWD", "validation commands must run from the repository root")
        base = ROOT / name
    for n, command in commands:
        error = target_error(command, base)
        if error:
            add(n, "A-TARGET", error)


def check_links(report, doc, component):
    path = rel(doc)
    for n, target in links(split_fences(doc.read_text(errors="replace"))[0]):
        full, fragment, rooted = resolve(doc, target)
        if full is None:
            flag(report, path, n, "L-TARGET",
                       'link target "%s" is outside the repository' % target, component)
            continue
        if not full.exists():
            flag(report, path, n, "L-TARGET", 'link target "%s" does not exist' % target, component)
            continue
        if not rooted:
            wanted = "/" + rel(full) + ("#" + fragment if fragment else "")
            flag(report, path, n, "L-ROOT",
                       'link target "%s" must be repository-root-relative: "%s"' % (target, wanted),
                       component)
        markdown = full == doc or (full.is_file() and full.suffix == ".md")
        if fragment and markdown and fragment not in slugs(full):
            flag(report, path, n, "L-ANCHOR",
                       'no heading for "#%s" in %s' % (fragment, rel(full)), component)


def exemptions(report, known):
    """Return {(component, rule): contributing.md line} for the valid rows."""
    page = ROOT / "docs/contributing.md"
    if not page.is_file():
        return {}
    table = table_after(split_fences(page.read_text(errors="replace"))[0], "Exemptions")
    if table is None or table[1] != EXEMPTION_HEADER:
        return {}
    valid = {}
    for n, cells in table[2]:
        cells = (cells + ["", "", ""])[:3]
        component = cells[0].replace("`", "").strip().rstrip("/")
        rule = cells[1].replace("`", "").strip()
        problem = None
        if component not in known:
            problem = 'unknown component "%s"' % component
        elif rule not in RULES:
            problem = 'unknown rule "%s"' % rule
        elif rule not in EXEMPTABLE:
            problem = 'rule "%s" cannot be exempted' % rule
        elif not cells[2]:
            problem = "reason is empty"
        if problem:
            flag(report, "docs/contributing.md", n, "X-ROW", "exemption row: " + problem)
        else:
            valid[(component, rule)] = n
    return valid


def main(argv):
    if argv:
        sys.stderr.write("usage: python3 -B docs/check_structure.py\n")
        return 2
    tracked = tracked_dirs()
    report = []

    for name in ROOT_FILES:
        if not (ROOT / name).is_file():
            flag(report, name, 0, "R-FILE", "missing required root file")
    shim = ROOT / "CLAUDE.md"
    if shim.is_file() and shim.read_text(errors="replace").strip() != SHIM:
        flag(report, "CLAUDE.md", 0, "R-CLAUDE", 'must contain exactly "%s"' % SHIM)

    indexed = check_index(report)
    known = tracked | set(indexed or ())
    if indexed is not None:
        for name, line in sorted(indexed.items()):
            if not (ROOT / name).is_dir():
                flag(report, "README.md", line, "I-MISSING",
                           "indexed component %s/ does not exist" % name)
                continue
            check_files(report, name)
            if (ROOT / name / "AGENTS.md").is_file():
                check_agents(report, name)
        for name in sorted(tracked - set(indexed)):
            flag(report, name + "/", 0, "I-UNINDEXED",
                       "tracked top-level directory is not in the README.md component index; "
                       "add a row there or an exemption in docs/contributing.md", name)

    docs = [(ROOT / n, None) for n in ("CLAUDE.md", "AGENTS.md", "README.md")]
    docs += [(p, None) for p in sorted((ROOT / "docs").glob("*.md"))]
    docs += [(ROOT / c / n, c) for c in sorted(known) for n in ("AGENTS.md", "README.md", "INSTALL.md")]
    for doc, component in docs:
        if doc.is_file():
            check_links(report, doc, component)

    rows = exemptions(report, known)
    used, remaining = set(), []
    for path, line, rule, message, component in report:
        if (component, rule) in rows:
            used.add((component, rule))
        else:
            remaining.append((path, line, rule, message))
    for (component, rule), line in rows.items():
        if (component, rule) not in used:
            remaining.append(("docs/contributing.md", line, "X-STALE",
                              "exemption %s %s matches no violation; delete this row" % (component, rule)))

    for path, line, rule, message in sorted(remaining):
        where = "%s:%d" % (path, line) if line else path
        print("%s: %s %s" % (where, rule, message))
    counts = "(%d components, %d exempted)" % (len(indexed or ()), len(used))
    if remaining:
        print("check_structure: %d violations %s" % (len(remaining), counts))
        return 1
    print("check_structure: ok %s" % counts)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
