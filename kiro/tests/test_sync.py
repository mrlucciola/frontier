import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MK = REPO / "kiro" / "tools" / "mk_sync.py"
APPLY = REPO / "kiro" / "tools" / "APPLY.sh"

FILES = {
    "hello.txt": "héllo 日本語のテキスト\n".encode(),   # CJK, trailing newline
    "nested/note.md": b"no trailing newline",          # no trailing newline
    "empty.bin": b"",                                  # empty file
    "junk/.git/config": b"[core]\n",                   # must be skipped
    "junk/node_modules/x.js": b"junk\n",               # must be skipped
}


def sh(cmd, **env_extra):
    return subprocess.run(cmd, capture_output=True, text=True,
                          env={**os.environ, **env_extra})


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "fixture"
        for rel, data in FILES.items():
            p = self.src / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        self.bundle = self.tmp / "bundle"
        rc = sh([shutil.which("python3") or "python3", str(MK),
                 "--from", str(self.src), "--out", str(self.bundle)])
        self.assertEqual(rc.returncode, 0, rc.stderr)
        self.manifest = {}
        for line in (self.bundle / "MANIFEST.txt").read_text().splitlines():
            sha, size, rel = line.split(" ", 2)
            self.manifest[rel] = (sha, int(size))

    def apply(self, target):
        return sh(["sh", str(APPLY), str(self.bundle), str(target)])

    def test_bundle_skips_junk_and_hashes(self):
        self.assertEqual(sorted(self.manifest),
                         ["fixture/empty.bin", "fixture/hello.txt", "fixture/nested/note.md"])
        for rel, (sha, size) in self.manifest.items():
            data = (self.tmp / rel).read_bytes()
            self.assertEqual(sha, hashlib.sha256(data).hexdigest())
            self.assertEqual(size, len(data))

    def test_apply_writes_exact_bytes(self):
        target = self.tmp / "root-a"
        rc = self.apply(target)
        self.assertEqual(rc.returncode, 0, rc.stdout + rc.stderr)
        written = sorted(p.relative_to(target).as_posix()
                         for p in target.rglob("*") if p.is_file())
        self.assertEqual(written, sorted(self.manifest))
        for rel in self.manifest:
            self.assertEqual((target / rel).read_bytes(), (self.tmp / rel).read_bytes())

    def test_rerun_is_idempotent(self):
        target = self.tmp / "root-b"
        first = self.apply(target)
        state = {p: p.read_bytes() for p in sorted(target.rglob("*")) if p.is_file()}
        second = self.apply(target)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(second.stdout, first.stdout)
        self.assertEqual({p: p.read_bytes() for p in state}, state)

    def test_tampered_base64_fails_that_file(self):
        target = self.tmp / "root-c"
        chunks = sorted((self.bundle).glob("SYNC-*.txt"))
        self.assertTrue(chunks)
        text = chunks[0].read_text()
        lines = text.splitlines()
        i = lines.index(next(l for l in lines if l.startswith("BEGIN fixture/hello.txt "))) + 1
        lines[i] = ("B" if lines[i][0] != "B" else "C") + lines[i][1:]
        chunks[0].write_text("\n".join(lines) + "\n")
        rc = self.apply(target)
        self.assertNotEqual(rc.returncode, 0)
        self.assertIn("FAIL fixture/hello.txt", rc.stdout)
        self.assertFalse((target / "fixture" / "hello.txt").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
