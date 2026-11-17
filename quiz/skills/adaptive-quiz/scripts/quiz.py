#!/usr/bin/env python3
"""Fixed-bank adaptive quiz with a local answer store. Python 3.9+, standard library only.

Data: $KNOWLEDGE_HOME/quiz.sqlite3 (default ~/.kiro/knowledge). Separate from the feynman
component's card store, linked by identity: concept keys equal feynman card slugs, so the
same key names the same idea in both stores. Nothing reads or writes across them.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

VERSION = 1
DB_NAME = "quiz.sqlite3"
DIMENSIONS = ("recognition", "explanation", "application", "debugging", "transfer")
KEY = re.compile(r"[a-z0-9][a-z0-9._-]{0,119}\Z")
SCOPE = re.compile(r"(?:global|(?:repo|dir):[a-z0-9][a-z0-9._-]{0,119})\Z")
SCHEMA = """
CREATE TABLE sessions(id TEXT PRIMARY KEY, created REAL NOT NULL, scope TEXT NOT NULL,
    catalog_hash TEXT NOT NULL, items TEXT NOT NULL);
CREATE TABLE answers(session TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question TEXT NOT NULL, concept TEXT NOT NULL, dimension TEXT NOT NULL,
    choice TEXT NOT NULL, correct INTEGER NOT NULL, assisted INTEGER NOT NULL,
    observed REAL NOT NULL, PRIMARY KEY(session, question));
