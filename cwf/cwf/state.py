from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

from .common import Fault, private_dir, canonical, now


class State:
    def __init__(self, home, ephemeral=False, fallback=False):
        self.warning = None
        self.durable = not ephemeral
        self.path = Path(home).resolve() / ".local/state/cwf/state.sqlite3"
        try:
            if not ephemeral:
                private_dir(self.path.parent)
                if self.path.is_symlink():
                    raise Fault("State database is a symlink", "blocked")
            self.db = sqlite3.connect(":memory:" if ephemeral else str(self.path), timeout=1)
            self.db.execute("PRAGMA busy_timeout=1000")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS scopes (identity TEXT PRIMARY KEY, id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS roots (root TEXT PRIMARY KEY, id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS records (
                  kind TEXT, root TEXT, id TEXT, revision INTEGER, updated TEXT, payload TEXT,
                  PRIMARY KEY(kind,root,id));
                CREATE TABLE IF NOT EXISTS cache (
                  root TEXT, key TEXT, updated TEXT, payload TEXT, PRIMARY KEY(root,key));
            """)
            if not ephemeral:
                os.chmod(self.path, 0o600)
        except (OSError, sqlite3.Error, Fault) as exc:
            if hasattr(self, "db"):
                self.db.close()
            if not fallback or isinstance(exc, Fault):
                if isinstance(exc, Fault):
                    raise
                raise Fault("State unavailable; no durable write completed", "blocked", type(exc).__name__) from exc
            self.db = sqlite3.connect(":memory:")
            self.durable = False
            self.warning = "state_unavailable_ephemeral"
            self.db.executescript("""
              CREATE TABLE scopes(identity TEXT PRIMARY KEY,id TEXT NOT NULL);
              CREATE TABLE roots(root TEXT PRIMARY KEY,id TEXT NOT NULL);
              CREATE TABLE records(kind TEXT,root TEXT,id TEXT,revision INTEGER,updated TEXT,payload TEXT,PRIMARY KEY(kind,root,id));
              CREATE TABLE cache(root TEXT,key TEXT,updated TEXT,payload TEXT,PRIMARY KEY(root,key));
            """)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def ids(self, info):
        def get(table, column, value):
            with self.db:
                self.db.execute(f"INSERT OR IGNORE INTO {table} VALUES (?,?)", (value, uuid.uuid4().hex))
            return self.db.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()[0]
        return get("scopes", "identity", info["identity"]), get("roots", "root", info["worktree"])

    def cached(self, root, key):
        row = self.db.execute("SELECT payload FROM cache WHERE root=? AND key=?", (root,key)).fetchone()
        return json.loads(row[0]) if row else None

    def cache(self, root, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO cache VALUES(?,?,?,?)", (root,key,now(),canonical(value)))

    def get(self, kind, root, id):
        row = self.db.execute("SELECT revision,updated,payload FROM records WHERE kind=? AND root=? AND id=?", (kind,root,id)).fetchone()
        if not row:
            raise Fault("Record not found in selected scope", "blocked")
        return {"revision": row[0], "updated_at": row[1], "record": json.loads(row[2])}

    def put(self, kind, root, id, value, expected):
        if not self.durable:
            raise Fault("Durable state required for this operation", "blocked")
        if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0:
            raise Fault("expected_revision must be a nonnegative integer")
        try:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT revision FROM records WHERE kind=? AND root=? AND id=?", (kind,root,id)).fetchone()
            current = row[0] if row else 0
            if current != expected:
                raise Fault("Revision conflict; read current record before updating", "blocked", {"current_revision": current})
            revision = current+1
            self.db.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?)", (kind,root,id,revision,now(),canonical(value)))
            self.db.commit()
            return self.get(kind,root,id)
        except BaseException:
            self.db.rollback()
            raise

    def records(self, root=None, kind=None, limit=None):
        clauses=[]; params=[]
        if root is not None: clauses.append("root=?"); params.append(root)
        if kind is not None: clauses.append("kind=?"); params.append(kind)
        sql="SELECT kind,root,id,revision,updated,payload FROM records"
        if clauses: sql+=" WHERE "+" AND ".join(clauses)
        sql+=" ORDER BY kind,root,id"
        if limit is not None: sql+=" LIMIT ?"; params.append(limit)
        rows=self.db.execute(sql,params)
        return [{"kind": k, "root": r, "id": i, "revision": v, "updated_at": t, "record": json.loads(p)} for k,r,i,v,t,p in rows]

    def prune(self, root, cache_days, observation_days):
        cache_cut=(datetime.now(timezone.utc)-timedelta(days=cache_days)).isoformat()
        obs_cut=(datetime.now(timezone.utc)-timedelta(days=observation_days)).isoformat()
        with self.db:
            caches=self.db.execute("DELETE FROM cache WHERE root=? AND updated<?", (root,cache_cut)).rowcount
            ids=[r["id"] for r in self.records(root,"observation") if r["updated_at"]<obs_cut and r["record"]["claim_status"]=="inferred"]
            for id in ids:
                self.db.execute("DELETE FROM records WHERE kind='observation' AND root=? AND id=?",(root,id))
        return {"cache_records":caches,"observations":len(ids)}

    def purge(self, root):
        with self.db:
            a=self.db.execute("DELETE FROM records WHERE root=?",(root,)).rowcount
            b=self.db.execute("DELETE FROM cache WHERE root=?",(root,)).rowcount
        return {"records":a,"cache_records":b}
