#!/usr/bin/env python3
"""Build a hand-paste sync bundle for a firewalled machine.

Writes into --out: MANIFEST.txt (lines `<sha256> <bytes> <relpath>`) and
SYNC-NNN.txt chunk files. Each record is `BEGIN <relpath> <bytes> <sha256>`,
the file's base64 wrapped at 76 columns, then `END <relpath>`. A chunk is
closed once it holds 40 files or 90000 bytes, so a paste session stays
eyeballable. Prints each produced file with its sha256 at the end; the
receiver verifies chunks with kiro/tools/APPLY.sh.

Relative --from paths resolve against the repository root, so the default
list works from any directory. Standard library only.
"""
import argparse
import base64
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FROM = ["pm", "wt", "cwf", "icm", "kiro", "README.md", "AGENTS.md", "CLAUDE.md"]
SKIP_DIRS = {".git", ".tmp", ".venv", "node_modules", "__pycache__"}
MAX_FILES = 40
MAX_BYTES = 90000


def collect(from_paths):
    """[(relpath, Path)] sorted by relpath; relpaths are rooted at each
    --from entry's name. Shared with mk_sync_branch.py so the bundle and the
    kiro-sync branch carry the same list."""
    found = {}
    for entry in from_paths:
        p = Path(entry)
        if not p.is_absolute():
            p = ROOT / p
        if p.is_file():
            found[p.name] = p
        elif p.is_dir():
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
                for name in sorted(filenames):
                    full = Path(dirpath) / name
                    rel = full.relative_to(p.parent).as_posix()
                    found[rel] = full
        else:
            sys.stderr.write("mk_sync: no such path: %s\n" % entry)
            raise SystemExit(1)
    return sorted(found.items())


def record(rel, data):
    b64 = base64.b64encode(data).decode()
    body = [b64[i:i + 76] for i in range(0, len(b64), 76)]
    sha = hashlib.sha256(data).hexdigest()
    text = "\n".join(["BEGIN %s %d %s" % (rel, len(data), sha)] + body + ["END %s" % rel])
    return text + "\n", sha


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mk_sync", description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="from_paths", nargs="+", default=DEFAULT_FROM,
                    metavar="PATH", help="files/directories to bundle "
                    "(relative to %s); default: %s" % (ROOT, " ".join(DEFAULT_FROM)))
    ap.add_argument("--out", required=True, help="bundle directory to create")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, buf, count, size, nchunks = [], [], 0, 0, 0
    chunk_paths = []

    def flush():
        nonlocal buf, count, size, nchunks
        if not count:
            return
        nchunks += 1
        name = "SYNC-%03d.txt" % nchunks
        data = "".join(buf).encode()
        (out_dir / name).write_bytes(data)
        chunk_paths.append(name)
        buf, count, size = [], 0, 0

    for rel, path in collect(args.from_paths):
        text, sha = record(rel, path.read_bytes())
        manifest.append("%s %d %s" % (sha, len(path.read_bytes()), rel))
        buf.append(text)
        count += 1
        size += len(text.encode())
        if count >= MAX_FILES or size >= MAX_BYTES:
            flush()
    flush()
    (out_dir / "MANIFEST.txt").write_text("\n".join(manifest) + "\n")

    for name in ["MANIFEST.txt"] + chunk_paths:
        data = (out_dir / name).read_bytes()
        print("%s %s %d" % (name, hashlib.sha256(data).hexdigest(), len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
