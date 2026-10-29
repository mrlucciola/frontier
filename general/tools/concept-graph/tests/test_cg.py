"""End-to-end tests for cg.py against a temporary store. Standard library only.
Run: python3 general/tools/concept-graph/tests/test_cg.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CG = HERE.parent / "cg.py"
sys.path.insert(0, str(HERE.parent))
import cg as cgmod  # noqa: E402

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def run(root, *args, cwd=None, stdin=None, env=None, expect=0):
    e = dict(os.environ, CONCEPT_GRAPH_ROOT=str(root), CLAUDE_CODE_SESSION_ID="test-session")
    if env:
        e.update(env)
    r = subprocess.run([sys.executable, str(CG)] + list(args), cwd=cwd or str(pathlib.Path(root).parent),
                       input=stdin, capture_output=True, text=True, env=e)
    if expect is not None and r.returncode != expect:
        FAILS.append("cg %s: exit %d (want %d) stderr=%r stdout=%r" % (
            " ".join(args[:3]), r.returncode, expect, r.stderr.strip()[-300:], r.stdout.strip()[-200:]))
    return r


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True)


def test_frontmatter_roundtrip():
    meta = {
        "name": "wal-mode", "title": "SQLite WAL mode", "aliases": ["write-ahead log", "wal"],
        "scopes": ["global", "/tmp/x"], "status": "learning", "confidence": 2,
        "epistemic": "reasoned",
        "edges": {"depends_on": ["sqlite-journal"], "related": []},
        "anchors": [{"repo": "/tmp/x", "path": "schema.sql", "sha": "abc1234", "line": 10}],
        "gaps": [{"q": "Why: readers never block?", "status": "open", "opened": "2026-10-29",
                  "due": "2026-11-05"},
                 {"q": "Odd chars # [x] \"q\"", "status": "closed", "evidence": "ran",
                  "ref": "sqlite3 db 'pragma journal_mode'"}],
        "created": "2026-10-29T00:00:00Z", "updated": "2026-10-29T00:00:00Z",
    }
    text = cgmod.dump_front(meta) + "\nbody\n"
    back, body = cgmod.parse_front(text)
    check(back == meta, "frontmatter round-trip differs:\n%s\n%s" % (json.dumps(back, indent=1), text))
    check(body == "body\n", "body after frontmatter: %r" % body)
    meta2 = dict(meta, edges={}, anchors=[], gaps=[])
    back2, _ = cgmod.parse_front(cgmod.dump_front(meta2))
    check(back2.get("edges") is None and back2.get("anchors") == [] and back2.get("gaps") == [],
          "empty containers: %r" % {k: back2.get(k) for k in ("edges", "anchors", "gaps")})


def test_cli():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp) / "store"
        r = run(root, "init")
        check("ok" in r.stdout, "init output")
        r = run(root, "add", "wal-mode", "--explain", "x", expect=2)
        check("missing sections" in r.stderr, "add requires all sections")
        r = run(root, "add", "wal-mode", "--title", "SQLite WAL mode", "--alias", "write-ahead log",
                "--alias", "wal", "--explain", "Writes go to a side file first; readers keep reading the main file.",
                "--analogy", "A restaurant order pad: orders pile up on the pad, the kitchen catches up later.",
                "--breaks", "The pad is replayed in order; real kitchens reorder.",
                "--pitch", "WAL lets readers and one writer work at once.")
        check("added wal-mode" in r.stdout, "add ok: %r" % r.stdout)
        text = (root / "cards" / "wal-mode.md").read_text()
        check(text.startswith("---\nname: wal-mode\n"), "card starts with frontmatter")
        check("## Simple explanation" in text and "## Log" in text, "card has sections")
        check("status: learning" in text, "new card is learning")

        # gaps
        r = run(root, "gap", "wal-mode", "add", "Why do readers never block writers?")
        check("gap opened" in r.stdout, "gap add")
        r = run(root, "gaps", "--due")
        check("no open gaps due" in r.stdout, "future gap is not due")
        r = run(root, "gap", "wal-mode", "add", "What happens on unclean shutdown?", "--due", "2020-01-01")
        r = run(root, "gaps", "--due")
        check("unclean shutdown" in r.stdout and "readers never block" not in r.stdout, "gaps --due filters")
        r = run(root, "gap", "wal-mode", "close", "readers never block", "--evidence", "verified-in-code", expect=2)
        check("--ref is required" in r.stderr, "evidence needs ref")
        r = run(root, "gap", "wal-mode", "close", "readers never block", "--evidence", "verified-in-code",
                "--ref", "src/wal.c:120@abc1234", "--answer", "Readers use the last committed frame index.")
        check("gap closed" in r.stdout, "gap close")
        text = (root / "cards" / "wal-mode.md").read_text()
        check("epistemic: verified-in-code" in text, "epistemic derived from strongest evidence")
        check("status: learning" in text, "still learning while a gap is open")
        r = run(root, "gap", "wal-mode", "close", "unclean shutdown", "--evidence", "source-cited",
                "--ref", "https://sqlite.org/wal.html")
        r = run(root, "set", "wal-mode", "confidence=4")
        text = (root / "cards" / "wal-mode.md").read_text()
        check("status: understood" in text, "understood once gaps closed and confidence>=3: %s" % text[:400])

        # links and neighbors
        r = run(root, "link", "wal-mode", "depends_on", "sqlite-journal", expect=1)
        check("add it first" in r.stderr, "link target must exist")
        run(root, "add", "sqlite-journal", "--title", "SQLite journal", "--explain", "a", "--analogy", "b",
            "--breaks", "c", "--pitch", "d")
        r = run(root, "link", "wal-mode", "depends_on", "sqlite-journal")
        check("--[depends_on]-->" in r.stdout, "link")
        r = run(root, "neighbors", "sqlite-journal")
        check("wal-mode --[depends_on]--> sqlite-journal" in r.stdout, "reverse edge visible: %r" % r.stdout)

        # recall and scopes
        r = run(root, "recall", "how", "does", "the", "write-ahead", "log", "work")
        check(r.stdout.startswith("memory: 1 concept (scope: global)"), "recall header: %r" % r.stdout[:80])
        check(cgmod.GUARD in r.stdout, "guard line present")
        r = run(root, "recall", "kubernetes", "ingress")
        check("no concepts match" in r.stdout, "recall miss")
        other = pathlib.Path(tmp) / "repo"
        other.mkdir()
        run(root, "add", "local-thing", "--local-only", "--scope", str(other), "--title", "Local thing",
            "--explain", "a", "--analogy", "b", "--breaks", "c", "--pitch", "d")
        r = run(root, "recall", "local", "thing", cwd=str(tmp))
        check("no concepts match" in r.stdout, "local card hidden outside its scope: %r" % r.stdout[:80])
        r = run(root, "recall", "local", "thing", cwd=str(other))
        check("Local thing" in r.stdout and "this-project" in r.stdout, "local card visible inside: %r" % r.stdout[:120])
        r = run(root, "list", "--scope", "global")
        check("wal-mode" in r.stdout and "local-thing" not in r.stdout, "list --scope global")

        # index and lexicon
        (root / "index.json").unlink()
        r = run(root, "index")
        check("indexed 3 cards" in r.stdout, "index rebuild: %r" % r.stdout)
        lex = (root / "lexicon.txt").read_text().split()
        check("wal" in lex and "write-ahead" in lex and "the" not in lex, "lexicon tokens: %r" % lex)

        # hook recall: JSON envelope, dedup per session, slash skip, plain mode
        payload = {"session_id": "s1", "cwd": str(tmp), "prompt": "why does WAL mode let readers continue?"}
        r = run(root, "hook-recall", stdin=json.dumps(payload))
        doc = json.loads(r.stdout)
        ctx = doc["hookSpecificOutput"]["additionalContext"]
        check(doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit", "hook event name")
        check(ctx.startswith("memory: 1 concept") and ctx.endswith(cgmod.GUARD), "hook block shape: %r" % ctx[:60])
        check(len(ctx) <= cgmod.HOOK_MAX_CHARS, "hook block within cap")
        r = run(root, "hook-recall", stdin=json.dumps(payload))
        check(r.stdout == "", "same session, same card: silent (dedup), got %r" % r.stdout[:60])
        r = run(root, "hook-recall", stdin=json.dumps(dict(payload, session_id="s2")))
        check(r.stdout.startswith("{"), "new session recalls again")
        r = run(root, "hook-recall", stdin=json.dumps(dict(payload, session_id="s3", prompt="/feynman wal")))
        check(r.stdout == "", "slash invocation skipped")
        r = run(root, "hook-recall", "--plain", stdin=json.dumps(dict(payload, session_id="s4")))
        check(r.stdout.startswith("memory: 1 concept"), "plain mode is the bare block")
        r = run(root, "hook-recall", stdin="not json")
        check(r.stdout == "" and r.returncode == 0, "garbage stdin fails open")
        run(root, "write", "wal-mode", "--pitch", "WAL: one writer, many readers, no waiting.")
        r = run(root, "hook-recall", stdin=json.dumps(payload))
        check(r.stdout.startswith("{"), "card updated since injection: recalled again in s1")

        # export
        r = run(root, "export", "--format", "mermaid")
        check("flowchart LR" in r.stdout and "wal_mode -- depends_on --> sqlite_journal" in r.stdout,
              "mermaid export: %r" % r.stdout)
        r = run(root, "export", "--format", "json")
        check("wal-mode" in json.loads(r.stdout), "json export")

        # grade with a fake grader
        fake = pathlib.Path(tmp) / "grader.py"
        fake.write_text("import sys; sys.stdin.read(); print('{\"score\": 4, \"note\": \"analogy drifts\"}')\n")
        r = run(root, "grade", "wal-mode", "--grader", "%s %s" % (sys.executable, fake))
        check("grade 4/5" in r.stdout, "grade output: %r %r" % (r.stdout, r.stderr))
        text = (root / "cards" / "wal-mode.md").read_text()
        check("grade: 4" in text and "graded 4/5" in text, "grade persisted")

        # anchors and drift
        repo = pathlib.Path(tmp) / "anchored"
        repo.mkdir()
        g = git(repo, "init", "-q")
        if g.returncode != 0:
            print("note: git init unavailable here (%s); anchor tests skipped" % g.stderr.strip()[:120])
            return
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "t")
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "schema.sql").write_text("PRAGMA journal_mode = WAL;\n")
        git(repo, "add", "schema.sql")
        git(repo, "commit", "-q", "-m", "init")
        r = run(root, "anchor", "wal-mode", "--repo", str(repo), "--path", "schema.sql", "--line", "1")
        check("anchored wal-mode" in r.stdout, "anchor: %r %r" % (r.stdout, r.stderr))
        r = run(root, "check")
        check("DRIFT" not in r.stdout and "0 newly stale" in r.stdout, "no drift yet: %r" % r.stdout)
        (repo / "schema.sql").write_text("PRAGMA journal_mode = DELETE;\n")
        git(repo, "commit", "-q", "-am", "change")
        r = run(root, "check")
        check("DRIFT" in r.stdout and "1 newly stale" in r.stdout, "drift detected: %r" % r.stdout)
        text = (root / "cards" / "wal-mode.md").read_text()
        check("status: stale" in text and "drift: changed since" in text, "stale recorded")
        r = run(root, "recall", "wal")
        check("stale" in r.stdout, "stale shown in recall")
        r = run(root, "anchor", "wal-mode", "--repo", str(repo), "--path", "schema.sql")
        text = (root / "cards" / "wal-mode.md").read_text()
        check("status: stale" not in text and "drift:" not in text, "re-anchoring clears stale: %s" % text[:500])
        r = run(root, "check", "--scope", str(repo))
        check("0 newly stale" in r.stdout, "scoped check clean")


def main():
    test_frontmatter_roundtrip()
    test_cli()
    if FAILS:
        print("\n".join("FAIL " + f for f in FAILS))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