PRAGMA user_version=1;
"""


class Error(Exception):
    pass


def sha(value):
    return hashlib.sha256(value).hexdigest()


def data_dir():
    return Path(os.environ.get("KNOWLEDGE_HOME", str(Path.home() / ".kiro" / "knowledge"))).expanduser().resolve()


# --- scope: identical derivation to feynman/scripts/kg.py so repo scopes line up across both stores ---

def git(cwd, *args):
    try:
        result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=3, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def locate(cwd):
    cwd = Path(cwd).expanduser().resolve()
    if not cwd.is_dir():
        raise Error("cwd must be an existing directory")
    if git(cwd, "rev-parse", "--show-toplevel"):
        common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if not common:
            common = git(cwd, "rev-parse", "--git-common-dir")
            common = str((cwd / common).resolve()) if common else str(cwd)
        return "repo:" + sha(str(Path(common).resolve()).encode())[:20]
    return "dir:" + sha(str(cwd).encode())[:20]


def resolve_scope(value, cwd):
    if value == "here":
        return locate(cwd)
    if not isinstance(value, str) or not SCOPE.fullmatch(value):
        raise Error("scope must be global, here, repo:<slug>, or dir:<slug>")
    return value


# --- catalog ---

def load_catalog(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 2:
        raise Error("unsupported catalog schema")
    keys = set()
    for c in data["concepts"]:
        if not KEY.fullmatch(c["key"]) or c["key"] in keys:
            raise Error("invalid or duplicate concept key: " + str(c.get("key")))
        keys.add(c["key"])
        if not str(c.get("title", "")).strip() or not str(c.get("domain", "")).strip():
            raise Error("concept needs title and domain: " + c["key"])
    ids = set()
    for q in data["questions"]:
        if not KEY.fullmatch(q["id"]) or q["id"] in ids:
            raise Error("invalid or duplicate question id: " + str(q.get("id")))
        ids.add(q["id"])
        if q["concept"] not in keys or q["dimension"] not in DIMENSIONS:
            raise Error("question has unknown concept/dimension: " + q["id"])
        if set(q["options"]) != set("ABCD") or q["answer"] not in ("A", "B", "C", "D"):
            raise Error("question needs options A-D and one answer: " + q["id"])
        texts = list(q["options"].values())
        if len(set(texts)) != 4 or any(not str(t).strip() for t in texts):
            raise Error("options must be four distinct non-empty strings: " + q["id"])
        if not str(q.get("prompt", "")).strip() or not str(q.get("explanation", "")).strip():
            raise Error("question needs prompt and explanation: " + q["id"])
    if not keys or not ids:
        raise Error("empty catalog")
    return data


# --- storage ---

@contextlib.contextmanager
def connect(home, write=False):
    path = Path(home) / DB_NAME
    if not path.exists() and not write:
        yield None
        return
    if write:
        Path(home).mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(home, 0o700)
    conn = sqlite3.connect(path if write else path.as_uri() + "?mode=ro", uri=not write, timeout=5,
                           isolation_level=None)
    try:
        if write:
            os.chmod(path, 0o600)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0 and write:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute("PRAGMA user_version").fetchone()[0] == 0:
                for statement in SCHEMA.split(";"):
                    if statement.strip():
                        conn.execute(statement)
            conn.commit()
            version = VERSION
        if version != VERSION:
            raise Error(f"unsupported database schema {version}; expected {VERSION}; no data changed")
        yield conn
    finally:
        conn.close()


class Quiz:
    def __init__(self, home, catalog_path):
        self.home = Path(home)
        self.catalog = load_catalog(catalog_path)
        self.catalog_hash = sha(json.dumps(self.catalog, sort_keys=True, separators=(",", ":")).encode())
        self.concepts = {c["key"]: c for c in self.catalog["concepts"]}
        self.questions = {q["id"]: q for q in self.catalog["questions"]}

    def doctor(self):
        with connect(self.home) as db:
            return {"database_exists": db is not None, "data_directory": str(self.home),
                    "schema_version": VERSION, "catalog": self.catalog["version"], "catalog_hash": self.catalog_hash,
                    "concepts": len(self.concepts), "questions": len(self.questions),
                    "integrity": db.execute("PRAGMA quick_check").fetchone()[0] if db else "not_created",
                    "counts": {t: db.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
                               for t in ("sessions", "answers")} if db else {"sessions": 0, "answers": 0}}

    def history(self, db, scope):
        if db is None:
            return []
        return db.execute("SELECT a.* FROM answers a JOIN sessions s ON s.id=a.session WHERE s.scope=? "
                          "ORDER BY a.observed", (scope,)).fetchall()

    def start(self, count=5, domain=None, concepts=None, scope="global"):
        if not 1 <= count <= 20:
            raise Error("count must be 1..20")
        wanted = set(concepts or [])
        unknown = wanted - set(self.concepts)
        if unknown:
            raise Error("unknown concepts: " + ", ".join(sorted(unknown)) + "; known: " + ", ".join(sorted(self.concepts)))
        pool = [q for q in self.questions.values()
                if (domain is None or self.concepts[q["concept"]]["domain"] == domain)
                and (not wanted or q["concept"] in wanted)]
        if not pool:
            raise Error("no questions match; domains: " + ", ".join(sorted({c["domain"] for c in self.concepts.values()})))
        session = uuid.uuid4().hex
        rng = random.Random(session)
        with connect(self.home, True) as db:
            rows = self.history(db, scope)
            latest = {r["question"]: r for r in rows if not r["assisted"]}  # latest unaided per question
            seen = {r["question"] for r in rows}
            bins = {"unseen": [], "weak": [], "review": []}
            for q in pool:
                row = latest.get(q["id"])
                bins["unseen" if row is None else ("weak" if not row["correct"] else "review")].append(q)
            for items in bins.values():
                rng.shuffle(items)
                # Never-answered before assisted-only; oldest evidence first inside assessed bins.
                items.sort(key=lambda q: (q["id"] in seen, latest[q["id"]]["observed"] if q["id"] in latest else 0))
            chosen, used = [], set()
            mix = ("unseen", "unseen", "weak", "review")
            for i in range(min(count, len(pool))):
                order = [mix[i % 4]] + [b for b in bins if b != mix[i % 4]]
                bucket = next(b for b in order if bins[b])
                items = bins[bucket]
                index = next((j for j, q in enumerate(items) if q["concept"] not in used), 0)
                q = dict(items.pop(index))
                used.add(q["concept"])
                labels = list("ABCD")
                rng.shuffle(labels)  # per-session option shuffle removes position clues
                q["answer"] = "ABCD"[labels.index(q["answer"])]
                q["options"] = {new: q["options"][old] for new, old in zip("ABCD", labels)}
                q["selection_reason"] = bucket
                chosen.append(q)
            db.execute("INSERT INTO sessions VALUES (?,?,?,?,?)",
                       (session, time.time(), scope, self.catalog_hash, json.dumps(chosen)))
        return {"session": session, "scope": scope,
                "questions": [{k: v for k, v in q.items() if k not in ("answer", "explanation")} for q in chosen]}

    def answer(self, session, question, choice, assisted=False):
        if choice not in ("A", "B", "C", "D"):
            raise Error("choice must be A, B, C, or D")
        with connect(self.home, True) as db:
            row = db.execute("SELECT items FROM sessions WHERE id=?", (session,)).fetchone()
            if row is None:
                raise Error("unknown session")
            q = next((q for q in json.loads(row[0]) if q["id"] == question), None)
            if q is None:
                raise Error("question not in session")
            correct = choice == q["answer"]
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR IGNORE INTO answers VALUES (?,?,?,?,?,?,?,?)",
                       (session, question, q["concept"], q["dimension"], choice, correct, assisted, time.time()))
            prior = db.execute("SELECT choice, assisted FROM answers WHERE session=? AND question=?",
                               (session, question)).fetchone()
            db.commit()
            if prior["choice"] != choice or bool(prior["assisted"]) != assisted:
                raise Error("answer already recorded with different values; start a new quiz")
        return {"session": session, "question": question, "correct": correct, "answer": q["answer"],
                "explanation": q["explanation"], "assisted": assisted}

    def profile(self, scope="global"):
        with connect(self.home) as db:
            latest = {}
            for r in self.history(db, scope):
                if not r["assisted"]:
                    latest[r["question"]] = r
        out = []
        for c in self.concepts.values():
            rows = [r for r in latest.values() if r["concept"] == c["key"]]
            out.append({**c, "feynman_card": c["key"], "distinct_items": len(rows),
                        "correct": sum(r["correct"] for r in rows),
                        "observed_accuracy": round(sum(r["correct"] for r in rows) / len(rows), 2) if rows else None,
                        "dimensions_assessed": sorted({r["dimension"] for r in rows}),
                        "last_assessed": max((r["observed"] for r in rows), default=None)})
        return {"scope": scope, "catalog": self.catalog["version"],
                "interpretation": "Latest unaided answer per distinct item. Observed accuracy, not calibrated mastery.",
                "concepts": out}

    def export(self):
        with connect(self.home) as db:
            tables = {t: [dict(r) for r in db.execute("SELECT * FROM " + t)] if db else []
                      for t in ("sessions", "answers")}
        return {"schema_version": VERSION, "exported_at": time.time(), **tables}

    def forget_scope(self, scope):
        with connect(self.home, True) as db:
            db.execute("BEGIN IMMEDIATE")
            n = db.execute("DELETE FROM sessions WHERE scope=?", (scope,)).rowcount
            db.commit()
        return {"forgotten_scope": scope, "sessions_removed": n,
                "note": "Answers cascade. Exports and backups are separate copies."}


def main(argv=None):
    os.umask(0o077)
    root = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--home", type=Path, default=data_dir(), help="data directory (or KNOWLEDGE_HOME)")
    p.add_argument("--catalog", type=Path, default=root / "catalog.json")
    p.add_argument("--cwd", default=os.getcwd(), help="workspace used when --scope here")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    start = sub.add_parser("start")
    start.add_argument("--count", type=int, default=5)
    start.add_argument("--domain")
    start.add_argument("--concepts", help="comma-separated concept keys to focus on")
    start.add_argument("--scope", default="global", help="global (default), here, repo:<slug>, dir:<slug>")
    ans = sub.add_parser("answer")
    ans.add_argument("session")
    ans.add_argument("question")
    ans.add_argument("choice", choices=list("ABCD"))
    ans.add_argument("--assisted", action="store_true", help="a hint or solution was available before answering")
    prof = sub.add_parser("profile")
    prof.add_argument("--scope", default="global")
    sub.add_parser("export")
    forget = sub.add_parser("forget-scope")
    forget.add_argument("scope")
    args = p.parse_args(argv)
    try:
        quiz = Quiz(args.home.expanduser().resolve(), args.catalog)
        if args.command == "doctor":
            result = quiz.doctor()
        elif args.command == "start":
            concepts = [c.strip() for c in args.concepts.split(",") if c.strip()] if args.concepts else None
            result = quiz.start(args.count, args.domain, concepts, resolve_scope(args.scope, args.cwd))
        elif args.command == "answer":
            result = quiz.answer(args.session, args.question, args.choice, args.assisted)
        elif args.command == "profile":
            result = quiz.profile(resolve_scope(args.scope, args.cwd))
        elif args.command == "export":
            result = quiz.export()
        else:
            result = quiz.forget_scope(resolve_scope(args.scope, args.cwd))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
